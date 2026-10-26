"""Named errors. Callers catch these, never a vendor SDK's exception types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error this package raises on purpose."""


class ModelError(DomainError):
    """A model call failed."""


class TransientModelError(ModelError):
    """The call may succeed if repeated: a timeout, a rate limit, a 5xx, a dropped connection."""


class PermanentModelError(ModelError):
    """Repeating the call cannot help: a bad request, a bad key, a refusal to parse."""


class RecordingMissing(PermanentModelError):
    """The recorded adapter has no response for this request. Re-record with `make record`."""


class UnsupportedParameter(PermanentModelError):
    """The adapter cannot honor a parameter the request asked for (for example sampling on Claude)."""
