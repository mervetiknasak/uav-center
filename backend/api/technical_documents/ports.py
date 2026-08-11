"""Infrastructure ports used by technical-document use cases."""

from collections.abc import Sequence
from typing import Protocol


class EmailSender(Protocol):
    """Minimal outbound e-mail capability required by notifications."""

    def send(self, *, subject: str, body: str, bcc: Sequence[str]) -> None: ...
