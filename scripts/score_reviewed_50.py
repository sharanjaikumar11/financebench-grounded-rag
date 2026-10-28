"""Apply evidence-review decisions without dropping unresolved benchmark cases."""

import argparse
import hashlib
import json
from pathlib import Path

from rag_system.evaluation.reviewed_scoring import VERSION, apply_review, summarize_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output")
    collected = json.loads(args.collection.read_text(encoding="utf-8"))
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    digest = hashlib.sha256(args.collection.read_bytes()).hexdigest()
    if reviews.get("collection_sha256") != digest:
        parser.error("Reviews must reference this exact collection hash")
    rows = apply_review(collected["cases"], reviews["decisions"])
    original = [r for r in rows if r["cohort"] == "original_11"]
    additions = [r for r in rows if r["cohort"] == "added_39"]
    if len(original) != 11 or len(additions) != 39:
        parser.error("All 50 collected entries are required")
    report = {
        "scoring_version": VERSION,
        "collection_sha256": digest,
        "review_sha256": hashlib.sha256(args.reviews.read_bytes()).hexdigest(),
        "original": summarize_review(original, 11),
        "additions": summarize_review(additions, 39),
        "combined": summarize_review(rows, 50),
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["combined"], indent=2))


if __name__ == "__main__":
    main()
