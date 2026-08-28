from src.aplicacion.acquisition_failure import (
    AcquisitionFailure,
    AcquisitionFailureCategory,
    acquisition_failure_from_exception,
)


def test_network_failure_preserves_typed_cause_without_secret_leak():
    error = TimeoutError(
        "request failed Authorization: Bearer super-secret-token"
    )

    failure = acquisition_failure_from_exception(
        source="ted",
        operation="search",
        exc=error,
    )

    assert isinstance(failure, AcquisitionFailure)
    assert failure.source == "ted"
    assert failure.operation == "search"
    assert failure.category is AcquisitionFailureCategory.NETWORK
    assert failure.retryable is True
    assert failure.exception_type == "TimeoutError"

    assert "super-secret-token" not in failure.message_redacted
    assert "Bearer" not in failure.message_redacted


def test_unknown_runtime_failure_fails_closed():
    failure = acquisition_failure_from_exception(
        source="test-source",
        operation="download",
        exc=RuntimeError("unexpected boom"),
    )

    assert failure.category is AcquisitionFailureCategory.UNKNOWN
    assert failure.retryable is False
    assert failure.exception_type == "RuntimeError"
    assert failure.message_redacted == "unexpected boom"



def test_http_401_is_auth_and_not_retryable():
    from urllib.error import HTTPError

    error = HTTPError(
        "https://example.test",
        401,
        "Unauthorized",
        hdrs=None,
        fp=None,
    )

    failure = acquisition_failure_from_exception(
        source="test-source",
        operation="search",
        exc=error,
    )

    assert failure.category is AcquisitionFailureCategory.AUTH
    assert failure.retryable is False


def test_http_503_is_http_and_retryable():
    from urllib.error import HTTPError

    error = HTTPError(
        "https://example.test",
        503,
        "Service Unavailable",
        hdrs=None,
        fp=None,
    )

    failure = acquisition_failure_from_exception(
        source="test-source",
        operation="search",
        exc=error,
    )

    assert failure.category is AcquisitionFailureCategory.HTTP
    assert failure.retryable is True


def test_url_error_is_network_and_retryable():
    from urllib.error import URLError

    failure = acquisition_failure_from_exception(
        source="test-source",
        operation="download",
        exc=URLError("connection refused"),
    )

    assert failure.category is AcquisitionFailureCategory.NETWORK
    assert failure.retryable is True


def test_wrapped_transport_error_uses_original_cause():
    from urllib.error import URLError

    cause = URLError("connection reset")

    try:
        raise RuntimeError("request failed") from cause
    except RuntimeError as error:
        failure = acquisition_failure_from_exception(
            source="test-source",
            operation="search",
            exc=error,
        )

    assert failure.category is AcquisitionFailureCategory.NETWORK
    assert failure.retryable is True
    assert failure.exception_type == "RuntimeError"
