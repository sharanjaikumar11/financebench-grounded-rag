# Retrieval experiment report

## Scope

This report evaluates the three committed FinanceBench cases against the complete local corpus of 363 unique documents. Both configurations use the `all-MiniLM-L6-v2` local embedding model, cosine similarity, and the same inferred filing metadata filter when the question explicitly states a company and fiscal year.

The metadata filter is part of the evaluated configuration because the baseline dense-only system retrieved similar filings from incorrect years. The filter restricts those unambiguous queries to the matching filing before ranking chunks.

## Results

| Chunking strategy | K=3 recall | K=5 recall | K=10 recall |
| --- | ---: | ---: | ---: |
| Fixed-token (200 tokens, 40 overlap) | 100% (3/3) | 100% (3/3) | 100% (3/3) |
| Section-aware (200 tokens, 40 overlap) | 100% (3/3) | 100% (3/3) | 100% (3/3) |

Both strategies retrieved the expected filing for every evaluation case at K=3. Increasing K did not improve document-level recall on this small evaluation set.

## Baseline comparison

The unfiltered fixed-token dense baseline achieved 33.3% recall@10 (1/3). Metadata-aware retrieval increased recall@10 to 100% (3/3) by preventing wrong-year filings from competing with the explicitly requested filing.

## Artifacts

The machine-readable reports are generated locally under `evaluation/results/`:

- `fixed_token_top_k_3_metadata_filtered.json`
- `fixed_token_top_k_5_metadata_filtered.json`
- `fixed_token_top_k_10_metadata_filtered.json`
- `section_aware_top_k_3_metadata_filtered.json`
- `section_aware_top_k_5_metadata_filtered.json`
- `section_aware_top_k_10_metadata_filtered.json`

## Limits

These results measure retrieval recall against three cases. Answer accuracy, grounding, and citation accuracy remain separate generation evaluations and are not inferred from retrieval recall.
