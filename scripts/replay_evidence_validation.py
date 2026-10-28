"""Replay saved provider outputs against saved sources; no retrieval or API calls."""

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

from rag_system.generation.evidence import inspect_evidence_answer
from rag_system.schemas import DocumentChunk, RetrievedChunk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--financial-decimals",
        action="store_true",
        help="Test strict financial numeric formatting on saved responses",
    )
    parser.add_argument(
        "--absence-validation",
        action="store_true",
        help="Test explicit evidence for acquisition absence claims",
    )
    parser.add_argument(
        "--period-validation",
        action="store_true",
        help="Test explicit heading-period conflicts on saved responses",
    )
    parser.add_argument(
        "--metric-identity",
        action="store_true",
        help="Explicitly test the new metric-identity gate on saved responses",
    )
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; use a new filename")
    raw = args.collection.read_bytes()
    collection = json.loads(raw)
    os.environ["CALCULATION_VALIDATION"] = collection["run_metadata"]["settings"].get(
        "CALCULATION_VALIDATION", "0"
    )
    records = []
    os.environ["ABSENCE_VALIDATION"] = (
        "1"
        if args.absence_validation
        else collection["run_metadata"]["settings"].get("ABSENCE_VALIDATION", "0")
    )
    os.environ["FINANCIAL_DECIMAL_INPUT"] = (
        "1"
        if args.financial_decimals
        else collection["run_metadata"]["settings"].get("FINANCIAL_DECIMAL_INPUT", "0")
    )
    os.environ["PERIOD_VALIDATION"] = (
        "1"
        if args.period_validation
        else collection["run_metadata"]["settings"].get("PERIOD_VALIDATION", "0")
    )
    os.environ["METRIC_IDENTITY_VALIDATION"] = (
        "1"
        if args.metric_identity
        else collection["run_metadata"]["settings"].get("METRIC_IDENTITY_VALIDATION", "0")
    )
    os.environ["COMPARISON_VALIDATION"] = collection["run_metadata"]["settings"].get(
        "COMPARISON_VALIDATION", "0"
    )
    for case in collection["cases"]:
        chunks = {item["chunk"]["chunk_id"]: item for item in case.get("retrieved", [])}
        attempts = []
        for diagnostic in case.get("diagnostics", []):
            sources = {}
            for label, metadata in diagnostic["sources"].items():
                item = chunks[metadata["chunk_id"]]
                if list(item["chunk"]["page_numbers"]) != list(metadata["pages"]):
                    raise ValueError("Source page mismatch; cannot safely replay")
                sources[label] = RetrievedChunk(DocumentChunk(**item["chunk"]), item["score"])
            output = diagnostic.get("provider_output")
            if output is None:
                raise ValueError("Provider output missing; cannot replay")
            if output.strip() == "INSUFFICIENT_CONTEXT":
                answer, status = None, "model_abstention"
            else:
                answer, status = inspect_evidence_answer(output, sources, case["question"])
            attempts.append(
                {
                    "attempt": diagnostic["attempt"],
                    "original_status": diagnostic["status"],
                    "replayed_status": status,
                    "rendered_answer": answer.text if answer else None,
                }
            )
        records.append(
            {
                "case_id": case["case_id"],
                "original_abstained": case.get("abstained"),
                "any_saved_attempt_accepted": any(
                    a["replayed_status"] == "accepted" for a in attempts
                ),
                "attempts": attempts,
            }
        )
    report = {
        "collection_sha256": hashlib.sha256(raw).hexdigest(),
        "metric_identity_validation": os.environ["METRIC_IDENTITY_VALIDATION"],
        "period_validation": os.environ["PERIOD_VALIDATION"],
        "financial_decimal_input": os.environ["FINANCIAL_DECIMAL_INPUT"],
        "absence_validation": os.environ["ABSENCE_VALIDATION"],
        "scope": "Offline validation of saved attempts, not new generation or accuracy scoring. "
        "Saved repair replies were generated under old diagnostics; prompt changes are not measured.",
        "case_count": len(records),
        "cases_with_accepted_saved_attempt": sum(r["any_saved_attempt_accepted"] for r in records),
        "original_abstentions_with_accepted_saved_attempt": [
            r["case_id"]
            for r in records
            if r["original_abstained"] and r["any_saved_attempt_accepted"]
        ],
        "attempt_status_counts": dict(
            Counter(a["replayed_status"] for r in records for a in r["attempts"])
        ),
        "cases": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
