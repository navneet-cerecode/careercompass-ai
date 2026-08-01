"""Opaque, stateless capabilities for anonymous task polling."""

import base64
import hashlib
import hmac
from uuid import UUID


class TaskCapability:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise ValueError("Task capability secrets must contain at least 32 bytes.")
        self._secret = secret

    def issue(self, task_id: UUID) -> str:
        digest = hmac.new(self._secret, task_id.bytes, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def verify(self, task_id: UUID, token: str) -> bool:
        return hmac.compare_digest(self.issue(task_id), token)
