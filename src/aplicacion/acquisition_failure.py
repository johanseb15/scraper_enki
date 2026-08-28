from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from urllib.error import HTTPError, URLError


class AcquisitionFailureCategory(str, Enum):
    NETWORK = "NETWORK"
    AUTH = "AUTH"
    HTTP = "HTTP"
    SCHEMA = "SCHEMA"
    DECODE = "DECODE"
    PARSE = "PARSE"
    PERSISTENCE = "PERSISTENCE"
    RUNTIME = "RUNTIME"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AcquisitionFailure:
    source: str
    operation: str
    category: AcquisitionFailureCategory
    retryable: bool
    exception_type: str
    message_redacted: str
    resource_id: str | None = None


_SECRET_PATTERNS = (
    re.compile(
        r"(?i)(authorization\s*[:=]\s*)([^\s,;]+(?:\s+[^\s,;]+)?)"
    ),
    re.compile(
        r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+"
    ),
    re.compile(
        r"(?i)(cookie\s*[:=]\s*)[^\s,;]+"
    ),
    re.compile(
        r"(?i)(token\s*[:=]\s*)[^\s,;]+"
    ),
    re.compile(
        r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"
    ),
)


def redact_failure_message(message: str) -> str:
    redacted = str(message)

    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda match: (
                match.group(1) + "[REDACTED]"
                if match.lastindex
                else "[REDACTED]"
            ),
            redacted,
        )

    return redacted


def _classify_single_exception(
    exc: BaseException,
) -> tuple[AcquisitionFailureCategory, bool] | None:
    # HTTPError is a URLError subclass, so HTTP must be classified first.
    if isinstance(exc, HTTPError):
        status = int(exc.code)

        if status in {401, 403}:
            return AcquisitionFailureCategory.AUTH, False

        retryable = (
            status in {408, 425, 429}
            or 500 <= status <= 599
        )

        return AcquisitionFailureCategory.HTTP, retryable

    if isinstance(exc, URLError):
        return AcquisitionFailureCategory.NETWORK, True

    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
        ),
    ):
        return AcquisitionFailureCategory.NETWORK, True

    if isinstance(exc, UnicodeError):
        return AcquisitionFailureCategory.DECODE, False

    if isinstance(
        exc,
        (
            ValueError,
            TypeError,
            KeyError,
        ),
    ):
        return AcquisitionFailureCategory.PARSE, False

    return None


def _exception_chain(
    exc: BaseException,
):
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None:
        identity = id(current)

        if identity in seen:
            break

        seen.add(identity)
        yield current

        if current.__cause__ is not None:
            current = current.__cause__
        elif (
            current.__context__ is not None
            and not current.__suppress_context__
        ):
            current = current.__context__
        else:
            current = None


def _classify_exception(
    exc: Exception,
) -> tuple[AcquisitionFailureCategory, bool]:
    for candidate in _exception_chain(exc):
        classification = _classify_single_exception(candidate)

        if classification is not None:
            return classification

    return AcquisitionFailureCategory.UNKNOWN, False


def acquisition_failure_from_exception(
    *,
    source: str,
    operation: str,
    exc: Exception,
    resource_id: str | None = None,
    category_override: AcquisitionFailureCategory | None = None,
    retryable_override: bool | None = None,
) -> AcquisitionFailure:
    category, retryable = _classify_exception(exc)

    if category_override is not None:
        category = category_override

    if retryable_override is not None:
        retryable = retryable_override

    return AcquisitionFailure(
        source=source,
        operation=operation,
        category=category,
        retryable=retryable,
        exception_type=type(exc).__name__,
        message_redacted=redact_failure_message(str(exc)),
        resource_id=resource_id,
    )
