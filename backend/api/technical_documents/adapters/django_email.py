"""Django e-mail adapter for the technical-document sender port."""

from collections.abc import Sequence

from django.conf import settings
from django.core.mail import EmailMessage


class DjangoEmailSender:
    def send(self, *, subject: str, body: str, bcc: Sequence[str]) -> None:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            bcc=list(bcc),
        )
        email.send(fail_silently=False)
