# Period validation: live comparison

Optional improvement evaluation, separate from the lead-required submission.

Baseline: `evaluation/results/generation_50_numeric_row_coverage.json`.
Candidate: `evaluation/results/generation_50_period_validation.json`.
Reviewed on 2026-10-26 using saved responses, source text and diagnostics.

| Measure | Baseline | Candidate |
|---|---:|---:|
| Completed cases | 50 | 50 |
| Provider errors | 0 | 0 |
| Expected-filing retrieval hits | 50/50 | 50/50 |
| Answers returned | 42 | 41 |
| Abstentions | 8 | 9 |
| Strict citation-location matches | 34/50 (68%) | 33/50 (66%) |
| Fully reviewed answer accuracy | null | null |

Dataset and source-audit hashes, K, index size/mtime, configured models and
thinking level match. Index size/mtime do not prove identical contents, and
configured model aliases do not establish an immutable provider revision.
Period validation is enabled; source-repair instructions also changed.

## Findings

- Kraft Heinz's answer changes from 6.33 to INSUFFICIENT_CONTEXT. Its first
  attempt fails quote membership; the repaired quote then passes membership
  but its FY2019 COGS operand conflicts with the source's explicit 2017 heading.
  The new check correctly blocks this known incorrect answer. The strict page
  score loses one match because the previous wrong answer cited a reference page.
- All other cases retain their previous abstention and citation-match outcomes.
  This does not establish that every answer's wording or correctness is unchanged.
- Adobe still attributes the year header to S2 rather than S1 on both attempts.
  Reconstructing the repair prompt confirms the hint identifies S1 correctly.
  The model did not use that hint to fix the source assignment in this run.
- Nine cases abstain: 3M capital intensity, AES ROA, Adobe operating-income
  growth, AMCOR acquisitions, American Express tax-rate change, Coca-Cola
  payout, Kraft Heinz inventory turnover, AES inventory turnover, and
  Activision capex/revenue.
- Eight answered cases fail strict citation-location matching: 3M dividend
  trend, AMD cash-flow activity, Corning tax rate, Foot Locker CEO experience,
  MGM region EBITDAR, Pfizer PP&E, Verizon debt, and Walmart operating margin.
  A failed location match alone does not prove the cited evidence is wrong;
  changed generated answers require review against their actual source text.

## Next work

Retain the wrong-period check. Investigate bounded source-repair context for
header/row assignment and retrieval of missing statement rows. Test these
offline before another full generation run. Complete semantic review of the
actual answers and supporting citations before publishing answer accuracy.

No benchmark labels were changed. 41/50 answers returned is coverage, not 82%
answer accuracy. The measured 66% is citation-location agreement, not entailment.
