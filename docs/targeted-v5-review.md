# Targeted v5 review — 28 October 2026

Input: `evaluation/results/generation_targeted_repairs_v5.json`.
Scope: ten tuned diagnostic cases, not the full 50-case evaluation.

All ten cases completed without provider errors. Nine answers and one abstention
were returned. Reference citation-location matches increased from 8/10 in v4 to
9/10 (90%). All recorded provider attempts finished with STOP, without fallback.
Answer accuracy remains null pending review; citation location does not establish
answer correctness or entailment.

Activision now returns 1.9%. Its repair preserves the negative capex operands,
links them to evidence entry 1, and uses operand names in the expression. This
resolves the specific v4 evidence-link failure in this run.

Remaining issues:

- 3M capital intensity still abstains.
- AES ROA now uses decimal ratio units but returns -0.01 versus reference -0.02.
  It uses consolidated net loss of 505 and average assets of 35,663. Income-basis
  selection still needs source/reference adjudication; unit correction alone
  does not resolve the discrepancy.
- AES inventory returns 12.14 using average inventory, versus reference 9.5
  using closing inventory. Preserve this definition mismatch explicitly.

The other returned answers retain reference-compatible headline results, but no
approved answer score has been written. Do not report 90% answer accuracy or
90% full-set citation accuracy from this subset. Next: adjudicate the outstanding
reference/definition issues before publishing scores, then run the full set once
with the limitations documented. No runtime edits or API calls during this review.
