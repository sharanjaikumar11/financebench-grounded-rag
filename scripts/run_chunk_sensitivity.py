"""Bounded retrieval-only chunk size/overlap experiment on complete case filings."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from rag_system.chunking.strategies import FixedTokenChunker
from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.metrics import retrieval_hit, retrieval_page_hit
from rag_system.evaluation.provenance import run_metadata
from rag_system.evaluation.runner import _inferred_filing_filter
from rag_system.generation.answering import _generation_evidence_sources
from rag_system.ingestion.parsers import ParserRegistry
from rag_system.ingestion.pipeline import file_hash
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever
from rag_system.retrieval.vector_store import SQLiteVectorStore

CONFIGURATIONS = ((100, 40), (200, 40), (300, 40), (200, 0), (200, 80))


def summarize(rows):
    labelled = [r for r in rows if r["page_hit"] is not None]
    return {
        "case_count": len(rows),
        "page_labelled_case_count": len(labelled),
        "filing_recall": sum(r["filing_hit"] for r in rows) / len(rows),
        "page_recall": sum(r["page_hit"] for r in labelled) / len(labelled) if labelled else None,
        "selected_page_recall": sum(r["selected_page_hit"] for r in labelled) / len(labelled)
        if labelled
        else None,
        "mean_selected_tokens": sum(r["selected_tokens"] for r in rows) / len(rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--pdf-directory", type=Path, default=Path("data/raw/financebench/pdfs"))
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists():
        parser.error("Choose a new output directory; previous runs are never overwritten")
    cases = load_evaluation_cases(args.cases)
    names = sorted({c.expected_document for c in cases})
    paths = [args.pdf_directory / name for name in names]
    if any(not p.is_file() for p in paths):
        parser.error("All case filings must exist locally")
    # Fix the experimental settings independently of the calling terminal.
    os.environ.update(
        STATEMENT_AWARE_RANKING="1",
        FINANCIAL_INTENT_RANKING="0",
        RERANKER_MODEL="",
        HF_HUB_OFFLINE="1",
    )
    import torch

    torch.set_num_threads(4)
    args.output_directory.mkdir(parents=True)
    documents = []
    for path in paths:
        digest = file_hash(path)
        documents.append(ParserRegistry().parse(path, f"doc_{digest[:16]}", digest))
        print(f"Parsed complete filing {path.name}", flush=True)
    embedder = SentenceTransformerEmbeddingProvider()
    manifest = {
        "scope": "Retrieval only, all original cases, complete expected filings; reduced corpus",
        "dataset_sha256": file_hash(args.cases),
        "source_sha256": {p.name: file_hash(p) for p in paths},
        "configurations": CONFIGURATIONS,
        "top_k": 3,
        "selection_note": "Expected documents select corpus only; queries use inferred routing, not gold filters",
        "results": [],
    }
    for size, overlap in CONFIGURATIONS:
        started = time.monotonic()
        path = args.output_directory / f"size{size}_overlap{overlap}.sqlite3"
        store = SQLiteVectorStore(path)
        chunks_count = 0
        try:
            retriever = HybridRetriever(embedder, store)
            for document in documents:
                chunks = FixedTokenChunker(size, overlap).chunk(document)
                retriever.index(chunks)
                chunks_count += len(chunks)
                print(
                    f"{size}/{overlap}: indexed {document.document_name} ({len(chunks)} chunks)",
                    flush=True,
                )
            indexing_seconds = time.monotonic() - started
            rows = []
            for case in cases:
                found = retriever.retrieve(
                    case.question, 3, _inferred_filing_filter(retriever, case.question)
                )
                selected = _generation_evidence_sources(case.question, found)
                rows.append(
                    {
                        "case_id": case.case_id,
                        "filing_hit": retrieval_hit(case, found),
                        "page_hit": retrieval_page_hit(case, found),
                        "selected_page_hit": retrieval_page_hit(case, selected),
                        "retrieved_pages": [list(r.chunk.page_numbers) for r in found],
                        "selected_pages": [list(r.chunk.page_numbers) for r in selected],
                        "selected_tokens": sum(r.chunk.token_count for r in selected),
                    }
                )
            result = {
                "chunk_size": size,
                "overlap": overlap,
                "chunk_count": chunks_count,
                "indexing_seconds": round(indexing_seconds, 2),
                "total_seconds": round(time.monotonic() - started, 2),
                **summarize(rows),
                "cases": rows,
                "metadata": run_metadata(args.cases, path, "hybrid", 3),
            }
        finally:
            store.close()
        result["index_bytes"] = path.stat().st_size
        output = args.output_directory / f"size{size}_overlap{overlap}.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        manifest["results"].append(
            {
                "file": output.name,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                **{k: v for k, v in result.items() if k not in {"cases", "metadata"}},
            }
        )
        (args.output_directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Completed {size}/{overlap}: {summarize(rows)}", flush=True)


if __name__ == "__main__":
    main()
