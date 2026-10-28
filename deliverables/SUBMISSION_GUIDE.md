# Lead assessment submission checklist

Reconciled 2026-10-15 against local files and saved measurements.
This is not an assertion that all delivery checks have passed.

## Required assessment deliverables

| Deliverable | Evidence/location | Current status |
| --- | --- | --- |
| Working RAG application | `src/rag_system/`, `streamlit_app.py` | Implemented; fresh live smoke test pending |
| Source repository | [GitHub](https://github.com/sharanjaikumar11/financebench-grounded-rag) | Local changes not published in this phase; remote sync unverified |
| Architecture/data flow | [Architecture](../docs/architecture.md) | Reconciled; default and optional paths distinguished |
| Evaluation dataset | `evaluation/cases.json` | Original 11; 50-case draft separate |
| Evaluation results/failure analysis | [Experiment report](../docs/experiment-report.md) | Finalized; chunker generation, K retrieval, scorer correction and limitations |
| Chunking justification | [Sensitivity results](../docs/chunk-sensitivity-results.md) | Five settings completed on bounded 10-filing corpus; not full-corpus generation |
| Technical decisions | [Decisions](../docs/technical-decisions.md) | Updated to measured comparisons |
| Setup/configuration | [README](../README.md), [runbook](../docs/runbook.md) | Documented; clean-machine and container execution unverified |
| Tests/error handling | `tests/`, API/generation code | Latest suite: 138 passed, two upstream warnings; final release checks pending |
| Final presentation/demo | Intended `deliverables/FinanceBench_RAG_Interview_Review.pptx` | **Missing locally (Git deletion); must be supplied/refreshed before delivery** |

Docker/Compose files exist as preferred packaging; the engine was unavailable
during verification. Do not mark container execution complete.

## Separate optional enhancement attachment

Send [IMPROVEMENTS.md](../IMPROVEMENTS.md) separately. Hybrid search/reranking are
advanced options in the assessment, not mandates to enable every technique.
The 50-case expansion, particular accuracy targets, extra provider, PDF link
convenience and quality-tool choices must not be presented as additional client
requirements. Table indexing is stopped; the cross-encoder is disabled.

## Completed evidence checks

- [x] Compare both complete chunker indexes on the original 11 questions:
  retrieval K=3/5/10; live generation K=3.
- [x] Preserve original raw reports and disclose the numeric scoring correction.
- [x] Complete bounded 100/40,200/40,300/40,200/0,200/80 sensitivity.
- [x] Reconcile README, architecture, context and this checklist.
- [x] Separate required deliverables from optional improvements.

## Before sending

- [ ] Supply and verify the final presentation; do not link to a missing file.
- [ ] Smoke-test supported answer, abstention and browser PDF/page navigation.
- [ ] Verify clean setup and disclose the Docker execution limitation if unresolved.
- [ ] Final lint/format/tests, secrets and licensing review; exclude raw source and
  provider excerpts unless cleared. Review existing presentation deletion.
- [ ] Commit, push and verify the remote commit. Local documents are not proof of publication.
- [ ] Send repository URL plus verified commit, architecture, report, decisions,
  presentation and separate improvement summary.

## Reproduction pointers

Use the explicit measured settings and fresh-output commands in the
[experiment report](../docs/experiment-report.md).
The [sensitivity report](../docs/chunk-sensitivity-results.md) has the bounded
experiment command; no key is needed for retrieval-only runs.
Full comparison requires separately provisioned fixed-token and section-aware
indexes containing the same corpus. Generation requires a local provider key.

PDFs, vector stores and model weights are not part of a normal checkout.
Raw runs stay local under evaluation/results; published summaries retain their
own dates and scope. Do not claim 50-case answer/citation accuracy.
