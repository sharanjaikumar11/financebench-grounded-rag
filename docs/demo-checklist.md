# FinanceBench demo checklist

## Before presenting

1. Activate the project environment and set `GEMINI_API_KEY`. Set `GEMINI_FALLBACK_MODEL` if a fallback model is available.
2. Confirm `data/processed/local_sentence_transformers/vectors.sqlite3` and the FinanceBench PDFs under `data/raw/financebench/pdfs/` are present on the demonstration machine.
3. Run `python -m pytest -q`.
4. Run the expanded retrieval evaluation using `evaluation/cases.json`. The evaluator requires enough available memory for the 1.86 GB local vector index.
5. With the Gemini key set, run the grounded generation evaluation and save its report under `evaluation/results/`.
6. Update `docs/experiment-report.md` only with the newly generated measured metrics.

## Live demonstration sequence

1. Ask a table-based annual question, such as Best Buy FY2019 inventory, and open its linked source page.
2. Ask a quarter-specific question, such as JPMorgan Q2 2022 highest segment net income, to demonstrate 10-Q routing.
3. Ask a financial-statement synonym question, such as Microsoft FY2016 cost of goods sold, to demonstrate terminology expansion and table-aware reranking.
4. Ask an unsupported question to demonstrate `INSUFFICIENT_CONTEXT` rather than an invented answer.
5. If the primary Gemini model is temporarily unavailable, explain that the system retries the configured fallback only for a capacity error.

## Talking points

- Retrieval remains local: MiniLM embeddings load from the local model cache, and SQLite provides vector storage plus FTS5/BM25 lexical search.
- The reranker is a generic financial-table heuristic, not an answer lookup. It prioritizes evidence using query-term coverage, numeric density, and statement-heading signals.
- Citations are grounded in retrieved chunks and open the locally indexed PDF at the first cited page.
- The original three-case results are historical. The expanded 11-case set is the correct basis for the final reported metrics after its run completes.
