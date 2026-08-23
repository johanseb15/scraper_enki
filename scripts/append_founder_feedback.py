from argparse import ArgumentParser
from datetime import datetime, timezone

from src.infraestructura.human_real_intake import append_founder_feedback


def main():
    parser = ArgumentParser(description="Append founder feedback to a HUMAN_REAL trace.")
    parser.add_argument("--trace-id", required=True)
    parser.add_argument("--label", action="append", required=True)
    parser.add_argument("--note")
    parser.add_argument("--out", default="data/field/human_real_founder_feedback_v1.jsonl")
    args = parser.parse_args()
    event = append_founder_feedback(
        args.out,
        trace_id=args.trace_id,
        received_at=datetime.now(timezone.utc).isoformat(),
        labels=args.label,
        note=args.note,
    )
    print(f"FEEDBACK_EVENT_ID={event['feedback_event_id']}")
    print("PROMOTION_AUTHORIZED=False")


if __name__ == "__main__":
    main()
