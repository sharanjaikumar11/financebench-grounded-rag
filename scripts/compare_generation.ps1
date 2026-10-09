param(
    [string]$Baseline = 'data/processed/local_sentence_transformers/vectors.sqlite3',
    [string]$Tables = 'data/processed/table_aware_v1/vectors.sqlite3',
    [string]$Model = 'data/processed/models/ms-marco-MiniLM-L6-v2'
)
$ErrorActionPreference = 'Stop'
if (-not $env:GEMINI_API_KEY) { throw 'Set GEMINI_API_KEY in this terminal before running this comparison.' }
foreach ($path in @($Baseline, $Tables, $Model)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing experiment input: $path" }
}
# Do not spend provider calls comparing a partially built table corpus.
& ./.venv/Scripts/python.exe -c 'import sqlite3,sys; from pathlib import Path; sets=[]; [(sets.append(set(sqlite3.connect(Path(p).resolve().as_uri()+"?mode=ro",uri=True).execute("SELECT DISTINCT document_name FROM chunks")))) for p in sys.argv[1:]]; sys.exit(0 if sets[0] == sets[1] else "Indexes have different document sets. Wait for table indexing to finish.")' $Baseline $Tables
if ($LASTEXITCODE -ne 0) { throw 'Index comparison preflight failed.' }
$priorModel = $env:RERANKER_MODEL
$priorCandidates = $env:RERANKER_CANDIDATE_K
$priorProvider = $env:ANSWER_PROVIDER
try {
    $env:ANSWER_PROVIDER = 'gemini'
    $env:RERANKER_CANDIDATE_K = '30'
    foreach ($index in @(@{Name='baseline'; Path=$Baseline}, @{Name='tables'; Path=$Tables})) {
        foreach ($rerank in @($false, $true)) {
            $env:RERANKER_MODEL = if ($rerank) { $Model } else { '' }
            $suffix = if ($rerank) { 'reranked' } else { 'hybrid' }
            $reportPath = "evaluation/results/comparison/$($index.Name)_${suffix}_generation.json"
            & ./.venv/Scripts/python.exe scripts/run_generation_evaluation.py --vector-store $index.Path --output $reportPath
            if ($LASTEXITCODE -ne 0) { throw "Evaluation failed: $reportPath" }
        }
    }
} finally {
    $env:RERANKER_MODEL = $priorModel
    $env:RERANKER_CANDIDATE_K = $priorCandidates
    $env:ANSWER_PROVIDER = $priorProvider
}
