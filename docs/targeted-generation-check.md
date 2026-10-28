# Targeted generation verification

Before a full 50-case evaluation, collect answers for the nine abstentions from
`generation_50_period_validation.json` and acquisition regression questions.
This currently selects ten cases, including Best Buy. It is a diagnostic subset,
not a replacement benchmark or a new full-set accuracy score.

From the project folder, in PowerShell with `GEMINI_API_KEY` configured locally:

```powershell
.\scripts\run_targeted_generation.ps1
```

The launcher uses the existing virtual environment, baseline Gemini model and
thinking settings, and enables the evidence, calculation, comparison, metric,
period, numeric-row and operand-coverage checks. It restores prior environment
settings afterward. The key is neither printed nor written to reports.

Output: `evaluation/results/generation_targeted_repairs.json`. Existing output
is never overwritten. Use `-PreflightOnly` for a no-API readiness check.

The collection script accepts repeated `--case-id` arguments for other diagnostic
subsets. It validates the unchanged 50-case source audit first, records selected
IDs and code hashes, preserves original/addition cohort membership, and uses the
subset's actual denominators. Empty groups have no accuracy score.

Inspect generated answers, source IDs, quoted row/header alignment and repair
diagnostics before proceeding. Ambiguous reference criteria remain documented in
`pending-issue-audit-20261026.md`; do not tune answers to those references.
