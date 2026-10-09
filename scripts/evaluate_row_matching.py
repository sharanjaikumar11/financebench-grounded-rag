"""Compare statement ranking with/without row matching on full expanded context."""

import json
import os
from pathlib import Path

from rag_system.evaluation.datasets import load_evaluation_cases
from rag_system.evaluation.metrics import retrieval_page_hit
from rag_system.retrieval import vector_store
from rag_system.retrieval.embeddings import SentenceTransformerEmbeddingProvider
from rag_system.retrieval.retriever import HybridRetriever


def main():
    os.environ["STATEMENT_AWARE_RANKING"] = "1"
    os.environ.pop("RERANKER_MODEL", None)
    store = vector_store.SQLiteVectorStore(
        Path("data/processed/local_sentence_transformers/vectors.sqlite3")
    )
    retriever = HybridRetriever(SentenceTransformerEmbeddingProvider(), store)
    scorer = vector_store._financial_row_relevance
    records = []
    try:
        for case in load_evaluation_cases(Path("evaluation/cases.json")):
            record = {"case_id": case.case_id}
            for enabled in (False, True):
                vector_store._financial_row_relevance = scorer if enabled else lambda *_: 0.0
                evidence = retriever.retrieve(
                    case.question, 3, store.infer_filing_metadata_filter(case.question)
                )
                record["row_matching" if enabled else "baseline"] = {
                    "page_hit": retrieval_page_hit(case, evidence),
                    "pages": [item.chunk.page_numbers for item in evidence],
                    "texts": [item.chunk.text for item in evidence],
                }
            records.append(record)
            print(
                case.case_id,
                record["baseline"]["page_hit"],
                record["row_matching"]["page_hit"],
                flush=True,
            )
    finally:
        vector_store._financial_row_relevance = scorer
        store.close()
    target = Path("evaluation/results/row_matching_retrieval.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
