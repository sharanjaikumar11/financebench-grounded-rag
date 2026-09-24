# Retrieval experiment report

## Scope

This report evaluates the initial three committed FinanceBench cases against the complete local corpus of 363 unique documents. Both configurations use the `all-MiniLM-L6-v2` local embedding model, SQLite hybrid retrieval (dense cosine similarity plus FTS5 BM25 fused with reciprocal-rank fusion), and the same inferred filing metadata filter when the question explicitly states a company and fiscal year.

The metadata filter is part of the evaluated configuration because the baseline dense-only system retrieved similar filings from incorrect years. The filter restricts those unambiguous queries to the matching filing before ranking chunks.

The current implementation extends that evaluated pipeline with quarter-aware 10-Q routing, annual 10-K preference, financial-statement synonym expansion, table-aware reranking, diversified anchors, and neighboring context. These changes are implementation improvements motivated by observed failure cases. They have not yet been assigned new quantitative results in this report.

## Results

| Chunking strategy | K=3 recall | K=5 recall | K=10 recall |
| --- | ---: | ---: | ---: |
| Fixed-token (200 tokens, 40 overlap) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| Section-aware (200 tokens, 40 overlap) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

Both strategies retrieved the expected filing for every evaluation case at K=3. Increasing K did not improve document-level recall on this small evaluation set.

## Final production selection

Fixed-token chunking with 200 tokens and 40-token overlap is the production configuration. Both strategies tied on every measured retrieval result, so the decision is based on controlled, overlapping chunks that preserve context across page and table boundaries and match the existing API indexing workflow. The production API uses hybrid retrieval with `top_k=3` and inferred filing metadata filtering.

## Baseline comparison

The unfiltered fixed-token dense baseline achieved 33.3% recall@10 (1/3). Metadata-aware retrieval increased recall@10 to 100% (3/3) by preventing wrong-year filings from competing with the explicitly requested filing.

## Artifacts

The machine-readable reports are generated locally under `evaluation/results/`:

- `fixed_token_hybrid_top_k_3_metadata_filtered.json`
- `fixed_token_hybrid_top_k_5_metadata_filtered.json`
- `fixed_token_hybrid_top_k_10_metadata_filtered.json`
- `section_aware_hybrid_top_k_3_metadata_filtered.json`
- `section_aware_hybrid_top_k_5_metadata_filtered.json`
- `section_aware_hybrid_top_k_10_metadata_filtered.json`

## Limits

These results measure retrieval recall against three initial cases. Answer accuracy, grounding, and citation accuracy remain separate generation evaluations and are not inferred from retrieval recall. Before final presentation, rerun the evaluation against an expanded dataset containing expected answers and expected source pages; report routing, table-row retrieval, abstention, answer accuracy, and citation accuracy separately.
