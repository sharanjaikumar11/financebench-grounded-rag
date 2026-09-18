# Technical decisions

## Embeddings

`all-MiniLM-L6-v2` is used locally for embeddings. It removes embedding API rate limits during corpus indexing and produces 384-dimensional vectors. Gemini remains restricted to grounded answer generation.

## Vector store

SQLite stores vectors and provenance locally. SQLite FTS5 provides keyword candidates for hybrid retrieval. This keeps the supplied FinanceBench corpus reproducible without hosted vector infrastructure.

## Chunking

Both fixed-token (200 tokens, 40 overlap) and page/section-aware strategies were indexed separately. Both retrieved all three evaluated expected filings at K=3, K=5, and K=10 after filing metadata filtering. Fixed-token is the API default because it provides a stable overlapping context window; section-aware remains available for comparison.

## Grounding

The generation prompt restricts answers to retrieved sources, requires citation labels, and returns `INSUFFICIENT_CONTEXT` if evidence is absent or citations are invalid.

## Retrieval improvements

Dense-only fixed-token retrieval scored 33.3% recall@10 on the three FinanceBench cases because similar filings from incorrect years ranked highly. Exact filing metadata filtering increased recall@10 to 100%. Hybrid retrieval is implemented and uses reciprocal-rank fusion of dense and FTS5 results.
