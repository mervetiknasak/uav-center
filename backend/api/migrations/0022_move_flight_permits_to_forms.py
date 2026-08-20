from django.db import migrations, models


FLIGHT_TEMPLATE_MAP = {
    "institution_a": "fm_qua_0579",
    "institution_b": "fm_qua_0580",
    "institution_c": "fm_qua_0581",
}
FLIGHT_FORM_TEMPLATES = tuple(FLIGHT_TEMPLATE_MAP.values())


def _available_record_number(FormProcessRecord, base_number, *, exclude_id=None):
    base = (base_number or "UCUS-IZNI").strip().upper()
    candidate = base
    suffix = 1
    queryset = FormProcessRecord.objects.filter(process_code="flight-permits")
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)
    while queryset.filter(record_number=candidate).exists():
        suffix += 1
        candidate = f"{base}-FP-{suffix}"
    return candidate


def move_flight_permits_to_forms(apps, schema_editor):
    FlightPermit = apps.get_model("api", "FlightPermit")
    FormProcessRecord = apps.get_model("api", "FormProcessRecord")

    existing_records = FormProcessRecord.objects.filter(template_code__in=FLIGHT_FORM_TEMPLATES)
    for record in existing_records.iterator():
        data = dict(record.data or {})
        fallback_date = (
            data.get("issue_date")
            or data.get("intended_flight_date")
            or record.created_at.date().isoformat()
        )
        data.setdefault("purpose_of_flight", [])
        data.setdefault("valid_from", fallback_date)
        data.setdefault("valid_until", fallback_date)
        lifecycle_status = record.status if record.status in {"draft", "approved"} else "revoked"
        data.setdefault("permit_lifecycle_status", lifecycle_status)
        record.record_number = _available_record_number(
            FormProcessRecord,
            record.record_number,
            exclude_id=record.pk,
        )
        record.process_code = "flight-permits"
        record.data = data
        record.save(update_fields=["process_code", "record_number", "data"])

    for permit in FlightPermit.objects.order_by("pk").iterator():
        template_code = FLIGHT_TEMPLATE_MAP.get(permit.template_code, "fm_qua_0579")
        record_number = _available_record_number(FormProcessRecord, permit.permit_number)
        purpose_codes = list(permit.purpose_of_flight or [])
        data = {
            "applicant": permit.permit_applicant,
            "application_number": permit.permit_number,
            "aircraft_owner": permit.aircraft_owner,
            "aircraft_model": permit.aircraft_type,
            "serial_number": permit.serial_number,
            "aircraft_nationality": permit.aircraft_nationality,
            "aircraft_id_mark": permit.aircraft_id_mark,
            "aircraft_manufacturer": permit.aircraft_manufacturer,
            "aircraft_configuration": permit.aircraft_configuration,
            "purpose_of_flight": purpose_codes,
            "purpose_scope": "\n".join(purpose_codes),
            "conditions_restrictions": permit.conditions_restrictions,
            "substantiations": permit.conditions_substantiations,
            "intended_flight_date": permit.target_date.isoformat() if permit.target_date else "",
            "flight_duration": str(permit.flight_duration or ""),
            "valid_from": permit.valid_from.isoformat(),
            "valid_until": permit.valid_until.isoformat(),
            "permit_lifecycle_status": permit.status,
            "issue_date": permit.valid_from.isoformat(),
            "approver_name": "",
        }
        template_data = dict(permit.template_data or {})
        if template_code == "fm_qua_0579":
            data.update(
                {
                    "is_recommendation": "yes" if permit.is_recommendation else "no",
                    "contract_number": template_data.get("contract_number", ""),
                    "flight_test_plan_number": template_data.get(
                        "flight_test_plan_number", ""
                    ),
                }
            )
        elif template_code == "fm_qua_0580":
            data.update(
                {
                    "initial_approval_reference": template_data.get("approval_reference", ""),
                    "maintenance_instructions": "",
                    "approval_name": template_data.get("approving_authority", ""),
                }
            )
        else:
            data.update(
                {
                    "nationality_registration": " / ".join(
                        value
                        for value in (permit.aircraft_nationality, permit.aircraft_id_mark)
                        if value
                    ),
                    "validity_period": f"{permit.valid_from.isoformat()} / {permit.valid_until.isoformat()}",
                    "place_of_issue": "",
                    "authority_representative_name": "",
                    "coordination_contact": template_data.get("coordination_contact", ""),
                    "coordination_reference": template_data.get("coordination_reference", ""),
                    "operational_notes": template_data.get("operational_notes", ""),
                }
            )

        identity = permit.serial_number or permit.aircraft_id_mark or permit.permit_applicant
        record = FormProcessRecord.objects.create(
            process_code="flight-permits",
            template_code=template_code,
            record_number=record_number,
            title=f"{identity[:285]} Uçuş İzni",
            status=(
                permit.status
                if permit.status in {"draft", "approved"}
                else "archived"
            ),
            data=data,
            notes=permit.notes,
            attachment=permit.document.name if permit.document else "",
            attachment_name=permit.document_name,
            attachment_content_type=permit.document_content_type,
            attachment_size=permit.document_size,
            created_by_id=permit.created_by_id,
            updated_by_id=permit.updated_by_id,
        )
        FormProcessRecord.objects.filter(pk=record.pk).update(
            created_at=permit.created_at,
            updated_at=permit.updated_at,
        )


class Migration(migrations.Migration):
    dependencies = [("api", "0021_formprocessrecord")]

    operations = [
        migrations.AddField(
            model_name="formprocessrecord",
            name="attachment",
            field=models.FileField(
                blank=True,
                max_length=500,
                upload_to="form_processes/%Y/%m/",
            ),
        ),
        migrations.AddField(
            model_name="formprocessrecord",
            name="attachment_content_type",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="formprocessrecord",
            name="attachment_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="formprocessrecord",
            name="attachment_size",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.RunPython(move_flight_permits_to_forms, migrations.RunPython.noop),
    ]
