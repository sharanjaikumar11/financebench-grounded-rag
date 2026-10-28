# Full-run validation fixes — 28 October 2026

Optional reliability work following `generation_50_20261028_130232.json`.

## Implemented

- A bounded check rejects explicit increase/decrease claims whose stated from/to
  values contradict the direction, after calculation placeholders are rendered.
  It handles signed values and skips differing scales rather than guessing unit
  conversion. This is a narrow contradiction guard, not semantic entailment.
- Repair instructions require rechecking direction, year order and Yes/No
  together without changing quoted inputs to fit prose.
- Every repair prompt reiterates the prohibition on citation markers in the
  answer field and asks for verbatim headers with intervening labels/punctuation.
  Quote membership remains strict; fabricated headers are not normalized away.

## Verification

290 unit tests and changed-file Ruff checks pass. Offline replay of the full 50
saved responses rejects the erroneous Verizon increase claim and retains the
other 45 accepted answers. Results:
`evaluation/results/direction_replay_20261028.json`.

This does not produce a corrected live Verizon answer or improve measured
accuracy. Previously saved model replies are immutable; prompt improvements
require fresh generation. No API calls were made during this fix.

## Still open

Four original abstentions remain in saved responses. The new guard would reject
Verizon, so its saved response becomes an additional validation rejection.
AES, AMD and PayPal definition/reference discrepancies need evidence review.
Alternate-page citations must be reviewed rather than relabelled to improve the
metric. No reference answers, page labels or review scores were changed.
