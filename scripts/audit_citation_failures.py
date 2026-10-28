"""Read-only PDF quote audit; never change labels or assign semantic correctness."""

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf


def normalize(value):
    return re.sub(r"\s+", " ", value).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output filename")
    report = json.loads(args.collection.read_text(encoding="utf-8"))
    rows = []
    for case in report["cases"]:
        if case.get("citation_correct") or case.get("status") != "completed":
            continue
        row = {
            "case_id": case["case_id"],
            "abstained": case["abstained"],
            "expected_document": case["expected_document"],
            "expected_pages": case["expected_pages"],
            "generated_answer": case["generated_answer"],
            "attempts": [],
            "pdf_quote_checks": [],
        }
        retrieved = {r["chunk"]["chunk_id"]: r["chunk"] for r in case["retrieved"]}
        for attempt in case["diagnostics"]:
            raw = attempt.get("provider_output", "")
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                parsed = {}
            evidence = parsed.get("evidence", []) if isinstance(parsed, dict) else []
            checks = []
            for entry in evidence:
                label, quote = entry.get("source_id"), entry.get("quote", "")
                source = attempt.get("sources", {}).get(label)
                exact_sources = [
                    sid
                    for sid, meta in attempt.get("sources", {}).items()
                    if quote
                    and normalize(quote)
                    in normalize(retrieved.get(meta["chunk_id"], {}).get("text", ""))
                ]
                checks.append(
                    {"source_id": label, "quote": quote, "exact_source_matches": exact_sources}
                )
                if attempt["status"] != "accepted" or not source:
                    continue
                pdf_path = Path("data/raw/financebench/pdfs") / source["document_name"]
                with pymupdf.open(pdf_path) as pdf:
                    pages = source["pages"]
                    text = " ".join(pdf[p - 1].get_text() for p in pages)
                row["pdf_quote_checks"].append(
                    {
                        "document": pdf_path.name,
                        "pages": pages,
                        "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                        "quote": quote,
                        "exact_whitespace_normalized_match": bool(quote)
                        and normalize(quote) in normalize(text),
                    }
                )
            row["attempts"].append({"status": attempt["status"], "quote_checks": checks})
        rows.append(row)
    output = {
        "collection_sha256": hashlib.sha256(args.collection.read_bytes()).hexdigest(),
        "scope": "Quote location audit, not entailment or approved label correction",
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(
            row["case_id"],
            "abstained",
            row["abstained"],
            "PDF quotes",
            [c["exact_whitespace_normalized_match"] for c in row["pdf_quote_checks"]],
            "failed quotes found elsewhere",
            sum(
                bool(q["exact_source_matches"]) and q["source_id"] not in q["exact_source_matches"]
                for a in row["attempts"]
                for q in a["quote_checks"]
            ),
        )


if __name__ == "__main__":
    main()
