"""Durable database-backed job queue and document-processing handler."""

from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections
from django.db.models import F
from django.utils import timezone

from ..models import AsyncJob, Document
from .document_extractor import extract_document
from .rag_service import answer_document_query, index_document


def enqueue_document_processing(*, document, owner, use_ocr, use_ai):
    return AsyncJob.objects.create(
        owner=owner,
        job_type=AsyncJob.TYPE_DOCUMENT_PROCESSING,
        document=document,
        payload={
            "document_id": document.pk,
            "use_ocr": bool(use_ocr),
            "use_ai": bool(use_ai),
        },
        max_attempts=getattr(settings, "JOB_MAX_ATTEMPTS", 3),
    )


def claim_next_job(worker_id):
    """Atomically claim one ready job; safe for multiple worker processes."""
    close_old_connections()
    now = timezone.now()
    candidate_ids = AsyncJob.objects.filter(
        status=AsyncJob.STATUS_QUEUED,
        available_at__lte=now,
        attempts__lt=F("max_attempts"),
    ).order_by("-priority", "created_at").values_list("pk", flat=True)[:20]

    for job_id in candidate_ids:
        updated = AsyncJob.objects.filter(
            pk=job_id,
            status=AsyncJob.STATUS_QUEUED,
            available_at__lte=now,
        ).update(
            status=AsyncJob.STATUS_RUNNING,
            attempts=F("attempts") + 1,
            locked_at=now,
            locked_by=worker_id,
            started_at=now,
            error_message="",
        )
        if updated:
            return AsyncJob.objects.select_related("document", "owner").get(pk=job_id)
    return None


def update_progress(job, progress):
    progress = max(0, min(100, int(progress)))
    now = timezone.now()
    AsyncJob.objects.filter(pk=job.pk, status=AsyncJob.STATUS_RUNNING).update(
        progress=progress,
        locked_at=now,
    )
    job.progress = progress
    job.locked_at = now


def process_document_job(job):
    document = job.document
    if document is None:
        document = Document.objects.get(pk=job.payload["document_id"])

    update_progress(job, 5)
    extraction = extract_document(
        document.file.path,
        use_ocr=bool(job.payload.get("use_ocr", False)),
    )
    extracted_text = extraction["text"]
    document.extracted_text = extracted_text
    document.save(update_fields=["extracted_text"])

    update_progress(job, 45)
    chunk_count = index_document(document)
    update_progress(job, 65)

    use_ai = bool(job.payload.get("use_ai", True))
    if use_ai:
        ai_result = answer_document_query(document, document.prompt)
        ai_result["response"] = ai_result["answer"]
        ai_result["filename"] = document.original_name
        ai_result["prompt"] = document.prompt
    else:
        ai_result = {
            "provider": "disabled",
            "filename": document.original_name,
            "prompt": "",
            "response": "",
        }

    ai_result["metrics"] = {
        "characters": len(extracted_text),
        "words": len(extracted_text.split()),
        "chunks": chunk_count,
    }
    ai_result["ai_enabled"] = use_ai
    ai_result["ocr"] = extraction["ocr"]

    document.ai_result = ai_result
    document.status = Document.STATUS_PROCESSED
    document.processed_at = timezone.now()
    document.error_message = ""
    document.save(update_fields=["ai_result", "status", "processed_at", "error_message"])
    update_progress(job, 95)
    return {
        "document_id": document.pk,
        "document_name": document.original_name,
        "characters": len(extracted_text),
        "words": len(extracted_text.split()),
        "chunks": chunk_count,
    }


JOB_HANDLERS = {
    AsyncJob.TYPE_DOCUMENT_PROCESSING: process_document_job,
}


def complete_job(job, result):
    now = timezone.now()
    AsyncJob.objects.filter(pk=job.pk, status=AsyncJob.STATUS_RUNNING).update(
        status=AsyncJob.STATUS_COMPLETED,
        progress=100,
        result=result,
        error_message="",
        completed_at=now,
        locked_at=None,
        locked_by="",
    )


def fail_or_retry_job(job, exc):
    message = str(exc) or exc.__class__.__name__
    now = timezone.now()
    if job.attempts < job.max_attempts:
        base_seconds = getattr(settings, "JOB_RETRY_BASE_SECONDS", 15)
        delay = base_seconds * (2 ** max(job.attempts - 1, 0))
        AsyncJob.objects.filter(pk=job.pk, status=AsyncJob.STATUS_RUNNING).update(
            status=AsyncJob.STATUS_QUEUED,
            progress=0,
            error_message=message,
            available_at=now + timedelta(seconds=delay),
            locked_at=None,
            locked_by="",
        )
        return AsyncJob.STATUS_QUEUED

    AsyncJob.objects.filter(pk=job.pk, status=AsyncJob.STATUS_RUNNING).update(
        status=AsyncJob.STATUS_FAILED,
        error_message=message,
        completed_at=now,
        locked_at=None,
        locked_by="",
    )
    if job.document_id:
        Document.objects.filter(pk=job.document_id).update(
            status=Document.STATUS_FAILED,
            error_message=f"Dosya işlenemedi: {message}",
            processed_at=now,
        )
    return AsyncJob.STATUS_FAILED


def execute_job(job):
    handler = JOB_HANDLERS.get(job.job_type)
    if handler is None:
        raise ValueError(f"Desteklenmeyen job tipi: {job.job_type}")
    result = handler(job)
    complete_job(job, result)
    return result


def recover_stale_jobs():
    stale_seconds = getattr(settings, "JOB_STALE_TIMEOUT", 7200)
    now = timezone.now()
    threshold = now - timedelta(seconds=stale_seconds)
    stale_jobs = AsyncJob.objects.filter(
        status=AsyncJob.STATUS_RUNNING,
        locked_at__lt=threshold,
    )
    exhausted = stale_jobs.filter(attempts__gte=F("max_attempts"))
    exhausted_document_ids = list(
        exhausted.exclude(document_id=None).values_list("document_id", flat=True)
    )
    failed_count = exhausted.update(
        status=AsyncJob.STATUS_FAILED,
        error_message="Worker zaman aşımına uğradı ve deneme sınırı aşıldı.",
        completed_at=now,
        locked_at=None,
        locked_by="",
    )
    if exhausted_document_ids:
        Document.objects.filter(pk__in=exhausted_document_ids).update(
            status=Document.STATUS_FAILED,
            error_message="Dosya işlenemedi: worker zaman aşımı.",
            processed_at=now,
        )

    requeued_count = stale_jobs.filter(attempts__lt=F("max_attempts")).update(
        status=AsyncJob.STATUS_QUEUED,
        progress=0,
        locked_at=None,
        locked_by="",
        available_at=now,
        error_message="Worker zaman aşımından sonra yeniden sıraya alındı.",
    )
    return failed_count + requeued_count
