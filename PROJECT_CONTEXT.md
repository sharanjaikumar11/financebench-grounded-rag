# FinanceBench Grounded RAG — Project Context

Reconciled 2026-10-15 against local code and saved evaluation artifacts.
This is a local handoff, not proof of GitHub synchronization or production readiness.

## Scope and source of truth

Workspace: `C:\Users\shara\Projects\production-rag-system`.
Repository: https://github.com/sharanjaikumar11/financebench-grounded-rag.
The lead's assessment is mapped in [submission status](docs/submission-status.md).
[Experiment report](docs/experiment-report.md) is the authoritative current
evaluation narrative; [submission guide](deliverables/SUBMISSION_GUIDE.md) is the
delivery checklist. [IMPROVEMENTS.md](IMPROVEMENTS.md) separates optional work.

Do not modify MultiPDF-Hybrid-RAG, restart stopped table indexing, inject expected
answers/pages into retrieval, or overwrite measured reports. Preserve unrelated
working-tree changes. The presentation is currently **missing**, shown as deleted
by Git; it was not restored or deleted by this documentation pass.

## Architecture

PDF/TXT/Markdown → content hash/duplicate check → parsing and normalization →
fixed-token or section-aware chunks with provenance → local MiniLM embeddings →
SQLite vectors and FTS5.

Streamlit and FastAPI independently call RAGQueryService → inferred company/year/
quarter filters → dense + lexical hybrid retrieval → generic relevance ranking →
K anchors and adjacent chunks → maximum nine selected generation chunks →
Gemini (or optional Groq) → citations/evidence checks → answer or abstention.
Provider errors are distinct from insufficient context.

The API uses K=3 and FixedTokenChunker(200,40). Counts are whitespace tokens.
Plain text is the default generation protocol; the measured profile explicitly
enables evidence mode and statement ranking. Neither is silently a new default.
See [architecture](docs/architecture.md) for the diagram and settings.

## Completed work

- PDF/TXT/Markdown ingestion, normalization, provenance, duplicate registry,
  batched indexing and incomplete-index recovery.
- Fixed-token and section-aware chunkers; local all-MiniLM-L6-v2 embeddings;
  SQLite dense scoring and FTS5/BM25 rank fusion.
- Indexed fiscal-year/quarter/company routing, generic aliases, adjacent context,
  optional statement/row and financial-concept relevance preferences.
- Gemini and optional Groq generation; capacity fallback, citation validation,
  opt-in structured evidence and one repair attempt.
- FastAPI health/index/query endpoints and local Streamlit demo; literal-dollar
  rendering and loopback PDF/page links.
- Evaluation metrics, diagnostics, provenance, draft scoring guards, source-page
  audit, controlled chunker/K comparison and bounded size/overlap experiment.
- Tests, Ruff/pre-commit configuration and lint/format CI. CI does not run pytest.
- Docker/Compose scaffolding; container execution is not verified.

## Verified results and profiles

| Experiment | Scope/settings | Result |
| --- | --- | --- |
| Current fixed-token generation | Original 11; K=3; evidence mode, statement ranking on; concept ranking and cross-encoder off | Answer 9/11, citation 9/11 (81.82% each); filing 11/11; page 10/10; abstentions 2/11 |
| Section-aware generation | Same 11, corpus and settings | Answer 7/11 after scoring correction; citation 7/11 (63.64%); page 9/10; abstentions 4/11 |
| Chunker/K retrieval | Same 363 filings; K=3/5/10 | Fixed full-page recall 10/10 at all K; section 9/10,9/10,10/10; selected-context coverage can fall to 9/10 |
| Size/overlap sensitivity | Same 11; 10 complete expected filings; five isolated fixed-token indexes; K=3 | 200/40,300/40,200/80: 10/10 selected-page hits; 100/40,200/0: 8/10 |
| Optional 50-case draft retrieval | K=5; statement and financial-intent ranking on; no cross-encoder | Filing 50/50; full pages 45/49 (91.84%); selected pages 40/49 (81.63%) |

Section-aware raw generation recorded 6/11 answers. Generic parsing of currency
after amounts/plural units corrected one false negative to 7/11 under unchanged
numeric tolerance. Original reports remain untouched. This is evaluator repair,
not an LLM gain. The 50-case draft has **no generation accuracy result**.

100% grounding is document-membership checking with abstentions accepted, not
claim entailment. Citation accuracy is document/page overlap. Answer matching is
numeric tolerance, yes/no prefixes or substring matching. Eleven reused cases
are not held-out production evidence. Full limitations and hashes are in the report.

## Data and artifacts

- Complete fixed index: `data/processed/local_sentence_transformers/vectors.sqlite3`;
  363 documents, 171,852 chunks (previous read-only inspection).
- Complete section index: `data/processed/local_sentence_transformers_section_aware/vectors.sqlite3`;
  same 363 documents, 185,925 chunks.
- Local PDFs: `data/raw/financebench/pdfs/`; original cases:
  `evaluation/cases.json` (11). Expanded draft: `evaluation/drafts/cases_50.json`.
- Current raw runs: `evaluation/results/submission_20261015_generation/`,
  `submission_20261015_retrieval/`, `chunk_sensitivity_20261015/`.
- Reviewable chunk sensitivity manifest: `evaluation/published/chunk_sensitivity_20261015.json`.
- Raw source text, indexes, model weights and secrets are excluded from Git.
  Historical published summaries are not automatically updated by new runs.
- Draft excerpt/page matches do not validate all reference answers or rubrics;
  attribution/redistribution review is required before publishing copied records.

## File map

| Files | Responsibility |
| --- | --- |
| `src/rag_system/main.py`, `config.py`, `api/`, `services/` | Composition, environment settings, API and shared workflow |
| `ingestion/`, `chunking/strategies.py` under `src/rag_system/` | Parsing, registry and two main chunkers |
| `src/rag_system/retrieval/` | Embeddings, routing, SQLite/FTS5, ranking |
| `src/rag_system/generation/` | Providers, prompts, citations and evidence validation |
| `src/rag_system/evaluation/` | Cases, metrics, execution and provenance |
| `streamlit_app.py` | Local UI and PDF source links |
| `scripts/index_documents.py` | Index provisioning |
| `scripts/run_generation_evaluation.py` | Live scored generation |
| `scripts/run_submission_comparison.py` | Complete-index chunker and K comparisons |
| `scripts/run_chunk_sensitivity.py` | Bounded size/overlap experiment |
| `scripts/prepare_expanded_evaluation.py`, `audit_expanded_evaluation.py`, `run_audited_retrieval.py` | Optional draft selection/audit/retrieval |
| `tests/`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/quality.yml` | Tests, dependencies and quality checks |
| `docs/`, `deliverables/SUBMISSION_GUIDE.md`, `IMPROVEMENTS.md` | Required evidence and separately labelled enhancements |

## Dependencies and configuration

Python 3.12; FastAPI, Uvicorn, PyMuPDF, Sentence Transformers, Streamlit,
google-genai; optional Groq. Development tools: pytest/httpx, Ruff and pre-commit.
Exact declared version ranges are in pyproject.toml; dependencies are not locked.
Model weights must be cached; embedding model loading is local-only.
YAML descriptors are not a fully wired runtime configuration system.

Measured profile: ANSWER_PROVIDER=gemini, GEMINI_MODEL=gemini-3.1-flash-lite,
GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite, GEMINI_THINKING_LEVEL=minimal,
GROUNDED_OUTPUT_MODE=evidence, STATEMENT_AWARE_RANKING=1,
FINANCIAL_INTENT_RANKING=0, RERANKER_MODEL empty. These are recorded aliases,
not actual provider revision/fallback telemetry. Keys belong only in local
environment/secret storage; another terminal's key is not automatically inherited.

## Failures addressed and unresolved limits

- Wrong filings: generic metadata/short fiscal-year/quarter normalization and
  eligible-filing routing; ambiguous questions remain a risk.
- Split headers/rows: neighbor context and row heuristics, not complete tables.
- Non-verbatim quotes: strict matching plus one repair; invalid evidence abstains.
- Currency formatting false negative: numeric evaluator now recognizes USD
  placement and plural units, without changing tolerance or references.
- PDF file/static route failures: loopback HTTP PDF delivery. Fresh browser
  validation is still pending.
- Capacity errors: bounded provider fallback; access/errors remain explicit.
- Windows test-folder permissions: approved test execution or fresh scoped temp
  directories, not blanket deletion.

Fixed-token remaining cases: 3M capital-intensity model abstention and JPMorgan
quote validation failure. Section-aware additionally misses Verizon's page and
fails Costco quote validation. See the report for exact IDs and diagnostics.

## Validation and remaining work

Latest executable validation: **138 passed**, two upstream Starlette/httpx/AnyIO
warnings. Ruff passed for the new sensitivity runner/tests; report hashes checked.
Documentation edits do not constitute another live provider/browser test.

Required submission closure:
1. Supply/refresh the missing presentation with current measurements.
2. Fresh application smoke test: supported question, abstention and PDF page link.
3. Clean-checkout setup verification; Docker execution remains unverified because
   the local engine was unavailable. Docker is preferred packaging, not proof of
   deployment.
4. Review secrets, licensing and diffs; final quality checks, commit/push and
   remote commit verification. No publication was performed in this doc pass.

Optional next work: review 50-case references/rubrics before generation, held-out
and unanswerable sets, repeat runs, semantic grounding, latency/cost testing,
versioned indexes/model telemetry and better context retention. Authentication,
ACLs, durable jobs, ANN scale-out, monitoring and remote PDF serving are production
extensions, not current features. Do not expose the unauthenticated server-local
/index source_path API publicly.

## Continuation rules

Read Git status before edits; the tree contains existing local work and a deleted
presentation. Do not assume GitHub matches the workspace. Keep old result files,
separate scoring corrections from system improvements, and consult README for
setup/reproduction rather than duplicating commands here.

## Latest optional improvement checkpoint: 2026-10-26

See `docs/pending-issue-audit-20261026.md` for the current audit of nine abstentions
and eight answered citation-location failures. Source repair, generic financial
aliases, opt-in `OPERAND_COVERAGE`, main-statement row selection, adjacent context
retention and per-filing acquisition evidence fixes are implemented. The final
acquisition check retains all three AMCOR event descriptions and preserves Best
Buy's labelled evidence, within nine generation sources. 238 unit tests and Ruff
pass. No full generation run or publication was performed during these fixes.

The latest live baseline remains `generation_50_period_validation.json`: 41 answers,
nine abstentions, 33/50 strict citation-location matches, answer accuracy null.
Do not substitute offline retrieval coverage for answer accuracy. Next work is
targeted live generation and explicit rubric decisions for capital intensity,
AES income basis/inventory denominator, and incomplete multi-year acquisition
references before another full generation evaluation. Keep improvements separate
from the lead-required submission and preserve original benchmark labels.

Targeted live follow-up completed: `generation_targeted_repairs.json` contains ten
cases (nine prior abstentions plus Best Buy), four answers and six abstentions,
with 4/10 strict citation-location matches. This is not a new full-set score.
Kraft Heinz now correctly returns 6.25; AES ROA remains a reference-basis mismatch,
and AMCOR answers only the supported FY2023 portion. Signed-operand, formula and
source-assignment errors remain. See `docs/targeted-generation-results-20261026.md`.
Do not rerun all 50 until targeted generation reliability is addressed.

Latest follow-up: targeted v2 returned eight answers, two abstentions and 8/10
citation-location matches. `FINANCIAL_DECIMAL_INPUT=1` now parses strict comma and
parenthesis numeric notation; offline replay recovers Activision at 1.9%, leaving
3M as the only validation abstention. No new full-set or semantic score is claimed.
261 unit tests pass. See `docs/targeted-v2-review-and-decimal-input.md` for remaining
AES basis/denominator issues, AMCOR partial coverage and Best Buy absence claims.

Next checkpoint: opt-in `ABSENCE_VALIDATION` now rejects recognized categorical
acquisition-absence claims without explicit dated supporting quotes. Offline v2
replay with decimal parsing retains Activision but rejects Best Buy's unsupported
absence claims (eight cases accepted, not eight adjudicated correct). 268 unit
tests pass. The targeted launcher enables the new flag; v3 preflight passed.
See `docs/acquisition-absence-validation.md`. No full evaluation was run.

28 October checkpoint: v3 returned three answers, six abstentions and one provider
error (see `docs/targeted-v3-review.md`). Local fixes now accept bounded mixed-case
calculation names, increase structured output to 4096 tokens and record safe
provider diagnostics. All 282 unit tests and changed-file Ruff checks pass.
Offline v3 replay recovers Adobe and Kraft (five accepted cases, not measured
accuracy); v2 replay under its original flags retains its eight accepted cases.
No live evaluation was launched. See `docs/targeted-local-fixes-20261028.md`.

Targeted v4 subsequently completed: eight answers, two abstentions, no provider
errors and 8/10 citation-location matches; answer accuracy remains unreviewed.
Generic evidence-link repair now reports verified candidate quote indices and
clarifies ratio units/denominator conventions. 283 unit tests and Ruff pass;
offline hints locate the three mislinked capex operands. No live test of these
latest prompts yet. See `docs/evidence-link-repair-20261028.md` and
`docs/targeted-v4-review.md`. AES definition ambiguity and 3M abstention remain.

Full run `generation_50_20261028_130232.json`: 46 answers, four abstentions, no
provider errors, 35/50 citation-location matches, 50/50 filing hits and 47/49
labelled-page hits. Answer accuracy remains unreviewed. Generic direction checking
now rejects Verizon's numerically contradictory increase claim; offline replay
retains 45 other answers. Repair format/header guidance strengthened. 290 unit
tests and Ruff pass; no live run after these changes. See
`docs/full-run-validation-fixes-20261028.md` for scope and remaining issues.

Documentation reconciled 28 October through latest full run and agent answer
review: README, architecture, technical decisions, experiment report and failure
analysis now describe one current project, with old experiments labelled historical
(user requested no lead-versus-extension separation). Review: 42/50 supported,
six unsuccessful, two AES definition decisions open; final accuracy unset.
Demo AppTest startup, missing-key handling, saved-answer rendering and actual PDF
HTTP delivery pass outside the socket-restricted sandbox; 290 unit tests pass.
Fresh live demo generation and visual PDF page navigation were not tested.
See `docs/demo-verification-20261028.md`. No new generation or Git push performed.
