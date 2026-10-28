# Calculation validation: first live comparison

Baseline: `evaluation/results/generation_50_repair_excerpts_20261025.json`.
Candidate: `evaluation/results/generation_50_calculation_validation.json`.
Both contain 50 completed cases with the same recorded dataset hash, K=5,
embedding model and configured Gemini models/thinking level. Index size and mtime
match, but are not an immutable content hash.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Completed cases | 50 | 50 |
| Provider-error cases | 0 | 0 |
| Answers returned | 44 | 23 |
| Abstentions | 6 | 27 |
| Strict citation-location matches | 34/50 (68%) | 18/50 (36%) |
| Approved answer accuracy | Unreviewed/null | Unreviewed/null |

This is a regression in answer coverage and strict citation-location matching.
It is not a measured change in fully adjudicated answer or semantic citation accuracy.
Do not promote calculation validation to the default configuration.

## Configuration caveat

The candidate recorded `CALCULATION_VALIDATION=1`, but also
`EVIDENCE_REPAIR_EXCERPTS=0`; the baseline had repair excerpts enabled.
Consequently the result cannot isolate the causal effect of the calculation flag.
Configured provider aliases also do not establish identical underlying revisions.

## Diagnostics

Across candidate attempts (not unique cases): 21 invalid JSON responses,
14 invalid-calculation responses, 12 quote mismatches, 3 operand-membership
failures, 2 result mismatches, 8 model abstentions and 23 accepted responses.

Inspected examples:

- Amazon net income: the first response was enclosed in a Markdown JSON fence;
  the repair then failed exact quote validation.
- AMD cash-flow comparison: both attempts omitted the required calculations list,
  despite providing a qualitative maximum answer with validated quotes.
- Activision fixed-asset turnover: both attempts used supported inputs but declared
  incorrect arithmetic results (23.70 then 24.11). The validator rejected both;
  the supplied expression evaluates to 24.26 rounded to two decimal places.

## Next implementation

1. Handle one complete JSON fence deterministically without accepting surrounding
   commentary or weakening quote checks.
2. Clarify the output schema and repair instructions for direct lookups and
   qualitative answers; do not blindly waive calculation requirements.
3. Consider rendering deterministic calculated results directly after input and
   expression validation, with explicit diagnostics, rather than asking the model
   to recompute arithmetic. Metric/period selection still needs review.
4. Test these changes offline against saved responses and synthetic adversarial
   cases, then rerun with repair excerpts enabled and the same 50 questions.

The original reports and benchmark labels are unchanged. This is an optional
improvement experiment, not part of the original submission metrics.
