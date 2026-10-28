param(
    [switch]$PreflightOnly,
    [switch]$FullSet,
    [string]$OutputPath = 'evaluation/results/generation_targeted_repairs.json'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$selectedCases = @()
if ($FullSet) {
    if (-not $PSBoundParameters.ContainsKey('OutputPath')) {
        $OutputPath = "evaluation/results/generation_50_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    }
} else {
$baseline = Get-Content -LiteralPath 'evaluation/results/generation_50_period_validation.json' -Raw | ConvertFrom-Json
# All prior abstentions plus acquisition questions as regression controls.
# Selection affects evaluation only; no expected answer/page enters retrieval.
$selectedCases = @($baseline.cases | Where-Object { $_.abstained -or $_.question -match 'acquisitions?' })
if ($selectedCases.Count -eq 0) { throw 'No diagnostic cases selected.' }
}
$settings = @{
    GEMINI_MODEL = 'gemini-3.1-flash-lite'
    GEMINI_FALLBACK_MODEL = 'gemini-3.5-flash-lite'
    GEMINI_THINKING_LEVEL = 'minimal'
    CALCULATION_VALIDATION = '1'
    COMPARISON_VALIDATION = '1'
    METRIC_IDENTITY_VALIDATION = '1'
    EVIDENCE_REPAIR_EXCERPTS = '1'
    NUMERIC_ROW_COVERAGE = '1'
    PERIOD_VALIDATION = '1'
    OPERAND_COVERAGE = '1'
    FINANCIAL_DECIMAL_INPUT = '1'
    ABSENCE_VALIDATION = '1'
}
$previousSettings = @{}
foreach ($name in $settings.Keys) {
    $previousSettings[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
try {
foreach ($name in $settings.Keys) {
    [Environment]::SetEnvironmentVariable($name, $settings[$name], 'Process')
}
$runArgs = @('scripts/run_50_generation_collection.py', '--output', $OutputPath)
foreach ($case in $selectedCases) { $runArgs += @('--case-id', $case.case_id) }
if ($PreflightOnly) { $runArgs += '--preflight-only' }
& '.\.venv\Scripts\python.exe' @runArgs
if ($LASTEXITCODE -ne 0) { throw "Collection failed with exit code $LASTEXITCODE" }
} finally {
    foreach ($name in $settings.Keys) {
        if ($null -eq $previousSettings[$name]) {
            Remove-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($name, $previousSettings[$name], 'Process')
        }
    }
}
