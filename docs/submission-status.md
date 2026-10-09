# Assessment submission status

Audited against the lead's Production-Oriented RAG assessment on 2026-10-09.

## Available

- Modular PDF/TXT/Markdown ingestion, normalization, provenance and deduplication.
- Fixed-token and section-aware chunking; dense/hybrid retrieval and filing filters.
- Grounded generation, citations, abstention and basic API error handling.
- Evaluation cases, sanitized result summaries, architecture and technical decisions.
- Unit/integration tests, README, Docker artifacts and a presentation file.
- Optional reranker, evidence repair, statement/row ranking, Ruff and pre-commit.

## Still pending or requiring confirmation

1. Compare answer quality for both chunkers on the same expanded cases; the old
   three-case document-recall comparison is not enough. Test chunk-size sensitivity.
2. Repeat generation with recorded model/configuration settings and add held-out
   and unanswerable cases. No live generation run was performed in this doc pass.
3. Verify setup from a clean checkout and container model/index provisioning.
4. Review presentation contents against the latest numbers. File presence alone
   is verified; slides were not updated in this pass.
5. Confirm the reviewed commit is present on the submission remote before sharing.
   Resume scripts/output and temporary artifacts are excluded from the project.

Do not claim authentication, durable background jobs, cloud deployment, full
semantic grounding verification or completed table-aware indexing. These are
extensions rather than minimum assessment requirements.
