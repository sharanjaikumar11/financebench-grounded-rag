# Targeted v3 review

Input: `evaluation/results/generation_targeted_repairs_v3.json`.
This is a ten-case diagnostic subset, not a full evaluation.

## Outcome

- Nine cases completed; AES inventory turnover ended in `provider_or_pipeline_error`.
- Three answers, six abstentions and one error, versus eight answers and two
  abstentions in v2.
- Three returned answers match labelled citation locations. The report correctly
  leaves aggregate citation-location accuracy null because the run contains an error.
- Answer accuracy remains unreviewed/null. Do not report a successful accuracy gain.

## Findings from saved outputs

- **AES error:** only `RuntimeError` was retained. There is insufficient diagnostic
  information to distinguish provider failure, empty output or a pipeline exception.
  Do not guess quota, timeout or availability as the cause.
- **Adobe:** source membership is repaired, but operands use `operatingIncome2016`
  and `operatingIncome2015`; the current name regex permits lowercase only.
- **Kraft Heinz:** repaired evidence includes the right rows and dates; calculation
  ID `turnoverRatio` violates the same lowercase-only restriction.
- **Activision:** first response stops mid-JSON. The provider's structured-output
  budget is 1,024 tokens, consistent with truncation, but finish-reason telemetry
  was not captured so the exact reason is unconfirmed. Repair uses financial
  numeric literals in the formula instead of declared operand names.
- **AMCOR and Best Buy:** both abstain on their first attempt. The absence prompt
  no longer yields the previous unsupported Best Buy absence claims, but these
  replies also omit the supported acquisition events.
- **Coca-Cola:** returns 79.82% rather than the requested ratio rounded to two
  decimals (0.80). Same underlying calculation, different presentation/rounding;
  a citation-location match is not sufficient for answer correctness.
- **AES ROA:** still returns -1.42%; income basis and ratio/percentage interpretation
  remain unresolved against reference -0.02.
- **American Express:** returns -3.0 percentage points, consistent with the quoted
  rates. **3M:** qualitative abstention remains.

## Before another run

1. Remove unnecessary case-style restrictions from safe AST identifiers while
   retaining length, uniqueness and exact-name matching; test saved responses.
2. Capture secret-free provider error categories/status codes and actual finish
   reasons, and use a suitable bounded structured-response budget.
3. Strengthen formula and unit instructions, without inventing source values or
   changing benchmark definitions. Decide how partial multi-year answers are scored.
4. Validate locally and retry affected cases only before any full evaluation.

The saved v3 output is preserved. No raw exception message or API credential has
been added to reports, and no new model calls were made during this review.
