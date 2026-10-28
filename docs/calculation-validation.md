# Calculation validation (optional improvement)

Implemented and unit-tested. Live 50-case accuracy impact has not been measured.
This extension is separate from the lead-required submission.

## Behavior

Enable `CALCULATION_VALIDATION=1` with `GROUNDED_OUTPUT_MODE=evidence`.
The provider supplies calculations and answer placeholders. After existing quote
validation, the application checks signed operands against quoted numeric tokens,
evaluates bounded decimal arithmetic and renders the computed, rounded result.
The model no longer supplies a result; legacy result fields are ignored. An invalid
operand, expression or source response gets the existing single repair attempt;
if that fails, the application abstains.

Allowed operations are addition, subtraction, multiplication, division and unary
signs. An AST allowlist rejects calls, attributes, indexing and powers; no `eval`
is used. Expression length, operand counts, decimal precision and intermediate
magnitudes are bounded. Structural constants cover averages, percentages, day counts
and unit conversion; financial values must be evidence-linked operands.

The flag defaults to off and is recorded in run provenance along with a hash of
the protocol implementation. No company IDs, benchmark answers or reference pages
are used by the calculation validator.

Current protocol: `decimal-render-v2`, recorded in generation diagnostics.
Signed-outflow guidance now explicitly retains negative operands, negates them only
for requested expenditure magnitudes, and adds signed capex for free cash flow.
The validator still rejects positive operands against parenthesized negative quotes.
This prompt change has not been measured in a live run; synthetic repair tests do
not demonstrate provider compliance.

201 unit tests pass. Saved-response replay after the formatting repair and direct
calculation rendering accepts attempts for 26/50 cases versus 23/50 in the original
live collection. This is not live accuracy: saved repair responses came from the
old prompts, and accepted answers have not all been semantically adjudicated.
See `evaluation/results/calculation_render_v2_replay_20261025.json`.

## Limits

Numeric membership does not establish the correct metric, period or column.
Operand metric/period/unit fields are metadata, not semantic validation. The model
can still misclassify a derived answer as a lookup with an empty calculation list,
or make unsupported claims outside calculated placeholders. This is an arithmetic
check, not a guarantee of complete correctness or semantic citation accuracy.
The additional schema may increase abstentions; measure that before enabling it
by default. Original evaluation labels remain unchanged.

## Live comparison in PowerShell

Use the activated environment and a locally configured `GEMINI_API_KEY`:

```powershell
$env:CALCULATION_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
python scripts\run_50_generation_collection.py --output evaluation\results\generation_50_calculation_render_v2.json
```

The collection script sets evidence mode and the existing retrieval flags/K=5.
It refuses to overwrite results. Compare with
`generation_50_repair_excerpts_20261025.json`, reviewing repaired answers and new
abstentions. Collection alone does not publish approved answer accuracy.

Tests: `python -m pytest tests/unit -q --basetemp .pytest-tmp-calc-unit`.
