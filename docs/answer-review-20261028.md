# Saved-answer evidence review — 28 October 2026

Collection: `evaluation/results/generation_50_20261028_142603.json`.
Case-by-case ledger: `evaluation/results/answer_review_20261028_142603.json`.
The ledger binds the review to the exact collection SHA-256. This is an agent
review of saved evidence, not independent human approval or a held-out evaluation.

## Review outcome

| Classification | Count |
| --- | ---: |
| Source-supported answers | 42/50 (84%) |
| Unsuccessful answers | 6/50 (12%) |
| Unresolved definition cases | 2/50 (4%) |
| Strict reference citation-location matches | 36/50 (72%) |

Final answer accuracy remains unset. Depending on adjudication of the two open
cases, it lies between 84% and 88% under this review rubric. Do not present 88% as
achieved accuracy or confuse source-supported answers with reference-page matches.

## Rubric

Compare the requested metric, period, units and claims against saved evidence.
Accept source-supported precision when the question does not demand a particular
rounding. Accept equivalent wording; a matching yes/no verdict does not excuse an
incorrect additional numeric claim. Count answerable-question abstentions as
unsuccessful. Keep ambiguous financial definitions unresolved rather than changing
the reference or denominator. Citation locations are scored separately.

## Six unsuccessful answers

- 3M capital intensity: abstention.
- Amazon FY2019 shareholder net income: abstention.
- Adobe FY2016 operating income growth: abstention after quote validation failures.
- Verizon debt movement: abstention after the direction validator rejects both replies.
- Activision three-year capex percentage: abstention after validation failures.
- AMD quick ratio: 1.77 includes prepaid expenses/other current assets. The source
  supports liquid assets of 4,835 + 1,020 + 4,126 + 2, divided by liabilities 6,369,
  yielding 1.57. The positive liquidity verdict does not validate the wrong ratio.

## Two unresolved cases

- AES ROA: consolidated net loss 505 gives -0.01 after rounding; attributable
  net loss 546 gives reference -0.02 using average assets 35,663. The question
  does not explicitly specify attribution.
- AES inventory: average inventory gives 12.14; closing inventory gives the
  reference's approximately 9.5. The denominator convention is unspecified.

## Reference discrepancies documented without changing labels

PayPal's current assets 57,517 minus current liabilities 45,101 supports 12,416
million and the positive working-capital verdict. The reference explanation's
1.6 billion is not supported by these balance-sheet totals. This answer is accepted
on source evidence, with the reference issue visible in the review ledger.

3M PP&E 8.738 billion, Block operating cash flow 381.6 million, General Mills FCF
3,215.4 million and Amcor receivables 1,615.9 million preserve source precision
where the references round. Corning's source rates 22.9% and 20.2% support a
2.7-percentage-point change. Walmart's 0.2-percentage-point margin change is not
relative percentage growth.

No generation was rerun, and no benchmark answers, reference pages or runtime
rules were changed during this review. These results belong to the optional
expanded evaluation, separate from the lead-only submission.
