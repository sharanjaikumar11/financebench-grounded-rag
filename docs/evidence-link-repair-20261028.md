# Evidence-link repair — 28 October 2026

Optional improvement following the targeted v4 review.

Calculation repair diagnostics now list zero-based candidate evidence entries
containing an operand's signed value, or its opposite sign. Only quotes verified
against supplied sources qualify. Candidates are numeric matches, not proof of
the correct metric or year. No operand, evidence index or answer is auto-corrected.

Prompts require rechecking all operand links against the final evidence order,
using independent expressions over quoted inputs rather than uncited intermediate
values, preserving requested ratio units, and stating an unspecified denominator
convention. All existing validation gates remain in place.

Validation: 283 unit tests and changed-file Ruff checks passed. Offline inspection
of v4's saved Activision repair correctly identifies evidence entry 1 for all three
mislinked capex operands. See
`evaluation/results/evidence_link_diagnostics_20261028.json`.
This confirms diagnostic behavior, not live answer recovery or accuracy.

AES remains a reference-review issue: inventory 12.1 uses average inventory whereas
9.5 uses closing inventory; ROA also has income attribution and ratio/percent rounding
ambiguity. References and scores were not changed. 3M's qualitative abstention is
unresolved; no answer was forced. A fresh targeted run is needed to measure prompt
effects before a full evaluation.
