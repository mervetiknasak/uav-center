"""Durable idempotent allocation; remote calls never hold a database transaction."""

import hashlib
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from ..models import FormNumberAllocation, FormNumberMapping, FormProcessRecord
from . import client
from .rules import enforce_locks, field_catalog, field_value, resolve_context, set_field


class AllocationConflict(APIException):
    status_code = 409
    default_detail = "Numaralandırma işlemi veya form değişti. Mevcut işlemi kontrol edin."


def digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False).encode()
    ).hexdigest()


def visible_allocation(actor, allocation_id):
    query = FormNumberAllocation.objects.select_related("record")
    if not actor.is_staff:
        query = query.filter(Q(created_by=actor) | Q(record__isnull=False))
    try:
        return query.get(pk=allocation_id)
    except FormNumberAllocation.DoesNotExist as exc:
        raise NotFound() from exc


def validate_form(payload, mapping, actor, record, attachment=None):
    from ..serializers import FormProcessRecordSerializer

    form = dict(payload["form"])
    if form.get("template_code") != mapping.template_code:
        raise ValidationError({"form": "Eşleştirme seçilen forma ait değil."})
    if field_value(form, mapping.target_field):
        raise ValidationError({"target_field": "Dolu hedef alanın üzerine numara yazılamaz."})
    if record:
        if record.status == "archived":
            raise AllocationConflict("Arşivlenmiş formda numara üretilemez.")
        if payload.get("expected_updated_at") != record.updated_at:
            raise AllocationConflict("Form değişmiş. Güncel kaydı yükleyin.")
        enforce_locks(record, form)
    # A temporary value satisfies normal serializer requirements without persisting a fake number.
    form["data"] = dict(form.get("data", {}))
    set_field(
        form,
        mapping.target_field,
        str(uuid.uuid4()) if mapping.target_field == "record_number" else "-",
    )
    form["status"] = record.status if record else "draft"
    if attachment:
        form["attachment"] = attachment
    serializer = FormProcessRecordSerializer(instance=record, data=form)
    serializer.is_valid(raise_exception=True)
    cleaned = dict(serializer.validated_data)
    cleaned.pop("attachment", None)
    set_field(cleaned, mapping.target_field, "")
    return cleaned


def start_allocation(*, actor, key, payload, attachment=None):
    fingerprint = dict(payload)
    if attachment:
        hasher = hashlib.sha256()
        for chunk in attachment.chunks():
            hasher.update(chunk)
        attachment.seek(0)
        fingerprint["attachment"] = {"name": attachment.name, "hash": hasher.hexdigest()}
    request_hash = digest(fingerprint)
    existing = FormNumberAllocation.objects.filter(idempotency_key=key).first()
    if existing:
        if existing.created_by_id != actor.pk or existing.request_hash != request_hash:
            raise AllocationConflict("Bu işlem anahtarı farklı bir istek için kullanılmış.")
        return existing, False
    try:
        mapping = FormNumberMapping.objects.get(pk=payload["mapping_id"], enabled=True)
    except FormNumberMapping.DoesNotExist as exc:
        raise ValidationError({"mapping_id": "Etkin eşleştirme bulunamadı."}) from exc
    record = None
    if payload.get("record_id"):
        try:
            record = FormProcessRecord.objects.get(pk=payload["record_id"])
        except FormProcessRecord.DoesNotExist as exc:
            raise NotFound() from exc
    form = validate_form(payload, mapping, actor, record, attachment)
    contract = client.get_format(mapping.format_code)
    if contract.get("required_context", []) != mapping.format_snapshot.get("required_context", []):
        raise AllocationConflict(
            "Numaratör context tanımı değişmiş. Yönetici eşleştirmeyi güncellemelidir."
        )
    context, locks = resolve_context(mapping, form, payload["manual_context"])
    try:
        allocation_id = uuid.UUID(key)
    except ValueError:
        allocation_id = uuid.uuid5(uuid.NAMESPACE_URL, f"form-numbering:{actor.pk}:{key}")
    provider_payload = {
        "format_code": mapping.format_code,
        "context_data": context,
        "external_reference": str(allocation_id),
        "metadata": {},
    }
    preview = client.preview_number(mapping.format_code, context)
    maximum = field_catalog(mapping.template_code)[mapping.target_field][1]
    if len(preview) > maximum:
        raise ValidationError(
            {"target_field": "Format çıktısı hedef alanın uzunluk sınırını aşıyor."}
        )
    allocation = FormNumberAllocation(
        id=allocation_id,
        idempotency_key=key,
        request_hash=request_hash,
        created_by=actor,
        record=record,
        original_record_id=record.pk if record else None,
        mapping=mapping,
        target_field=mapping.target_field,
        mapping_snapshot={
            "template_code": mapping.template_code,
            "format_code": mapping.format_code,
            "context_sources": mapping.context_sources,
            "format": contract,
        },
        form_snapshot=form,
        provider_payload=provider_payload,
        locked_values=locks,
        expected_updated_at=record.updated_at if record else None,
    )
    if attachment:
        allocation.attachment = attachment
        allocation.attachment_name = attachment.name
    try:
        with transaction.atomic():
            allocation.save(force_insert=True)
    except Exception as exc:
        if allocation.attachment and allocation.attachment._committed:
            from ..services.lifecycle import _delete_stored_attachment

            _delete_stored_attachment(
                allocation.attachment.storage, allocation.attachment.name, record_id=None
            )
        if isinstance(exc, IntegrityError):
            existing = FormNumberAllocation.objects.filter(
                idempotency_key=key, created_by=actor, request_hash=request_hash
            ).first()
            if existing:
                return existing, False
            raise AllocationConflict("Bu form alanı için bir numara işlemi zaten var.") from exc
        raise
    return allocation, True


def run_allocation(allocation):
    if allocation.status == "completed":
        return allocation
    token = uuid.uuid4()
    now = timezone.now()
    claimed = (
        FormNumberAllocation.objects.filter(pk=allocation.pk)
        .exclude(status="completed")
        .filter(Q(lease_until__isnull=True) | Q(lease_until__lt=now))
        .update(
            lease_token=token,
            lease_until=now + timedelta(seconds=max(60, settings.NUMARATOR_TIMEOUT * 3)),
        )
    )
    if not claimed:
        raise AllocationConflict(
            "Numara işlemi sürüyor. İşlem durumunu kontrol edip tekrar deneyin."
        )
    try:
        allocation.refresh_from_db()
        if allocation.provider_id is None:
            result = client.generate_number(allocation.provider_payload, f"form-{allocation.id}")
            if not FormNumberAllocation.objects.filter(pk=allocation.pk, lease_token=token).update(
                provider_id=result["id"], document_number=result["document_number"], status="issued"
            ):
                raise AllocationConflict()
            allocation.refresh_from_db()
        return finalize(allocation, token)
    finally:
        FormNumberAllocation.objects.filter(pk=allocation.pk, lease_token=token).update(
            lease_token=None, lease_until=None
        )


def finalize(allocation, token):
    from ..serializers import FormProcessRecordSerializer
    from ..services.lifecycle import create_form_process_record, update_form_process_record

    with transaction.atomic():
        # Write-lock the operation before checking its result or touching the form.
        if not FormNumberAllocation.objects.filter(pk=allocation.pk, lease_token=token).update(
            status="issued"
        ):
            raise AllocationConflict()
        record = None
        if allocation.original_record_id:
            record = (
                FormProcessRecord.objects.select_for_update()
                .filter(pk=allocation.original_record_id)
                .first()
            )
            if not record or record.updated_at != allocation.expected_updated_at:
                raise AllocationConflict(
                    "Numara ayrıldı ancak form değişmiş veya silinmiş; eski verilerle üzerine yazılmadı."
                )
        form = json.loads(json.dumps(allocation.form_snapshot))
        set_field(form, allocation.target_field, allocation.document_number)
        maximum = field_catalog(form["template_code"])[allocation.target_field][1]
        if len(allocation.document_number) > maximum:
            raise AllocationConflict(
                "Üretilen numara alan sınırını aşıyor; numara ayrıldı, yönetici kontrolü gerekli."
            )
        # Preserve provider casing, and apply the regular catalog/uniqueness validation again.
        serializer = FormProcessRecordSerializer(
            instance=record, data=form, context={"numbering_result": True}
        )
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        set_field(validated, allocation.target_field, allocation.document_number)
        if allocation.attachment:
            validated["attachment"] = allocation.attachment
        if record:
            saved = update_form_process_record(
                record=record, validated_data=validated, actor=allocation.created_by
            )
        else:
            saved = create_form_process_record(
                validated_data=validated, actor=allocation.created_by
            )
        if allocation.attachment:
            saved.attachment_name = allocation.attachment_name
            saved.save(update_fields=["attachment_name"])
        locks = dict(allocation.locked_values)
        locks[allocation.target_field] = allocation.document_number
        FormNumberAllocation.objects.filter(pk=allocation.pk, lease_token=token).update(
            record=saved,
            original_record_id=saved.pk,
            status="completed",
            locked_values=locks,
        )
        allocation.refresh_from_db()
        return allocation
