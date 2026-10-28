# Targeted generation result: 2026-10-26

Optional diagnostic subset, not a full 50-case evaluation.
Result: `evaluation/results/generation_targeted_repairs.json`.
Baseline: the same ten cases in `generation_50_period_validation.json`.

| Measure | Previous same-case results | New targeted run |
|---|---:|---:|
| Cases completed | 10 | 10 |
| Answers returned | 1 | 4 |
| Abstentions | 9 | 6 |
| Strict citation-location matches | 1/10 | 4/10 |
| Approved answer accuracy | null | null |

All intended flags, including OPERAND_COVERAGE and PERIOD_VALIDATION, are enabled.
No provider/pipeline errors were recorded. This selected difficult subset cannot
be compared directly with the full-set 66% citation-location baseline or used to
infer a new full-set score.

## Answer/evidence inspection

| Case | Outcome | Assessment |
|---|---|---|
| 3M capital intensity | Abstains | Qualitative criterion remains unresolved. |
| AES ROA | Returns -1.42% | Computes consolidated loss -505 divided by average assets 38,363/32,963, expressed as a percentage. Reference -0.02 uses a different basis/rounding. Retrieval recovered; do not mark benchmark answer correct. |
| Adobe growth | Abstains | Both replies still assign the year header to S2, although it belongs to S1. |
| AMCOR acquisitions | Answers FY2023 events | All three event descriptions are supported; explicitly reports lack of information for earlier years. Partial coverage of the three-year question, not proof of no earlier acquisitions. |
| American Express tax | Abstains | First reply has a wrong-source quote; repair then uses numeric literals in the expression and operand names beginning with digits. |
| Best Buy acquisitions | Answers | Retains two FY2022 acquisitions. Claims of no acquisitions in other years need stronger support: a zero cash-flow acquisition line alone does not establish absence of all acquisitions. |
| Coca-Cola payout | Abstains | Correct rows retrieved, but both replies declare positive 7616 against a quoted negative cash outflow. |
| Kraft Heinz turnover | Returns 6.25 | Verified current-year COGS 16,830 and inventories 2,721/2,667 with their dates in actual source text. Corrects the former wrong-year calculation. |
| AES inventory turnover | Abstains | Both replies declare positive cost of sales against the negative quoted amount. Average versus closing inventory also remains a reference-definition issue. |
| Activision capex/revenue | Abstains | Correct three-year rows retrieved, but operands lose cash-outflow signs and expressions contain copied financial literals instead of operand names. |

## Decision

Do not run another full generation evaluation yet. Retrieval fixes recovered
missing evidence, but the generator is not reliably following the evidence and
calculation schema. Keep strict validation; do not silently flip signs, relabel
sources, change benchmark definitions or count partial answers as correct.

Next implementation should provide precise, structured repair diagnostics for
offending operands/expressions and source entries, then test the affected cases.
Also address unsupported absence claims and settle the documented rubric
ambiguities. A schema-constrained response alone cannot establish source
membership, period alignment or semantic correctness.
