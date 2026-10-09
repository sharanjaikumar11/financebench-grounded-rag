"""Run a controlled index/reranker matrix and retain full retrieved evidence."""

import argparse
import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.metrics import retrieval_hit, retrieval_page_hit
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.reranking import CrossEncoderReranker
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--tables", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/results/comparison"))
    args = parser.parse_args()
    cases = load_evaluation_cases(args.cases)
    os.environ.pop("RERANKER_MODEL", None)
    embedder = SentenceTransformerEmbeddingProvider()
    reranker = CrossEncoderReranker(args.model)
    args.output.mkdir(parents=True, exist_ok=True)
    for label, path in [("baseline", args.baseline), ("tables", args.tables)]:
        if path is None:
            continue
        if not path.is_file():
            raise FileNotFoundError(path)
        # Preflight the same benchmark filings without creating a missing database.
        with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as connection:
            documents = {
                row[0] for row in connection.execute("SELECT DISTINCT document_name FROM chunks")
            }
        missing = {case.expected_document for case in cases} - documents
        if missing:
            raise ValueError(f"{label} index missing benchmark filings: {sorted(missing)}")
        for enabled in (False, True):
            name = f"{label}_{'reranked' if enabled else 'hybrid'}"
            store = SQLiteVectorStore(path)
            records = []
            try:
                retriever = HybridRetriever(embedder, store, reranker if enabled else None, 30)
                for case in cases:
                    start = perf_counter()
                    evidence = retriever.retrieve(
                        case.question, 3, store.infer_filing_metadata_filter(case.question)
                    )
                    records.append(
                        dict(
                            case_id=case.case_id,
                            retrieval_hit=retrieval_hit(case, evidence),
                            page_hit=retrieval_page_hit(case, evidence),
                            seconds=perf_counter() - start,
                            evidence=[asdict(item) for item in evidence],
                        )
                    )
                    print(name, case.case_id, records[-1]["page_hit"], flush=True)
                labelled = [r for r in records if r["page_hit"] is not None]
                report = dict(
                    configuration=name,
                    index=str(path),
                    document_count=len(documents),
                    top_k=3,
                    candidate_k=30 if enabled else None,
                    reranker=args.model if enabled else None,
                    case_count=len(records),
                    page_labelled_count=len(labelled),
                    filing_recall=sum(r["retrieval_hit"] for r in records) / len(records),
                    page_recall=sum(r["page_hit"] for r in labelled) / len(labelled)
                    if labelled
                    else None,
                    total_seconds=sum(r["seconds"] for r in records),
                    cases=records,
                )
                (args.output / f"{name}.json").write_text(
                    json.dumps(report, indent=2), encoding="utf-8"
                )
            finally:
                store.close()


if __name__ == "__main__":
    main()
