# Assessment submission status

Reconciled 2026-10-15 using the previously reviewed lead assessment and current
local evidence. The external assignment was not re-fetched during this
documentation-only reconciliation.

## Required scope and evidence

The assessment calls for ingestion/provenance, at least two chunking strategies
and comparisons, embedding/retrieval experiments, grounded cited answers and
abstention, a small evaluation with failure analysis, modular service/API,
configuration/errors/tests, setup instructions, architecture/decisions, and a
presentation/demo. Docker is preferred. Advanced techniques are choices, not a
requirement to implement every listed technique.

| Area | Status |
| --- | --- |
| PDF/TXT/Markdown ingestion, cleaning, provenance, deduplication | Implemented |
| Fixed-token and section-aware comparison | Complete on unchanged 11 cases: retrieval K=3/5/10 and generation K=3 |
| Chunk-size/overlap sensitivity | Complete bounded 10-filing, five-setting retrieval comparison |
| Embeddings, retrieval, metadata and top-K experiments | Implemented and measured; see experiment report |
| Grounded generation, citations, abstention/errors | Implemented; semantic entailment is not guaranteed |
| Dataset, metrics and failure report | Original 11 reviewed cases; current report reconciled |
| API, tests and setup documentation | Implemented; latest suite 138 passed; fresh setup/demo verification pending |
| Architecture and decisions | Reconciled to current implementation and results |
| Presentation | Missing locally: Git shows deleted PPTX; final presentation still required |
| Repository publication | Local changes pending; remote synchronization not verified |
| Docker packaging | Files present; execution unverified, local engine unavailable |

See the [delivery checklist](../deliverables/SUBMISSION_GUIDE.md),
[experiment report](experiment-report.md), and
[bounded sensitivity results](chunk-sensitivity-results.md).

## Optional work kept separate

[IMPROVEMENTS.md](../IMPROVEMENTS.md) lists implementation choices/enhancements:
hybrid search, generic routing/ranking, structured evidence repair, PDF links,
provider alternatives, provenance and Ruff tooling. Some satisfy the assessment's
advanced-exploration component; none imply every advanced option was required.

The 50-case draft, specific recall targets, held-out expansion and production
scale-out are not minimum delivery requirements. Its best retrieval diagnostic
is 50/50 filing hits, 45/49 full-context page hits, 40/49 selected-context page
hits at K=5 with optional concept ranking. No 50-case generation score is claimed.

## Remaining delivery checks

Supply/refresh the missing presentation; verify startup, abstention and PDF page
navigation; clean-checkout setup; final quality/security/licensing review; commit,
push and remote verification. Do not claim cloud deployment, authentication,
durable indexing jobs, complete table-aware indexing or perfect factual grounding.
