from __future__ import annotations


_OLE_COMPOUND_FILE_MAGIC = bytes.fromhex(
    "d0cf11e0a1b11ae1"
)

_REQUIRED_MARKERS = (
    "honorarios de referencia",
    "ciencias inform",
    "hardware/software",
)


def extract_cpitlp_msword_text(
    raw_bytes: bytes,
) -> str | None:
    """Project a CPITLP legacy Word OLE document to deterministic text.

    This is deliberately source-specific. It does not attempt to implement a
    general Microsoft Word/OLE parser.

    The projection is admitted only when:
    - the binary has the OLE Compound File signature;
    - UTF-16LE decoding yields the CPITLP Informatics reference markers.

    Binary NUL noise and whitespace are normalized, but lexical content is not
    otherwise rewritten.
    """

    if not raw_bytes.startswith(
        _OLE_COMPOUND_FILE_MAGIC
    ):
        return None

    decoded = raw_bytes.decode(
        "utf-16le",
        errors="ignore",
    )

    text = " ".join(
        decoded.replace(
            "\x00",
            " ",
        ).split()
    )

    folded = text.casefold()

    if not all(
        marker in folded
        for marker in _REQUIRED_MARKERS
    ):
        return None

    return text
