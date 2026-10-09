# Development checks and evidence evaluation

## Improvements without reindexing

Table-aware indexing is stopped. Continue using the complete original index.
Generation now assembles selected chunks with available immediate neighbors,
deduplicates them, and presents each document in chunk order (up to nine chunks).
This preserves source ordering within the available budget, not complete tables.

To test structured evidence on that same index:

```powershell
$env:GROUNDED_OUTPUT_MODE = 'evidence'
.\.venv\Scripts\python.exe scripts/run_generation_evaluation.py --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --output evaluation/results/structured_evidence.json
```

Unset GROUNDED_OUTPUT_MODE or use `text` for the original plain-answer protocol.
The evidence mode requests JSON with answer, period, unit, and source/quote pairs.
It validates shape, source membership and exact quotes after whitespace
normalization, constructs citations from stored metadata, and allows one repair
attempt. A valid quote is not proof that the answer follows from it: period/unit
interpretation, arithmetic and semantic entailment remain evaluation limitations.
This experimental protocol is opt-in pending live measurement. Provider output
budgets are larger for JSON to avoid cutting off quotes.

For an evidence-mode diagnostic run:

```powershell
$env:GROUNDED_OUTPUT_MODE = 'evidence'
.\.venv\Scripts\python.exe scripts/run_generation_evaluation.py --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --include-provider-output --output evaluation/results/evidence_diagnostics.json
```

Each case includes `generation_diagnostics` with one record per attempt and the
actual source-label to chunk/page mapping supplied to generation. Status codes
distinguish `model_abstention`, `invalid_json`, `unknown_source_id`,
`quote_not_in_source`, other schema problems, and `accepted`. An empty input uses
`no_sources`. Raw replies are captured only with `--include-provider-output`;
they may contain source content and should stay in ignored local reports.
Existing reports cannot reveal the reason for old abstentions because those
provider replies were not recorded. These diagnostics do not change acceptance
rules or certify semantic support. Plain-text mode retains its legacy behavior
and does not provide attempt-level validation diagnostics.

See [the page-label audit](page-label-audit.md) for corrected evaluation pages.

The project environment was repaired using the available Python 3.12 runtime.
Activate it with `.\.venv\Scripts\Activate.ps1`, or invoke
`.\.venv\Scripts\python.exe` directly. The repaired environment depends on the
bundled runtime remaining installed; for another machine create a fresh Python
3.12 virtual environment and install the project dependencies.

From the repository root, with Python 3.12 and the virtual environment activated:

```powershell
python -m pip install -e ".[dev]"
python -m pre_commit install
python -m pre_commit run --all-files
```

Ruff linting and formatting run before each commit. If a hook changes files, review
the diff, stage the changes, and commit again. Ruff is pinned to the same version
in the development dependency, hooks, and GitHub Actions workflow.

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -q --basetemp .pytest-tmp
python scripts/run_generation_evaluation.py --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --output evaluation/results/generation_evaluation.json
```

Generation evaluation requires the configured provider key. Reports now retain
all cases, retrieved text and pages, cited pages, page recall (only for page-labelled
cases), abstention rate, and accuracy among answered questions. Text diagnostics
can contain document contents; keep reports local unless cleared for sharing.

Citation accuracy now requires page overlap when expected pages exist. It remains
a source-location metric, not claim entailment. The legacy grounding metric checks
source membership and accepts abstentions; it does not prove factual support.
Do not compare the stricter citation score directly with historical document-only
scores. Verify expected PDF pages manually before using them as ground truth.

## Table and reranking experiment

Build a separate index to preserve the fixed-token baseline:

```powershell
python scripts/index_documents.py data/raw/financebench/pdfs --storage-directory data/processed/table_aware_v1 --strategy table_aware_v1 --chunk-size 200 --overlap 40
```

The experimental chunker retains page-local narrative and adds complete detected
table rows with candidate column headers, blank cells, nearby source text, and one-based PDF
pages. Every row is retained because detection may mistake data for a header.
Header candidates must be checked against original source context. A smoke check
of the benchmark pages found no tables on Best Buy page 51, JPMorgan page 20,
or Verizon page 47; table counts elsewhere do not establish correct extraction.
Ruled-table detection does not guarantee recovery of borderless, merged,
multi-page, or scanned tables. Missing headers/units are never guessed. A table row
is kept whole even when it exceeds the narrative chunk-size limit; long rows may
still be truncated by the embedding or reranker model.

Configure a locally downloaded Sentence Transformers cross-encoder by path or
cached model identifier (choose a model returning one relevance score per pair):

```powershell
$env:RERANKER_MODEL = 'C:\models\financial-reranker'
$env:RERANKER_CANDIDATE_K = '30'
python scripts/run_generation_evaluation.py --vector-store data/processed/table_aware_v1/vectors.sqlite3 --output evaluation/results/table_reranked_generation.json
```

HybridRetriever honors these settings in the API, demo, and generation evaluation.
An unset RERANKER_MODEL preserves baseline ranking. Models load locally only;
missing model files or invalid scores surface as errors rather than silently
changing the experiment. Rank 30 hybrid candidates, retain top K anchors, then
expand neighbors. The demo still uses its original index path; evaluate the new
index before switching it. Use a fresh storage directory for extraction revisions.

Compare baseline, tables-only, reranker-only, and combined runs on the same cases
and generation settings. Remove RERANKER_MODEL for the no-reranker runs. Track
page recall, answer accuracy, citation accuracy, abstentions, and latency. Structured
claim evidence validation and held-out evaluation remain future work.

## Run the controlled comparisons

The downloaded local model is `data/processed/models/ms-marco-MiniLM-L6-v2`.
After table indexing finishes successfully:

```powershell
.\.venv\Scripts\python.exe scripts/compare_retrieval.py --baseline data/processed/local_sentence_transformers/vectors.sqlite3 --tables data/processed/table_aware_v1/vectors.sqlite3 --model data/processed/models/ms-marco-MiniLM-L6-v2
```

Configure GEMINI_API_KEY in the terminal locally (never commit it), then run:

```powershell
.\scripts\compare_generation.ps1
```

The generation script runs baseline, reranker-only, tables-only, and combined
evaluations using the same configured Gemini settings. It restores environment
settings afterwards and stops on a failed run. Outputs live under
`evaluation/results/comparison/`. Preserve previous outputs separately before
repeating if comparing run-to-run variation. A key set in another terminal is
not automatically inherited by the agent or an already running server.

### Structured evidence quote repair

With `GROUNDED_OUTPUT_MODE=evidence`, quotes must be contiguous verbatim source
excerpts (whitespace is normalized). Separate headers, units and rows use separate
evidence entries; invented ellipses are not accepted. One bounded retry provides
validator-specific instructions for quote, source-ID or schema failures. Repeated
validation failure still abstains. Quote membership checks provenance, not semantic
entailment. No benchmark answers or company-specific repair rules are used.

Rerun generation evaluation with the same model settings and cases, saving to a new
output file to preserve the baseline. Unit tests do not establish a live accuracy gain.

Quote repair identifies failed evidence-entry positions and source IDs without
echoing untrusted provider text. It requests complete rows and separate headers;
strict substring validation and the one-retry limit remain unchanged.

Set `STATEMENT_AWARE_RANKING=1` to test experimental soft statement-intent preferences
(disabled by default pending like-for-like generation evaluation): requested statements
take precedence, asset balances favor balance sheets, and capital expenditure
favors cash-flow statements. Multiple numbered note listings without substantive
financial values are downranked; a running contents footer alone is not penalized.
These heuristics require evaluation on the unchanged cases before claiming gains.

Statement-aware ranking also rewards multiword query labels immediately followed
by multiple numeric cells. It does not use expected answers, company names or
benchmark page numbers. This is a text heuristic, not table-aware PDF extraction;
it cannot prove column alignment or analytical conclusions. Run
`python scripts/evaluate_row_matching.py` from the project root for a paired local
retrieval comparison with full neighbor context. Results are saved separately to
`evaluation/results/row_matching_retrieval.json`; generation accuracy must still
be measured with the generation evaluation command.

Local paired retrieval check (2026-10-09): on the unchanged 11 cases, expected-page
recall improved from 9/10 labelled cases to 10/10 with full expanded context.
The formerly missed net-asset balance row was present after row matching. This
does not establish an answer/citation accuracy increase or unseen-case performance.
