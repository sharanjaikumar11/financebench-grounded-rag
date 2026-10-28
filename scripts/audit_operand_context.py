"""Inspect required row-family coverage in a saved retrieval run, without API calls."""

import argparse
import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

from rag_system.generation.answering import _generation_evidence_sources
from rag_system.retrieval.financial_intent import operand_patterns
from rag_system.retrieval.vector_store import SQLiteVectorStore
from rag_system.schemas import RetrievedChunk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; choose a new filename")
    raw = args.retrieval.read_bytes()
    retrieval = json.loads(raw)
    if retrieval["status"] != "complete":
        parser.error("Retrieval run is incomplete")
    baseline = json.loads(args.baseline.read_bytes())
    old = {c["case_id"]: c for c in baseline["cases"]}
    os.environ.update(retrieval["run_metadata"]["settings"])
    records = []
    with sqlite3.connect(args.vector_store.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for case in retrieval["cases"]:
            patterns = operand_patterns(case["question"])
            before = old[case["case_id"]]
            if not patterns and not before.get("abstained"):
                continue
            hits = tuple(
                RetrievedChunk(
                    SQLiteVectorStore._row_to_chunk(
                        db.execute(
                            "SELECT * FROM chunks WHERE chunk_id=?", (item["chunk_id"],)
                        ).fetchone()
                    ),
                    0.0,
                )
                for item in case["retrieved"]
            )
            selected = _generation_evidence_sources(case["question"], hits)
            selected_text = [re.sub(r"[^a-z0-9]+", " ", hit.chunk.text.lower()) for hit in selected]
            baseline_text = []
            if before.get("diagnostics"):
                ids = {s["chunk_id"] for s in before["diagnostics"][0]["sources"].values()}
                baseline_text = [
                    re.sub(r"[^a-z0-9]+", " ", item["chunk"]["text"].lower())
                    for item in before["retrieved"]
                    if item["chunk"]["chunk_id"] in ids
                ]

            def covered(texts):
                return [
                    p
                    for p in patterns
                    if any(re.search(r"\b(?:" + p + r")\s+\d", t) for t in texts)
                ]

            records.append(
                {
                    "case_id": case["case_id"],
                    "question": case["question"],
                    "required_row_patterns": patterns,
                    "baseline_covered": covered(baseline_text),
                    "candidate_covered": covered(selected_text),
                    "selected": [
                        {
                            "chunk_id": h.chunk.chunk_id,
                            "pages": h.chunk.page_numbers,
                            "document": h.chunk.document_name,
                            "text": h.chunk.text,
                        }
                        for h in selected
                    ],
                }
            )
    report = {
        "scope": "Offline row-family coverage; not period alignment, complete operands or answer accuracy.",
        "retrieval_sha256": hashlib.sha256(raw).hexdigest(),
        "cases": records,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for row in records:
        print(
            row["case_id"],
            len(row["baseline_covered"]),
            "->",
            len(row["candidate_covered"]),
            "/",
            len(row["required_row_patterns"]),
        )


if __name__ == "__main__":
    main()
