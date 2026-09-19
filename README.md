# Production RAG System

Grounded retrieval-augmented generation over FinanceBench filings. The system ingests PDF, TXT, and Markdown sources, preserves source provenance, retrieves locally with Sentence Transformer embeddings, and produces Gemini-grounded answers with citations.

## Setup

```powershell
cd C:\Users\shara\Projects\production-rag-system
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Set the key only in the terminal session that will run answer generation:

```powershell
$env:GEMINI_API_KEY = "your_key"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
```

## Run

Start the API after the local fixed-token index is built:

```powershell
uvicorn rag_system.main:app --host 0.0.0.0 --port 8000
```

Endpoints: `GET /health`, `POST /index`, and `POST /query`.

## Lead demo

With `GEMINI_API_KEY` set in the terminal, run the Streamlit demo:

```powershell
streamlit run streamlit_app.py
```

The browser opens at `http://localhost:8501` and shows grounded answers, source citations, and safe insufficient-context responses.

## Evaluation

Run the reproducible final retrieval experiment:

```powershell
python scripts\run_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --chunking-strategy fixed_token --top-k 3 --retrieval-mode hybrid --apply-query-metadata-filter --output evaluation\results\fixed_token_hybrid_top_k_3_metadata_filtered.json
```

Run grounded answer evaluation with the key available in the same terminal:

```powershell
python scripts\run_generation_evaluation.py --vector-store data\processed\local_sentence_transformers\vectors.sqlite3 --output evaluation\results\generation_evaluation.json
```

## Tests

```powershell
python -m pytest -q
```

## Container

```powershell
docker compose up --build
```
