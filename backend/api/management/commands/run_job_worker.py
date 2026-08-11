import os
import socket
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from api.services.job_queue import (
    claim_next_job,
    execute_job,
    fail_or_retry_job,
    recover_stale_jobs,
)


class Command(BaseCommand):
    help = "Kalıcı asenkron job kuyruğundaki işleri çalıştırır."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="En fazla bir job çalıştırıp çıkar.")
        parser.add_argument("--poll-interval", type=float, default=1.0)
        parser.add_argument("--worker-id", default="")

    def handle(self, *args, **options):
        worker_id = options["worker_id"] or f"{socket.gethostname()}:{os.getpid()}"
        poll_interval = max(0.1, options["poll_interval"])
        recover_stale_jobs()
        next_recovery_at = time.monotonic() + 60
        self.stdout.write(f"Job worker hazır: {worker_id}")

        while True:
            if time.monotonic() >= next_recovery_at:
                recover_stale_jobs()
                next_recovery_at = time.monotonic() + 60
            close_old_connections()
            job = claim_next_job(worker_id)
            if job is None:
                if options["once"]:
                    return
                time.sleep(poll_interval)
                continue

            self.stdout.write(f"Job başladı: {job.id} ({job.job_type}, deneme {job.attempts})")
            try:
                execute_job(job)
            except Exception as exc:  # Worker must remain alive after an individual job failure.
                state = fail_or_retry_job(job, exc)
                self.stderr.write(f"Job {job.id} {state}: {exc}")
            else:
                self.stdout.write(self.style.SUCCESS(f"Job tamamlandı: {job.id}"))

            if options["once"]:
                return
