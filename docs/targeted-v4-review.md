# Targeted v4 review — 28 October 2026

Input: `evaluation/results/generation_targeted_repairs_v4.json`.
This ten-case diagnostic subset is not the full 50-case evaluation.

## Results

| Measure | v3 | v4 |
| --- | ---: | ---: |
| Completed cases | 9/10 | 10/10 |
| Returned answers | 3 | 8 |
| Abstentions | 6 | 2 |
| Provider/pipeline errors | 1 | 0 |
| Reference citation-location matches | 3 (aggregate withheld due to error) | 8/10 (80%) |

Answer accuracy remains unreviewed/null. A returned answer and matching citation
location do not establish semantic correctness. The tuned subset cannot establish
full-set accuracy or isolate the causal effect of each change.

All recorded v4 attempts have finish reason STOP, 4096 output-token limit and no
fallback. No truncated JSON or provider errors occurred in this run; this does
not guarantee they cannot recur.

## Answer review observations

- Adobe returns 65.4%, with repaired source assignment for the year heading.
- AMCOR lists the three supported FY2023 acquisitions and explicitly states
  the available evidence does not cover FY2022/FY2021.
- American Express returns a decrease of 3.0 percentage points.
- Best Buy lists the two FY2022 acquisitions. The validator rejects the initial
  unsupported no-acquisitions claim; the repair distinguishes missing evidence.
- Coca-Cola now returns the requested ratio 0.80 rather than a percentage.
- Kraft Heinz returns 6.25 using the requested average inventory denominator.
- AES ROA returns -1.42%, while the reference is -0.02. Income basis and
  ratio-versus-percent rounding need explicit review; do not count it correct
  simply because the cited pages match.
- AES inventory returns 12.1 using average inventory; the reference 9.5 uses
  closing inventory. Record this definition mismatch rather than silently
  changing the benchmark or forcing its answer.
- 3M capital intensity still abstains.
- Activision has complete JSON now. The repair fixes signs and the formula but
  assigns capex operands to evidence_index 0 (the revenue quote) instead of
  evidence_index 1 (the capex quote). The validator correctly rejects this.

## Next action

Before a full evaluation, improve generic evidence-index repair guidance and
review the two AES definition/unit mismatches. Preserve the evidence checks and
original references. This review does not modify runtime code or start API calls.
