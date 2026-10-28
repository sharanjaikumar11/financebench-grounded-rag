# Numeric-row coverage: live result

Candidate: `evaluation/results/generation_50_numeric_row_coverage.json`.
Baseline: `evaluation/results/generation_50_metric_identity.json`.
Reviewed against saved provider outputs and actual selected source text.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Completed cases | 50 | 50 |
| Provider errors | 0 | 0 |
| Answers returned | 39 | 42 |
| Abstentions | 11 | 8 |
| Strict citation-location matches | 32/50 (64%) | 34/50 (68%) |
| Approved answer accuracy | null | null |

Dataset hash, K, index size/mtime and configured model/thinking settings match.
All earlier flags remain enabled and numeric-row coverage is enabled. Repair
instructions also changed, so the gains cannot be attributed solely to selection.

## Case-level findings

- JPMorgan now correctly selects Corporate & Investment Bank from the segment
  table after repair. The emitted comparison candidates omit Corporate, but the
  complete quoted row includes its negative net income; it cannot change the maximum.
- Verizon now sums quoted current and long-term debt components rather than using
  computed totals as supposedly quoted operands. The totals and decline match the
  prior source review. Strict citation location still fails because it cites an
  alternative supporting page.
- Kraft Heinz returns 6.33, but this is an **incorrect-period calculation**, not a
  verified gain. S7 explicitly says 'For the Year Ended December 30, 2017'; its
  COGS figure 17,043 is incorrectly labelled FY2019 in the operand metadata and
  combined with 2019/2018 inventories. Citation location passes despite this error.
- Adobe now has operating income 1,493,602 / 903,095 in S2, but both attempts quote
  the year header from S2. That header exists in S1, so exact provenance checks
  correctly reject the response. Missing context has become a source-assignment issue.

## Remaining eight abstentions

3M capital intensity; AES ROA; Adobe operating-income growth; AMCOR acquisitions;
American Express tax-rate change; Coca-Cola payout; AES inventory turnover;
Activision capex/revenue.

Next priorities are period/column validation and deterministic repair hints that
identify an exact quote's correct supplied source ID. Do not relax quote matching
or accept an operand's asserted year as proof. Missing required statement rows
remain a retrieval issue for several cases.

68% is citation-location matching, not answer accuracy. No full semantic score is
published, original labels remain unchanged, and no new code changes are claimed
by this result review.
