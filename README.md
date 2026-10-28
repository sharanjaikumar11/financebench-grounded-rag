# FinanceBench Grounded RAG

## Current project status — 28 October 2026

An internship assessment project with local hybrid retrieval, cited generation,
financial evidence validation, a Streamlit demo and FastAPI interface. This is
not a claim of production readiness. All implemented work is documented together.

Latest full run: `evaluation/results/generation_50_20261028_142603.json`.
Raw run files are local and Git-ignored. The
[published summary](evaluation/published/full_50_review_20261028.json) includes
metrics, review decisions and the collection hash without raw provider outputs.

| Measure | Result |
| --- | ---: |
| Completed / provider errors | 50/50 / 0 |
| Answers / abstentions | 45 / 5 |
| Expected-filing recall | 50/50 (100%) |
| Labelled-page recall | 47/49 (95.92%) |
| Strict citation-location matches | 36/50 (72%) |
| Agent-reviewed source-supported answers | 42/50 (84%) |
| Incorrect or abstained / unresolved | 6 / 2 |

Final answer accuracy is **not settled**: two AES definition cases remain open.
The review range is 84–88%, not a claimed 88%. This is a tuned development set;
quote membership and page overlap do not establish semantic correctness.
See [current evaluation](docs/experiment-report.md),
[answer review](docs/answer-review-20261028.md) and
[failure analysis](docs/failure-analysis.md).

The 50-case collector uses five retrieval anchors and the validation flags recorded
in its run metadata. The Streamlit demo still uses three anchors by default;
do not present demo behavior as an exact reproduction of the 50-case profile.

To collect a fresh full run (only when needed, with the Gemini key configured):

```powershell
.\scripts\run_targeted_generation.ps1 -FullSet
```

The launcher creates a timestamped file and restores environment settings after
completion. Collection computes citation-location scores; answer review is separate.

Grounded retrieval-augmented generation over FinanceBench filings. The system ingests PDF, TXT, and Markdown sources, preserves source provenance, retrieves locally with Sentence Transformer embeddings, and produces source-cited answers using Gemini or Groq.

## Submission overview

Historical submission reconciled 2026-10-15. This is an assessment project, not a
production-readiness claim. Required deliverables and outstanding release checks
are mapped in the [submission guide](deliverables/SUBMISSION_GUIDE.md).

- [Architecture](docs/architecture.md), [technical decisions](docs/technical-decisions.md)
- [Evaluation report](docs/experiment-report.md), [chunk sensitivity](docs/chunk-sensitivity-results.md)
- [Project context](PROJECT_CONTEXT.md), [assessment status](docs/submission-status.md)
- [Implementation history](IMPROVEMENTS.md)

The final presentation is currently missing locally (Git records a deletion).
Demo startup, missing-key handling, saved-answer rendering and PDF HTTP links
were checked on 28 October; see [demo verification](docs/demo-verification-20261028.md).
Fresh live generation in the demo, fresh-machine setup and remote publication
verification remain pending.

## Setup

Requires Python 3.12. On a fresh Windows checkout, first run `py -3.12 -m venv .venv`.
The repository does not include the source PDFs, vector databases or model cache.

```powershell
cd C:\Users\shara\Projects\production-rag-system
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Set the key only in the terminal session that will run answer generation:

```powershell
$env:GEMINI_API_KEY = "your_key"
$env:ANSWER_PROVIDER = "gemini"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
```

Or use Groq for answer generation (retrieval remains local):

```powershell
$env:ANSWER_PROVIDER = "groq"
$env:GROQ_API_KEY = "your_key"
$env:GROQ_MODEL = "openai/gpt-oss-20b"
```

## Run

### First-time model cache and indexing

Download the embedding model once with network access; subsequent application
loads are local-only:

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
python scripts/index_documents.py data/raw/financebench/pdfs --strategy fixed_token --chunk-size 200 --overlap 40 --storage-directory data/processed/local_sentence_transformers
```

Supply your authorized FinanceBench PDFs in that directory first. TXT and Markdown
are also supported. Keep alternative chunking indexes in separate directories.
The 200/40 counts are whitespace-delimited tokens, not model-token counts.
Fresh-machine installation and Docker execution have not been revalidated in this
documentation pass. Containers also need the model cache and an index; the Docker
files alone do not provision them.

Start the API after the local fixed-token index is built:

```powershell
uvicorn rag_system.main:app --host 0.0.0.0 --port 8000
```

Endpoints: `GET /health`, `POST /index`, and `POST /query`.

For local review prefer `--host 127.0.0.1`. The API has no authentication;
`/index` accepts a server-local source path, not a browser upload. Do not expose
it publicly as-is.

## Lead demo

For the current validation features, set the following before starting Streamlit.
The demo still retrieves three anchors; the 50-case collector uses five.

```powershell
$env:GROUNDED_OUTPUT_MODE = "evidence"
$env:STATEMENT_AWARE_RANKING = "1"
$env:FINANCIAL_INTENT_RANKING = "1"
$env:CONTEXT_DIVERSITY_RANKING = "1"
$env:CALCULATION_VALIDATION = "1"
$env:COMPARISON_VALIDATION = "1"
$env:METRIC_IDENTITY_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
$env:NUMERIC_ROW_COVERAGE = "1"
$env:PERIOD_VALIDATION = "1"
$env:OPERAND_COVERAGE = "1"
$env:FINANCIAL_DECIMAL_INPUT = "1"
$env:ABSENCE_VALIDATION = "1"
$env:RERANKER_MODEL = ""
python -m streamlit run streamlit_app.py
```

The following older settings reproduce the historical 11-case profile instead;
do not run both configuration blocks sequentially expecting the current profile.

With the selected provider's API key set in the terminal, run the Streamlit demo:

To match the measured 11-case profile, set these optional features explicitly
before launching (plain-text generation and disabled statement ranking remain
the application defaults):

```powershell
$env:GROUNDED_OUTPUT_MODE = "evidence"
$env:STATEMENT_AWARE_RANKING = "1"
$env:FINANCIAL_INTENT_RANKING = "0"
$env:RERANKER_MODEL = ""
```

```powershell
streamlit run streamlit_app.py
```

The browser opens at `http://localhost:8501` and shows grounded answers, source citations, and safe insufficient-context responses. When the cited FinanceBench PDF is available under `data/raw/financebench/pdfs/`, the application automatically starts a loopback-only PDF source server on port `8502`. Each source link then opens the browser-served PDF at its first cited page. Set `FINANCEBENCH_PDF_SERVER_PORT` before starting Streamlit only if port `8502` is occupied. The application uses `GEMINI_FALLBACK_MODEL` only when the primary Gemini model returns a temporary capacity error; otherwise, generation failures are reported clearly.

## Evaluation

Historical controlled 11-case generation comparison: fixed-token K=3 achieved
**81.82% answer and citation accuracy**; section-aware K=3 achieved **63.64% for
both after a disclosed numeric scoring correction** (raw answer score 54.55%).
The [experiment report](docs/experiment-report.md) records settings, hashes,
failure diagnostics and metric limitations. Historical [summaries](evaluation/published/)
retain their original scopes. These are development results, not production accuracy.

The [bounded sensitivity experiment](docs/chunk-sensitivity-results.md) supports
200/40: 10/10 selected-context page hits versus 8/10 for 100/40 and 200/0,
matching 300/40 with less context and 200/80 with fewer chunks. It uses 10 complete
filings, not the entire corpus, and does not measure answer accuracy.

The expanded 50-case collection and agent review are now complete, with two
definition decisions unresolved. Grounding membership and page overlap are not
semantic entailment. To reproduce the older 11-case profile:

```powershell
$env:GROUNDED_OUTPUT_MODE = "evidence"
$env:STATEMENT_AWARE_RANKING = "1"
$env:FINANCIAL_INTENT_RANKING = "0"
$env:RERANKER_MODEL = ""
python scripts/run_generation_evaluation.py --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --include-provider-output --output evaluation/results/review_generation.json
```

Keep the model settings fixed and preserve previous reports. The command requires
the provider key in the same terminal. Raw outputs may contain document excerpts;
do not publish them without review. Export a safe summary with
`python scripts/export_evaluation_summary.py evaluation/results/review_generation.json --output evaluation/published/review_generation.json`.

For the authoritative full-context chunker/K comparison, use
`scripts/run_submission_comparison.py` with the commands and prerequisites in
the [experiment report](docs/experiment-report.md). For bounded size/overlap
reproduction, use `scripts/run_chunk_sensitivity.py` as documented in its report.
Both refuse to overwrite existing output directories.

Legacy retrieval-only experiment (this runner trims expanded context to K; its
page coverage is not directly comparable to full-context generation evaluation):

```powershell
python scripts\run_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --chunking-strategy fixed_token --top-k 3 --retrieval-mode hybrid --apply-query-metadata-filter --output evaluation\results\fixed_token_hybrid_top_k_3_metadata_filtered.json
```

Run grounded answer evaluation with the key available in the same terminal:

```powershell
python scripts\run_generation_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --output evaluation\results\generation_evaluation.json
```

## Tests

Latest executed suite: **138 passed**, two upstream deprecation warnings. This
does not substitute for a fresh live demo test. GitHub Actions currently runs
Ruff lint/format, not pytest.

See [the development runbook](docs/runbook.md) for Ruff pre-commit setup,
CI checks, and interpreting page-level evaluation diagnostics.

```powershell
python -m pytest -q --basetemp .pytest-tmp
```

## Container

Docker/Compose artifacts are provided, but container execution remains unverified:
the local Docker engine was unavailable. Provision the source/model/index first.

```powershell
docker compose up --build
```
