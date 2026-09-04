from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from src.infraestructura.cpitlp_temporal_reference_extractor import (
    CPITLPTemporalReferenceClaim,
)


SCHEMA_VERSION = "temporal-reference-claim-v1"


def write_temporal_reference_claims(
    path: str | Path,
    claims: Iterable[CPITLPTemporalReferenceClaim],
) -> None:
    """Persist immutable primary-reference temporal claims as JSONL."""

    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for claim in claims:
            payload = {
                "schema_version": SCHEMA_VERSION,
                **asdict(claim),
            }

            handle.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )


def load_temporal_reference_claims(
    path: str | Path,
) -> tuple[CPITLPTemporalReferenceClaim, ...]:
    """Load the immutable temporal-reference sidecar fail-closed."""

    claims: list[
        CPITLPTemporalReferenceClaim
    ] = []

    for line_number, line in enumerate(
        Path(path).read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        payload = json.loads(line)

        if (
            payload.get("schema_version")
            != SCHEMA_VERSION
        ):
            raise ValueError(
                "Unsupported temporal reference "
                f"claim schema at line {line_number}."
            )

        claims.append(
            CPITLPTemporalReferenceClaim(
                source_id=str(
                    payload["source_id"]
                ),
                source_url=payload.get(
                    "source_url"
                ),
                acquired_at=payload.get(
                    "acquired_at"
                ),
                raw_document_id=str(
                    payload["raw_document_id"]
                ),
                economic_object_raw=str(
                    payload[
                        "economic_object_raw"
                    ]
                ),
                price_raw=str(
                    payload["price_raw"]
                ),
                valid_from=str(
                    payload["valid_from"]
                ),
                valid_to=payload.get(
                    "valid_to"
                ),
                raw_basis=str(
                    payload["raw_basis"]
                ),
                extractor_version=str(
                    payload[
                        "extractor_version"
                    ]
                ),
                provenance=tuple(
                    payload.get(
                        "provenance",
                        (),
                    )
                ),
            )
        )

    return tuple(claims)
