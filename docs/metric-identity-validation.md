# Optional income-attribution identity validation

Implemented and verified on 26 October 2026. This improvement is separate from
the lead-required submission and does not change original benchmark labels.

Enable `METRIC_IDENTITY_VALIDATION=1` alongside calculation validation in evidence
mode. When a question explicitly requests net income/earnings/profit/loss
attributable to shareholders, income calculation operands must preserve that
attribution in their metric description and supporting quote. Consolidated or
noncontrolling-interest income cannot substitute just because a ratio rounds to
the expected value. Failures use the existing repair attempt, then abstain.

The flag defaults to off. Evaluation provenance records it and hashes the
implementation. No benchmark company, answer, or reference page is encoded in
the runtime check.

## Verification and limits

219 unit tests pass, including attribution synonyms, consolidated/noncontrolling
substitutions, relabelled evidence and opt-in integration. Ruff passes on changed
implementation and test files.

Offline replay of the comparison-validation collection rejects Coca-Cola's
consolidated-income calculation. Accepted saved cases are 38 versus 39 after the
combined-schema repair: this removes an unsupported metric choice; it is not an
answer-coverage gain. JPMorgan remains recovered by the combined-schema repair.
Artifact: `evaluation/results/metric_identity_replay_20261025.json`.

This is not general semantic validation. It only checks calculation operands whose
metric metadata identifies net income/earnings/profit/loss. Misnamed operands,
unrecognized question wording and direct lookups remain outside scope. It does
not prove period/column alignment or that each value in a long quote belongs to
the attributable-income row. Fresh provider repair behavior is unmeasured.

## Next live comparison

Use the activated environment with a locally configured Gemini key. Retain the
previous settings and choose a new output filename:

```powershell
$env:CALCULATION_VALIDATION = "1"
$env:COMPARISON_VALIDATION = "1"
$env:METRIC_IDENTITY_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
python scripts\run_50_generation_collection.py --output evaluation\results\generation_50_metric_identity.json
```

Keep original strict citation-location results separate from reviewed correctness.
The collection command does not itself establish approved answer accuracy.
