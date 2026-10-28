# Optional citation failure audit — 2026-10-25

Baseline: `generation_50_collection_20261025.json`, 50 completed responses,
7 abstentions, 34/50 strict expected-document/page citation hits (68%).
This audit does not change labels, answer references, grading or saved results.

## All 16 failures classified

| Case | Observed stage | Review required |
| --- | --- | --- |
| 00499 | Model abstention | Capital-intensity reasoning and reference definition |
| JPMorgan Q2 2022 demo | Quote rejection twice | Label/value copied without intervening table cells |
| 01858 | Answer, different page | Dividend history quoted on page 73 versus reference 62; time scope |
| 10420 | Model abstention | ROA operands and numerator definition |
| 01279 | Answer, different page | Cash-flow comparison table on page 51 versus reference 58 |
| 07507 | Quote rejection twice | Proposed figures changed between attempts; do not accept merely to reduce abstentions |
| 01079 | Model abstention | Three-year acquisitions question/reference completeness |
| 01346 | Answer, different pages | Detailed tax rates versus rounded summary; period/precision policy |
| 00839 | Answer, different filing | Prior CEO employment supported elsewhere; similarity claim still needs review |
| 10499 | Quote rejection twice | Inconsistent proposed COGS/ratios; verify operands |
| 00382 | Answer, different filing | Annual report versus earnings release; compare all segments, not one value alone |
| 00302 | Answer, different pages | Verify year headers and net/gross PP&E interpretation |
| 00566 | Answer, different pages | Verify debt components/periods and sum |
| 04784 | Answer, different page | Net-sales versus total-revenue margin denominator policy |
| 00540 | Answer, different page | Inventory nature supports discussion but does not by itself prove turnover is meaningless |
| 07966 | Quote rejection then abstention | Claimed revenue/capex values and period alignment |

Numeric IDs above have the `financebench_id_` prefix. The JPMorgan case is
`financebench_demo_jpmorgan_2022q2_highest_net_income`.

## Source-location check

`scripts/audit_citation_failures.py` checked accepted evidence quotes against the
actual cited PDF pages, using whitespace normalization only. All quoted excerpts
for the nine answered failures matched. This is source-location evidence, **not
semantic approval of the full answers**. Complete table/layout/claim adjudication
is still pending. No alternative page was added to the benchmark in this pass.

For rejected quotes, the audit also searched all sources supplied in the relevant
attempt. No failed-quote repair was found by simply reassigning its source ID.
Therefore source-ID reassignment is not a supported fix for this run.

Local audit artifact: `evaluation/results/citation_failure_audit_20261025.json`.
It records the collection hash and cited-PDF hashes, locations and quote checks.
Raw excerpts remain local and should not be published without review.

## Generic repair experiment

`EVIDENCE_REPAIR_EXCERPTS=1` repeats the failed sources as JSON data during the
existing single repair attempt. It explicitly asks for contiguous rows including
intervening columns, all required operands and period alignment. No answer values
are inserted, no pages are guessed and exact-quote validation remains unchanged.
The flag defaults off and is recorded in evaluation provenance. This is prompt
copy assistance, not a table parser or semantic validator; no gain is claimed yet.

## Next live comparison

Run the identical collector profile with only the repair flag changed, preserving
the baseline and choosing a fresh output path:

```powershell
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
python scripts/run_50_generation_collection.py --output evaluation/results/generation_50_repair_excerpts_20261025.json
```

Use the same Gemini model/fallback/thinking settings and local key as the original
run. Additional source repetition increases repair prompt size. A single paired
run remains sensitive to provider variability. Compare unchanged strict citation
hits, abstentions and answer evidence, not just response completion.

Even if all nine alternative citations were later approved, that would be 43/50
(86%), not 90–95%, with seven abstentions still remaining. This is a hypothetical
ceiling for relabelling the current answered cases, not a revised measured score.
Reaching 90% requires 45 supported, correctly cited responses; at least two current
abstentions would also need valid answers. Label-audit adjustments and actual
system improvements must be reported separately.
