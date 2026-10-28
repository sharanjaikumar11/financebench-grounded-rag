"""Replay fixed retrieved chunks to isolate bounded-context selection changes."""

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

from rag_system.evaluation.datasets import EvaluationCase
from rag_system.evaluation.metrics import retrieval_page_hit
from rag_system.generation.answering import _generation_evidence_sources
from rag_system.schemas import DocumentChunk, RetrievedChunk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--vector-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output file")
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    if raw.get("status") != "complete":
        parser.error("Requires a complete retrieval diagnostic")
    settings = raw["run_metadata"]["settings"]
    os.environ["FINANCIAL_INTENT_RANKING"] = settings.get("FINANCIAL_INTENT_RANKING", "0")
    results = []
    with sqlite3.connect(args.vector_store.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        for item in raw["cases"]:
            sources = []
            for saved in item["retrieved"]:
                row = db.execute(
                    "SELECT * FROM chunks WHERE chunk_id=?", (saved["chunk_id"],)
                ).fetchone()
                if (
                    row is None
                    or row["document_name"] != saved["document"]
                    or json.loads(row["page_numbers"]) != saved["pages"]
                ):
                    raise ValueError("Saved source identity no longer matches index")
                sources.append(
                    RetrievedChunk(
                        DocumentChunk(
                            row["chunk_id"],
                            row["document_id"],
                            row["document_name"],
                            row["chunk_index"],
                            row["text"],
                            row["token_count"],
                            row["chunking_strategy"],
                            tuple(json.loads(row["page_numbers"])),
                            tuple(json.loads(row["section_titles"])),
                        ),
                        0.0,
                    )
                )
            # Reference labels are used only by the scorer, never the selector.
            case = EvaluationCase(
                item["case_id"],
                item["question"],
                "",
                item["expected_document"],
                tuple(item["expected_pages"]),
            )
            result = {"case_id": case.case_id, "retrieval_page_hit": item["page_hit"]}
            for name, flag in (("baseline", "0"), ("diverse", "1")):
                os.environ["CONTEXT_DIVERSITY_RANKING"] = flag
                selected = _generation_evidence_sources(case.question, sources)
                result[name] = {
                    "page_hit": retrieval_page_hit(case, selected),
                    "chunks": [s.chunk.chunk_id for s in selected],
                }
            if result["baseline"]["page_hit"] != item["generation_page_hit"]:
                raise ValueError(f"Baseline replay differs: {case.case_id}")
            results.append(result)
    labelled = [r for r in results if r["retrieval_page_hit"] is not None]
    report = {
        "scope": "50-case draft, retrieval replay only; no live generation or held-out claim",
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "selector_sha256": hashlib.sha256(
            Path("src/rag_system/generation/answering.py").read_bytes()
        ).hexdigest(),
        "labelled_count": len(labelled),
        "baseline_hits": sum(r["baseline"]["page_hit"] for r in labelled),
        "diverse_hits": sum(r["diverse"]["page_hit"] for r in labelled),
        "regressions": [
            r["case_id"]
            for r in labelled
            if r["baseline"]["page_hit"] and not r["diverse"]["page_hit"]
        ],
        "gains": [
            r["case_id"]
            for r in labelled
            if not r["baseline"]["page_hit"] and r["diverse"]["page_hit"]
        ],
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
