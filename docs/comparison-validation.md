# Optional comparison validation

Enable `COMPARISON_VALIDATION=1` in evidence mode to validate questions with an
unambiguous highest/largest/greatest/most or lowest/smallest/least direction.
The flag defaults to off and is recorded in evaluation provenance.

The provider returns an answer containing `{{winner}}` and a comparison object
with signed candidate values, labels, evidence indices, period, metric and unit.
After quote validation, Python checks label/value membership and compatible
metadata, computes the extremum, and renders its label. Unsupported candidates,
duplicate labels, missing placeholders and ties fail validation, triggering the
existing repair/abstention behavior. No benchmark-specific values or labels are used.

Limitations: this does not prove candidate completeness, label/value column
alignment, or truth of period/unit/metric metadata. Equal winners abstain; ties
are not rendered. Questions containing both direction words bypass this protocol
rather than guessing their meaning. Ranking by absolute magnitude is not supported.
Unrelated prose claims are not semantically validated. This is not a guarantee of
correct answers and has not yet been evaluated live.

212 unit tests pass, including synthetic maximum/minimum comparisons, signed
outflows, mismatched metadata, duplicates, ties and integration with source and
calculation checks. Original submission metrics and reference labels are unchanged.

Combined-schema compatibility: after a comparison validates, an omitted calculations
field may be normalized to an empty array for a simple ranking-only template.
The gate rejects remaining placeholders, arithmetic markers/keywords and numeric
assertions not already in the question. Explicit null or malformed calculation
fields remain errors. This conservative syntactic gate is not semantic detection
of all possible arithmetic prose; the existing candidate-completeness limitations
still apply.

Offline replay of `generation_50_comparison_validation.json` accepts saved attempts
for 39 cases rather than 38, recovering JPMorgan's Corporate & Investment Bank
answer. This is not a new live accuracy result. Replay details are saved in
`evaluation/results/combined_schema_replay_20261025.json`.

For the next controlled live comparison, retain the same model/thinking settings:

```powershell
$env:CALCULATION_VALIDATION = "1"
$env:COMPARISON_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
python scripts\run_50_generation_collection.py --output evaluation\results\generation_50_comparison_validation.json
```

Use a locally configured Gemini key and a fresh filename. Compare against the
rendering-v2 run, tracking new schema abstentions as well as ranking corrections.
Keep raw strict citation-location results separate from reviewed correctness.
