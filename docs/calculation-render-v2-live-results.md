# Calculation rendering v2 — live results

Collection: `evaluation/results/generation_50_calculation_render_v2.json`.
All 50 cases completed; no provider-error cases. Answer adjudication remains null.

| Measure | Pre-calculation baseline | First calculation run | Rendering v2 |
|---|---:|---:|---:|
| Answers returned | 44 | 23 | 38 |
| Abstentions | 6 | 27 | 12 |
| Strict citation-location matches | 34/50 (68%) | 18/50 (36%) | 30/50 (60%) |

The first calculation run disabled repair excerpts; v2 enables them, as did the
baseline. Improvements over that first run cannot be attributed solely to rendering.
These are coverage and location metrics, not reviewed answer or semantic citation accuracy.

## Inspected findings

- Activision fixed-asset turnover now renders 24.26 and Amazon DPO 93.86, matching
  the independently checked calculations in the prior source review.
- JPMorgan Q2 2022 is a confirmed answer error despite passing citation location.
  The accepted response says Consumer & Community Banking. Its own quoted table
  reports CCB 3,100 and Corporate & Investment Bank 3,725 million; the latter is highest.
  The first attempt chose the right segment but failed quote validation; repair
  changed the conclusion incorrectly. Exact quote matching does not validate rankings.
- Kraft Heinz renders 7.10 from the supplied operands. Its COGS quote is only
  `5,077 19,126 2,976`, without a row label/year header. Numeric membership alone
  does not establish that 19,126 is the requested FY2019 COGS; this needs source review.
- PepsiCo capex abstains because the model supplies positive 4,625 against a quoted
  negative cash outflow `(4,625)`. The repair also substitutes an unsupported literal
  expression. Correct handling is a signed evidence operand and explicit magnitude
  conversion in the expression, not relaxing the source-sign check.

Attempt diagnostic counts: accepted 38; operand membership 7; model abstention 6;
quote mismatch 5; invalid calculations 3; invalid quote type 2. These count attempts,
not unique questions. JSON-format failures were eliminated in this run.

## Next priorities

Keep calculation validation opt-in. Add generic comparison/ranking checks, improve
signed cash-outflow repair guidance, and require evidence that identifies operand
metric and period. Review remaining responses and resolve rubric ambiguities before
publishing answer accuracy. No original labels or scores have been changed, and
no 90–95% accuracy claim is supported by this run.
