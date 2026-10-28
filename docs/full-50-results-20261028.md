# Full 50-case collection — 28 October 2026

Source: `evaluation/results/generation_50_20261028_130232.json`.
Optional expanded diagnostic evaluation; separate from lead-only deliverables.

| Measure | Result |
| --- | ---: |
| Completed | 50/50 |
| Provider/pipeline errors | 0 |
| Answers returned | 46/50 (92%) |
| Abstentions | 4/50 (8%) |
| Expected-filing retrieval hits | 50/50 (100%) |
| Labelled-page retrieval hits | 47/49 (95.92%) |
| Strict reference citation-location matches | 35/50 (70%) |
| Reviewed answer accuracy | Pending; null |

The targeted subset's 90% citation-location score did not generalize to this full
set. There are eleven answered cases with unmatched citation locations and four
abstentions. A location mismatch requires evidence review: it can be an alternate
valid page or an actual citation error. Do not relabel pages solely to raise scores.
Compared with the earlier period-validation full run, answers increased from 41
to 46 and strict citation-location matches from 33 to 35. This comparison does not
isolate individual changes or establish semantic accuracy improvements.

## Findings requiring review

- Abstentions: 3M capital intensity and Amazon net income (model abstention);
  PepsiCo capex (quote failure followed by invalid answer); American Express tax
  rate (quote membership failures on both attempts).
- Verizon debt is a confirmed directional error: the answer says debt increased,
  but its own computed values decrease from 150,868 to 150,639 million. The
  arithmetic validator does not guarantee the accompanying prose is correct.
- AES ROA and inventory retain the previously documented basis/definition
  discrepancies against the reference.
- AMD quick ratio uses current assets minus inventories and returns 1.77, versus
  the reference's selected liquid-asset numerator and 1.57. Review the question,
  source and metric definition before adjudicating.
- PayPal reports positive working capital of 12,416 million versus the reference
  explanation's 1.6 billion; the yes/no conclusion alone cannot settle whether
  its additional amount uses the requested definition.

No answer decisions have been approved or copied from older runs. Returned-answer
rate is not answer accuracy; citation location is not claim entailment. Preserve
this collection and review it rather than rerunning to obtain a better score.
