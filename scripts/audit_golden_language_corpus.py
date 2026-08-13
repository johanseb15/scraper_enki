from __future__ import annotations
import argparse,csv,json
from collections import Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--corpus",default="data/language/golden_corpus_v1.jsonl")
    ap.add_argument("--review",default="data/language/golden_corpus_review_v1.csv")
    args=ap.parse_args()

    corpus=[json.loads(x) for x in Path(args.corpus).read_text(encoding="utf-8").splitlines() if x.strip()]
    with Path(args.review).open("r",encoding="utf-8-sig",newline="") as f:
        review=list(csv.DictReader(f))

    cids={x["id"] for x in corpus}
    rids={x["id"] for x in review}
    missing=sorted(cids-rids)
    extra=sorted(rids-cids)
    counts=Counter(x["review_status"] for x in review)

    print("ENKI GOLDEN LANGUAGE AUDIT v1")
    print("=============================")
    print(f"Corpus cases: {len(corpus)}")
    print(f"Reviewed:     {len(review)}")
    print("\nSTATUS")
    for k,v in counts.most_common():
        print(f"{k:20} {v:3}")
    print(f"\nMissing review IDs: {missing or 'none'}")
    print(f"Extra review IDs:   {extra or 'none'}")

    print("\nPRIORITY NEEDS_IMPROVEMENT")
    for row in review:
        if row["review_status"]=="NEEDS_IMPROVEMENT":
            print(f'{row["id"]} | {row["review_notes"]}')

    if missing or extra:
        raise SystemExit(2)

if __name__=="__main__":
    main()
