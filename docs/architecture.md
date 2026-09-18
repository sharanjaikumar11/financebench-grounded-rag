# Architecture

```text
Supported documents → cleaning/parsing → duplicate registry → chunking
→ local Sentence Transformer embeddings → SQLite vectors + FTS5
→ dense or hybrid retrieval → Gemini grounded answer → citations
```

PDF pages and Markdown sections remain attached to every chunk. The SQLite store keeps the chunk text, vector, document name/ID, pages, sections, and chunking strategy. A query with an explicit company and fiscal year is constrained to the matching filing; otherwise retrieval searches the configured corpus. Hybrid retrieval fuses cosine-similarity ranking with SQLite FTS5 keyword ranking.

The FastAPI layer exposes indexing and querying while the evaluation runner measures retrieval separately from answer accuracy, grounding, and citation correctness.
