# Production RAG System

Grounded retrieval-augmented generation over FinanceBench filings. The system ingests PDF, TXT, and Markdown sources, preserves source provenance, retrieves locally with Sentence Transformer embeddings, and produces source-cited answers using Gemini or Groq.

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

## Lead demo

With the selected provider's API key set in the terminal, run the Streamlit demo:

```powershell
streamlit run streamlit_app.py
```

The browser opens at `http://localhost:8501` and shows grounded answers, source citations, and safe insufficient-context responses. When the cited FinanceBench PDF is available under `data/raw/financebench/pdfs/`, the application automatically starts a loopback-only PDF source server on port `8502`. Each source link then opens the browser-served PDF at its first cited page. Set `FINANCEBENCH_PDF_SERVER_PORT` before starting Streamlit only if port `8502` is occupied. The application uses `GEMINI_FALLBACK_MODEL` only when the primary Gemini model returns a temporary capacity error; otherwise, generation failures are reported clearly.

## Evaluation

Latest saved 11-case generation result: **81.82% answer accuracy and 81.82%
citation accuracy**. See [experiment report](docs/experiment-report.md) and
[sanitized summaries](evaluation/published/). These are development-set results,
not production-wide accuracy. To evaluate the improved optional path:

```powershell
$env:GROUNDED_OUTPUT_MODE = "evidence"
$env:STATEMENT_AWARE_RANKING = "1"
python scripts/run_generation_evaluation.py --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --include-provider-output --output evaluation/results/review_generation.json
```

Keep the model settings fixed and preserve previous reports. The command requires
the provider key in the same terminal. Raw outputs may contain document excerpts;
do not publish them without review. Export a safe summary with
`python scripts/export_evaluation_summary.py evaluation/results/review_generation.json --output evaluation/published/review_generation.json`.

Run a retrieval-only experiment (this runner trims expanded context to K; its
page coverage is not directly comparable to full-context generation evaluation):

```powershell
python scripts\run_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --chunking-strategy fixed_token --top-k 3 --retrieval-mode hybrid --apply-query-metadata-filter --output evaluation\results\fixed_token_hybrid_top_k_3_metadata_filtered.json
```

Run grounded answer evaluation with the key available in the same terminal:

```powershell
python scripts\run_generation_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --output evaluation\results\generation_evaluation.json
```

## Tests

See [the development runbook](docs/runbook.md) for Ruff pre-commit setup,
CI checks, and interpreting page-level evaluation diagnostics.

```powershell
python -m pytest -q --basetemp .pytest-tmp
```

## Container

```powershell
docker compose up --build
```
