# Metric identity: live result reviewed 26 October 2026

Candidate: `evaluation/results/generation_50_metric_identity.json`.
Baseline: `evaluation/results/generation_50_comparison_validation.json`.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Completed cases | 50 | 50 |
| Provider errors | 0 | 0 |
| Answers returned | 38 | 39 |
| Abstentions | 12 | 11 |
| Strict citation-location matches | 31/50 (62%) | 32/50 (64%) |
| Adjudicated answer accuracy | null | null |

Dataset hash, K, index size/mtime and configured model/thinking settings match.
All four optional validation/repair flags are enabled. Index metadata is not a
content hash and model aliases do not prove identical underlying revisions.
The combined-schema fix also changed between runs; this is not an isolated
measurement of metric-identity validation.

## Inspected changes

- General Mills now answers 3,215.4 million using 3,676.2 + (-460.8). Signed
  operands and arithmetic are correct against the previously reviewed cash-flow evidence.
- AMD now calculates quick ratio as (4,835 + 1,020 + 4,126) / 6,369 = 1.57
  rounded. This excludes prepaid assets, addressing the earlier definition issue.
  The broader liquidity judgment still needs qualitative adjudication.
- Coca-Cola abstains at the first model attempt. It no longer returns the known
  consolidated-income substitution, but has not produced the requested answer.
  No runtime attribution-rejection diagnostic occurred; do not claim the validator
  repaired this answer in the live run.
- JPMorgan still abstains. The first response is malformed JSON; the second fails
  exact quote validation. The correct winner recovered in offline replay was not
  successfully produced in this live run.

## Remaining abstentions

3M capital intensity; JPMorgan highest segment income; AES ROA; Adobe income
growth; AMCOR acquisitions; American Express tax-rate change; Coca-Cola payout;
Kraft Heinz turnover; Verizon debt; AES inventory; Activision capex/revenue.

Five cases are direct model abstentions. Six exhaust repairs on JSON, quote or
operand validation. Preserve these distinctions when diagnosing failures.

## Interpretation

Coverage and strict citation matches improved modestly, but remain below the
pre-calculation baseline of 44 answers and 68% citation-location matches. Neither
that baseline nor this run provides fully reviewed semantic answer accuracy.
Original labels and lead-only submission reports remain unchanged.

Next: inspect selected evidence for missing calculation inputs and repair failures
before another full run. Avoid claiming 64% answer accuracy or treating abstention
as a successfully corrected answer.
