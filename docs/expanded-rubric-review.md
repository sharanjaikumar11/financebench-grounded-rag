# Optional expanded evaluation: reference and rubric review

Review started 2026-10-25. This is separate from the lead-only submission.
The unchanged 50-case draft is **not yet approved for generation scoring**.

## Completed in this pass

- Inventoried all 50 questions/references and created a review ledger preserving
  original-11 versus added-39 membership and audited physical page locations.
- Assigned suggested rubric families, not automatic approvals.
- Inspected upstream evidence excerpts for AES ROA/inventory turnover, AMCOR
  acquisitions, American Express/Corning tax rates and Walmart margin change.
  These excerpts were previously page-matched; this pass is not a fresh visual
  PDF audit or independent verification of every answer.
- Left original questions, references, labels and source-audit hashes unchanged.
  No case exclusions, replacements, generation calls or new accuracy claims.

## Specific review findings

| Case | Finding | Required disposition before scoring |
| --- | --- | --- |
| financebench_id_04209 | Costco FY2021 assets repeats the original demo question's fact | Tag as duplicate coverage; retain historical 50-case diagnostics but define a distinct-question reporting policy before live scoring |
| financebench_id_04700 | Microsoft FY2016 COGS repeats the original demo question's fact | Same duplicate policy; do not silently inflate independent case count |
| financebench_id_01079 | Question asks FY2021–FY2023 acquisitions, reference/excerpt lists FY2023 acquisitions only | Review remaining periods; do not approve a partial reference as a complete three-year answer |
| financebench_id_01077 | Best Buy reference discusses FY2022 acquisitions for a three-year question | Verify completeness across all requested years, not just named transactions |
| financebench_id_00540 | AES 9.5 turnover matches 10,069/1,055 ending inventory; average inventory yields about 12.14 | Specify denominator or accept explicitly documented alternatives in a versioned rubric; unchanged question does not define it |
| financebench_id_10420 | AES ROA reference -0.02 is sensitive to numerator choice and rounding | Distinguish consolidated loss -505 from attributable loss -546, average assets 35,663; results approximately -0.01416 versus -0.01531; require an explicit interpretation before approval |
| financebench_id_01351 | American Express tax rate 24.6% to 21.6% | Accept a decrease of 3 percentage points or both correctly ordered rates; do not equate it with a 3% relative decrease |
| financebench_id_01346 | Corning rate 20% to 23% | Accept increase of 3 percentage points or both rates; distinguish 15% relative increase |
| financebench_id_04784 | Walmart margin change reference is 0.2% | Define later-minus-earlier direction and percentage-point units; total-revenue calculation is about +0.18 percentage points, rounded +0.2 |
| financebench_id_01858 | Dividend-trend question omits an as-of date | Reference 65-year statement is filing-time specific; define time scope or allow appropriate evidence without silently forcing one filing |
| financebench_id_00839 | Similar-company CEO experience requires interpretation | Require prior CEO role plus supported retail-business comparison; do not grade by exact wording |
| financebench_id_00382 | Question requests region, reference adds approximately 90% | Region is the essential answer; independently verify any asserted share, but do not require an unasked percentage |
| financebench_id_00941 | Several securities/rates/maturities are required | Use a complete set rubric; matching the first numeric token is inadequate |
| financebench_id_00746 | Negative claim about registered debt securities | Require scoped securities-registration evidence; lack of a retrieved match is not proof of absence |

Findings are based on reference/question inspection and the specific excerpts
listed above. Other narrative/calculation cases remain pending evidence review.
No reviewed status should be inferred from a suggested rubric in the ledger.

## Scoring contract to implement after reference review

1. **Signed numeric values:** retain negative signs/accounting parentheses;
   distinguish units and currency; never choose a fiscal year as the answer.
2. **Ratios:** specify numerator, denominator, period, decimal-versus-percent
   representation and requested rounding. A universal 0.01 absolute tolerance
   is unsafe for small ratios: it can accept materially wrong answers.
3. **Percent changes:** distinguish relative percent from percentage points and
   require the correct direction. Accept equivalent representations explicitly.
4. **Verdicts:** score the yes/no conclusion separately from mandatory supporting
   claims. Do not accept a contradicting explanation merely because it starts Yes.
5. **Categories and lists:** allow reviewed synonyms, require every essential
   item, and reject contradictory additions. Do not demand incidental reference prose.
6. **Evidence:** distinguish alternative source locations from jointly required
   pages/operands; report any-page hits separately from evidence completeness.
7. **Abstentions:** answerable cases remain incorrect if unanswered; genuinely
   unanswerable safety cases need a separate labelled set.

The numeric subset now has a standalone implementation (see below), not a
replacement for the legacy scorer. Non-numeric rules remain proposals.
Keep original-11 legacy scores intact and version any new grading policy. Do not
present rescoring gains as model improvements or mix grading policies silently.

## Artifacts and remaining work

- `evaluation/drafts/rubric_review_20261025.json`: 50 entries, all unapproved for
  new scoring, with source/dataset hashes and pending review criteria.
- `scripts/prepare_rubric_review.py`: regenerates a new ledger, refuses overwrites
  and checks original membership plus the source-audit hash.
- New triage tests: 2 passed. No full-suite rerun was needed for the ledger pass.

Next: finish source/calculation review for all additions, record explicit
dispositions for ambiguity/duplicates, implement versioned rubric scoring with
synthetic tests, then freeze a reviewed dataset. Only then run live generation
with original/addition/combined results separated. Attribution/redistribution
review also remains open. Do not publish the copied draft as cleared content.

## Numeric scoring implementation — 2026-10-25

`src/rag_system/evaluation/numeric_rubrics.py` implements `numeric-rubric-v1`.
It is deliberately not connected to the evaluation runner or draft loader yet.

- Explicit reviewed-reference gate: unreviewed rubrics return `blocked`.
- Decimal arithmetic, signed values and accounting parentheses.
- USD million/billion conversion into base dollars.
- Distinct ratio, percent and percentage-point units; percentage-to-ratio
  conversion requires explicit permission in the rubric.
- Explicit decimal-place rounding using ROUND_HALF_UP rather than the legacy
  blanket 0.01 minimum tolerance.
- Four outcomes: correct, incorrect, needs_review and blocked. Ambiguous prose,
  multiple values and missing/conflicting units require review. No first-number
  selection or hidden LLM judge is used.

This first version accepts scalar answer strings only (optionally trailing source
labels). Natural-language extraction, claim/list scoring, evidence sufficiency and
runner aggregation are not implemented. A needs_review result must never be
silently counted as a pass or omitted to inflate accuracy. Human-reviewed rubric
approval remains a process requirement, not something a boolean can establish.

Validation: 18 new numeric tests; full suite 160 passed with two upstream warnings.
Original reference data, legacy scorer and saved scores are unchanged. Next is
completing source/calculation review and non-numeric rubrics, then explicit versioned
runner integration before any expanded live accuracy score.
