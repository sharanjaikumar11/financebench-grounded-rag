# Targeted v2 review and financial decimal input

Optional diagnostic work; original benchmark labels remain unchanged.

## Live v2 result

`generation_targeted_repairs_v2.json` completed all ten cases without provider
errors: eight answers, two abstentions and 8/10 strict citation-location matches.
This selected subset is not a full-set accuracy estimate.

- Adobe now assigns the year header to S1 and returns 65.4%.
- American Express returns a decrease of 3.0 percentage points. Its accepted
  quote includes the rate row; the supporting year mapping is present elsewhere
  in supplied context but omitted from the final evidence entries.
- Coca-Cola uses the signed dividend outflow and attributable income, returning 0.80.
- Kraft Heinz preserves the current-year COGS/inventory columns and returns 6.25.
- AES ROA uses consolidated loss and percentage units (-1.42%); this is not the
  reference ratio -0.02. Income basis, units and rounding remain unresolved.
- AES inventory uses average inventory (12.1 times), while the reference 9.5
  reflects closing inventory. Arithmetic consistency does not resolve that definition.
- AMCOR supplies FY2023 events and explicitly lacks earlier-year information.
  It is incomplete against the three-year question.
- Best Buy's FY2022 acquisitions are supported; claims of no acquisitions in
  other years are not established by a zero acquisition cash-flow line alone.
- 3M capital intensity abstains; no agreed qualitative criterion is available.
- Activision fixes its formula in repair but uses parenthesized/comma-formatted
  operand strings, rejected by the existing canonical-decimal-only schema.

This is review of saved evidence, not completed independent PDF adjudication.
Do not publish 80% answer accuracy from the location-match result.

## Implemented format fix

Opt-in `FINANCIAL_DECIMAL_INPUT=1` accepts strictly grouped numeric strings such
as `6,489`, `-2,400` and `(116)`, interpreting the latter as negative 116. The
existing digit/precision limits remain. Malformed grouping, unmatched parentheses,
currency symbols, exponent notation and ambiguous mixed signs are rejected.

This is numeric-notation parsing, not a sign correction: positive `1,200` still
fails against a quote containing only `(1,200)`. Every parsed value still undergoes
quote membership and arithmetic/period checks. The shared comparison-value parser
uses the same opt-in rule. The flag is recorded in run provenance and enabled in
the targeted launcher; normal application defaults remain unchanged.

## Offline verification

- 261 unit tests pass; Ruff passes on changed Python files.
- Replaying saved v2 attempts with the flag accepts Activision's repaired response
  and renders 1.9%. All eight previously answered cases retain an accepted attempt.
- Nine cases have an accepted saved attempt; 3M still abstains. This is validation
  coverage, not 90% answer accuracy, and no new API responses were generated.
- Result: `evaluation/results/financial_decimal_replay_20261026.json`.

The live v2 file is preserved. Resolve the semantic/rubric findings above before
claiming full correctness or promoting strict citation matches to entailment scores.
