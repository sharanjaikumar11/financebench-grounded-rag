# Retrieval experiment report

## Scope

This report evaluates an expanded 11-case FinanceBench set against the complete local corpus of 363 unique documents. The set includes annual filings, a quarter-specific 10-Q, statement-table questions, and a derivative-instrument comparison. The measured configuration uses the `all-MiniLM-L6-v2` local embedding model, SQLite hybrid retrieval (dense cosine similarity plus FTS5 BM25 fused with reciprocal-rank fusion), and inferred filing metadata filtering when the indexed filing can be identified unambiguously.

The metadata filter is part of the evaluated configuration because the baseline dense-only system retrieved similar filings from incorrect years. The filter restricts those unambiguous queries to the matching filing before ranking chunks.

The current implementation adds quarter-aware 10-Q routing, annual 10-K preference, financial-statement synonym expansion, table-aware reranking, diversified anchors, and neighboring context. Each evaluation case records an expected filing and, where directly established from source evidence, expected PDF pages.

## Results

| Chunking strategy | Retrieval mode | K | Expected-filing recall |
| --- | --- | ---: | ---: |
| Fixed-token (200 tokens, 40 overlap) | Hybrid with inferred filing metadata | 3 | 100% (11/11) |

The measured run retrieved the expected filing for all 11 cases at K=3. This metric is **document-level recall**: it verifies that at least one of the retrieved chunks came from the expected filing. It does not by itself establish that the retrieved chunk contains the exact answer row or expected PDF page.

## Final production selection

Fixed-token chunking with 200 tokens and 40-token overlap is the production configuration. It provides controlled overlapping context across page and table boundaries and matches the existing API indexing workflow. The production API uses hybrid retrieval with `top_k=3` and generic index-backed filing metadata filtering.

## Baseline comparison

The original unfiltered fixed-token dense baseline achieved 33.3% recall@10 (1/3) on the original three-case set. The current 11-case hybrid evaluation achieved 100% expected-filing recall@3 by using generic index-backed filing identification, including quarter-aware 10-Q routing. These are different evaluation sets and configurations, so they are not a direct controlled baseline comparison.

## Artifacts

The machine-readable reports are generated locally under `evaluation/results/`:

- `fixed_token_hybrid_top_k_3_metadata_filtered.json`
- `fixed_token_hybrid_top_k_5_metadata_filtered.json`
- `fixed_token_hybrid_top_k_10_metadata_filtered.json`
- `section_aware_hybrid_top_k_3_metadata_filtered.json`
- `section_aware_hybrid_top_k_5_metadata_filtered.json`
- `section_aware_hybrid_top_k_10_metadata_filtered.json`
- `fixed_token_hybrid_top_k_3_expanded.json` (current 11-case measured run)

## Limits

These results measure retrieval recall only. Answer accuracy, grounding, citation correctness, and source-page correctness remain separate generation evaluations and are not inferred from retrieval recall. The Gemini generation evaluation must be run with `GEMINI_API_KEY` configured in the same terminal before those metrics can be reported.
