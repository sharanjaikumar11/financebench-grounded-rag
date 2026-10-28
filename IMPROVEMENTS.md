# Improvements beyond the core assessment

Updated 2026-10-15. These extend the required application; they do not imply
production readiness or completion of every experiment.

The assessment requests some advanced exploration, not every technique below.
These are implementation choices beyond the core deliverables; a 50-case set,
specific accuracy target, Groq support and Ruff are not additional client mandates.
Required deliverables are mapped in [submission status](docs/submission-status.md).

| Improvement | Purpose | Status |
| --- | --- | --- |
| Dense + FTS5/BM25 search | Semantic and exact financial-term retrieval | Implemented |
| Company/year/quarter routing | Reduce wrong-filing retrieval | Implemented |
| Aliases, statement/row scoring | Locate relevant financial evidence | Statement ranking opt-in |
| Financial-concept ranking and filing diversity | Improve evidence selection across eligible filings | Experimental, opt-in |
| Adjacent context | Recover nearby headers and split rows | Implemented, not complete-table extraction |
| Structured quotes and bounded repair | Validate source IDs and verbatim excerpts | Opt-in, not entailment verification |
| Clickable PDF/page sources | Allow local inspection of evidence | Loopback server, not remote deployment |
| Provider fallback and Groq adapter | Availability handling and provider experiments | Implemented; access must be verified |
| Evaluation provenance and draft guards | Reproducibility and honest scoring | Implemented |
| Ruff and pre-commit | Code consistency | Configured |

## Measured results

- Current controlled 11-case generation: fixed-token answer/citation 9/11
  (81.82%); section-aware 7/11 (63.64%) after a disclosed scorer correction.
  These development results do not establish a gain for every optional feature.
- Required comparison work is complete: chunker generation at K=3, retrieval at
  K=3/5/10, and bounded size/overlap sensitivity. See the
  [report](docs/experiment-report.md) and [sensitivity results](docs/chunk-sensitivity-results.md).
- Unchanged 50-case draft retrieval: filing recall 43/50 to 50/50; labelled-page
  recall 26/49 to 45/49 (91.84%). The final profile uses five anchors instead of
  three, with optional ranking. This does not isolate each change's contribution.
- Nine-chunk generation context retains 40/49 page hits (81.63%). No 50-case
  answer/citation accuracy has been measured. Reference/rubric review is pending.
- Details: `docs/retrieval-improvement-results.md`, `evaluation/published/`.

## Not active in the main demo

Cross-encoder reranking remains disabled after worse audited page recall.
Table-aware corpus indexing was stopped and remains incomplete. No agentic layer,
fine-tuning, authentication, cloud deployment or durable job queue is claimed.

## Remaining work

Citation-failure audit: all 16 failures are classified; nine answered failures
have quotes located in the cited PDFs, but semantic/alternative-reference review
remains pending. An opt-in verbatim-source repair experiment is implemented with
unchanged validation. No new live accuracy score is claimed; see
[citation failure audit](docs/citation-failure-audit.md).

Expanded reference review has started: a 50-entry non-scoring ledger and
[rubric findings](docs/expanded-rubric-review.md) now record duplicate questions,
ambiguous ratio/percentage definitions and incomplete multi-year references.
No cases were promoted or removed. Full source/calculation review and versioned
rubric implementation remain pending before live generation.

Numeric rubric v1 is now implemented separately with signed values, explicit
units/rounding and blocked/review outcomes (160 tests pass overall). It is not
connected to live scoring: full reference review, narrative/list grading and
versioned runner integration still remain. Historical scores are unchanged.

The collection/review integration is now available: see
[50-case workflow](docs/run-50-case-review.md). All 50 responses can be collected
and later adjudicated with hash-bound review records and fixed denominators.
Reference and actual answer reviews are still pending; no live 50-case score
has been produced. Narrative/list grading is explicit reviewer adjudication,
not automated entailment or substring matching.

Update 2026-10-25: opt-in bounded-context diversity now recovers all five page
hits previously dropped from the saved K=5 retrieval context: **40/49 to 45/49**,
with no page-hit regressions and the same nine-chunk cap. Original-11 coverage is
preserved. This is retrieval replay, not a new answer/citation score. See
[context retention improvement](docs/context-retention-improvement.md).
Default context selection remains unchanged pending live validation.

Optional follow-up: expanded rubric review before any 50-case generation score,
held-out/unanswerable evaluations, repeated runs and bounded-context retention.
Submission closure (presentation, demo/setup checks and publication) is tracked
separately in the [delivery checklist](deliverables/SUBMISSION_GUIDE.md).

Update 2026-10-26: [period validation and source repair](docs/period-validation-and-source-repair.md)
adds exact-source repair hints and opt-in dated-heading conflict checks. Offline
replay rejects one confirmed wrong-period calculation; 41 other saved answers
remain accepted. This is not a new live accuracy score. 229 unit tests pass.

The subsequent [live period-validation comparison](docs/period-validation-live-results.md)
completed all 50 cases: 41 answers, nine abstentions, and 33/50 strict citation
location matches. The one lost match is the correctly blocked wrong-year answer.
Adobe's source-assignment failure remains; reviewed answer accuracy is pending.

[Source-window repair](docs/source-window-repair.md) now repeats actual matching
sources first, within a bounded copy-check section. Offline inspection covered
all seven saved quote failures; 231 unit tests pass. Live recovery is unmeasured.

[Pre-generation issue audit](docs/pending-issue-audit-20261026.md) covers all nine
abstentions and eight answered citation-location failures. Generic operand and
statement-context selection, transaction fallback and prompt consistency fixes
are implemented. 238 unit tests pass. Offline results and unresolved rubric/model
validation limits are recorded separately; no new generation accuracy is claimed.

[Structured repair diagnostics](docs/structured-repair-diagnostics.md) now identify
specific signed-operand, decimal, name and formula errors together. Saved-response
replay preserves all validation decisions; 245 unit tests pass. Targeted live
verification is required before claiming recovery or running the full evaluation.

[Targeted v2 review](docs/targeted-v2-review-and-decimal-input.md): live subset has
eight answers and 8/10 citation-location matches. Opt-in financial decimal parsing
accepts Activision's already-saved repaired formula offline (1.9%), while retaining
sign and quote checks. 261 tests pass. AES definitions and acquisition completeness
remain unresolved; nine accepted replay cases do not mean 90% answer accuracy.

[Acquisition absence validation](docs/acquisition-absence-validation.md) rejects
recognized unsupported no-acquisition claims rather than treating zero cash flow
as proof. Replay blocks Best Buy's unsupported claims while retaining Activision;
268 unit tests pass. Semantic completeness and ambiguous definitions remain open.

[Targeted local fixes](docs/targeted-local-fixes-20261028.md): safe mixed-case
calculation names, a larger bounded structured-output budget and safe provider
diagnostics. 282 unit tests pass. Offline v3 replay recovers two responses;
this is validator coverage, not new answer/citation accuracy.
