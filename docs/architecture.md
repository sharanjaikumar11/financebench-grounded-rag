# Architecture

```text
Supported documents → cleaning/parsing → duplicate registry → chunking
→ local-only Sentence Transformer embeddings → SQLite vectors + FTS5
→ filing routing → dense + BM25 hybrid retrieval → financial relevance scoring
→ optional statement/row scoring or cross-encoder → anchors + adjacent context
→ Gemini/Groq → optional structured quote validation + bounded repair
→ grounded answer with page-linked citations OR insufficient context
```

PDF pages and Markdown sections remain attached to every chunk. The SQLite store keeps the chunk text, vector, document name/ID, pages, sections, and chunking strategy. A query with an explicit company and fiscal year is constrained to the matching filing; a stated quarter selects the matching 10-Q, while an annual request prefers a 10-K. Otherwise retrieval searches the configured corpus. Hybrid retrieval fuses cosine-similarity ranking with SQLite FTS5 keyword ranking, then applies generic financial-table relevance scoring before context expansion.

The FastAPI layer exposes indexing and querying while the evaluation runner measures retrieval separately from answer accuracy, grounding, and citation correctness.
