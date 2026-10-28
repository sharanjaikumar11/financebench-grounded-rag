# Pre-generation issue audit and fixes

Optional improvement work, separate from lead-required submission results.
Baseline: `evaluation/results/generation_50_period_validation.json`.
No generation API calls or full generation evaluation were run during this audit.
Original questions, reference answers and page labels are unchanged.

## Implemented fixes

1. Source-copy repair repeats actual matching source text before the incorrectly
   assigned source, while retaining strict quote membership and period checks.
2. Financial aliases now include capex, cost of products sold, net income (loss),
   shareholder/shareowner attribution and payout terminology.
3. Opt-in `OPERAND_COVERAGE=1` reserves existing retrieval candidates for distinct
   required rows in ROA, inventory turnover, payout and capex/revenue questions.
   Rows near dated consolidated statements take priority over affiliate notes.
   Filing filters and top-K remain in force; no expected values/pages are used.
4. Required-row context preserves available preceding headings and row
   continuations before unrelated neighborhoods, within the nine-source limit.
5. Transaction-note fallback looks for dated acquisition events, rather than
   amortization, contingent-consideration balances or a generic accounting policy.
   For multi-filing questions it considers each filing's leading anchor.
   Acquisition queries expand two neighboring chunks on each side; generation
   reserves event passages and their continuations within the same nine-source
   limit. This increases the retrieved candidate context, not the LLM source cap.
6. Removed conflicting prompt permission to replace explicitly requested
   shareholder-attributable income with consolidated income. Clarified that
   subtracting percentage rates produces a percentage-point difference.

The new coverage flag defaults off. Alias expansion remains under the existing
financial-intent experiment. No embedding model, index or benchmark was replaced.

## Nine abstentions: findings and status

| Topic | Finding and action | Remaining limitation |
|---|---|---|
| 3M capital intensity | Relevant figures exist; preserve safe abstention. | The reference says “No” without an agreed decision criterion. A defensible qualitative rubric is needed. |
| AES ROA | Main statement income/loss and both asset balances now retained, with headings. | Parent-attributable versus consolidated income changes rounding; income basis must be explicit in scoring. |
| Adobe operating-income growth | Required row is present; repair now repeats S1's actual header before S2. | Model compliance needs a targeted live check. |
| AMCOR acquisitions | Investigated ranking of non-GAAP reconciliations and contingent consideration instead of acquisition events; added per-filing transaction fallback. | Reference lists FY2023 events despite a three-year question. Complete multi-year answer coverage still requires review. |
| American Express tax rate | Actual matching source is available and repeated in repair context. | Model source assignment and percentage-point wording need live validation. |
| Coca-Cola payout | Attributable income and cash-flow dividends now both retained. | Cash-flow dividends differ from dividends in equity; model must use the requested basis. |
| Kraft Heinz turnover | Current-year main-statement COGS row and inventories now retained; wrong-year guard stays enabled for evaluation. | Full table-column interpretation is still model-dependent. |
| AES inventory turnover | Main-statement inventory and cost-of-sales rows now retained. | Reference approximately 9.5 uses closing inventory; average inventory gives a different result. Do not silently tune the formula to the reference. |
| Activision capex/revenue | Three-year capex series, revenues and statement headings now retained. | Live generation must preserve outflow signs and average the requested annual ratios. |

## Eight answered citation-location failures

These were inspected against saved provider quotes and selected source text.
This is a diagnostic review, not a completed independent PDF adjudication.

| Topic | Finding |
|---|---|
| 3M dividend trend | Cites multiple historical filings and a 2023 quarterly statement; quoted consecutive-year counts support the trend but differ from the labelled filing/page. |
| AMD cash-flow activity | Quotes operating, investing and financing values on an alternative page. |
| Corning tax rate | Quotes precise 22.9% and 20.2% rates; reference rounds them to 23% and 20%. Difference is 2.7 percentage points. |
| Foot Locker CEO | Quotes the prior CEO employment dates on an alternative page; similarity-of-business reasoning remains a semantic judgment. |
| MGM regional EBITDAR | Quotes the regional table on an alternative page; selected region matches the reference. |
| Pfizer PP&E | Quotes both balances and header on an alternative page and computes their difference. |
| Verizon debt | Sums the quoted current and long-term debt components on an alternative page. |
| Walmart margin | Quotes the rate series on an alternative page. Existing answer says percent for a difference of rates; prompt guidance now distinguishes percentage points. |

Do not rewrite labels or force reference pages to improve strict location scores.
Supporting alternative citations must be reviewed separately, with the original
score retained. Quote membership alone does not establish full entailment.

## Offline validation and boundaries

- 238 unit tests pass; Ruff passes on changed Python files.
- The 50-case alias retrieval check retained 50/50 expected-filing hits and
  45/49 labelled-page hits (91.84%), including in selected generation context.
- The targeted statement-coverage check found labelled pages for all eight
  page-labelled abstention cases (3M capital intensity has no page label).
- Actual selected text was inspected: both required row families are present for
  AES ROA, Coca-Cola payout, Kraft Heinz turnover, AES inventory and Activision.
  AES's split asset row retains its second value through adjacent context.
- Acquisition experiments exposed a Best Buy regression. Broad acquisition
  score boosts were removed; use the separately verified transaction run below,
  not intermediate experiment results, for the final acquisition check.
- Final acquisition retrieval and selected context preserve the labelled evidence
  for both AMCOR and Best Buy (2/2). AMCOR's actual selected text now includes
  the Czech Republic, Shanghai and New Zealand acquisition descriptions; the
  earlier transaction retrieval fix alone did not retain all three in generation.

Artifacts under `evaluation/results/`:

- `retrieval_alias_audit_20261026.json`: completed 50-case alias check.
- `retrieval_operand_targeted_v2_20261026.json`: targeted retrieval check.
- `operand_context_final_20261026.json`: current context selection inspection.
- `retrieval_transactions_context_20261026.json`: final acquisition retrieval/context check.
- `transaction_context_final_review_20261026.json`: inspection of retained event descriptions.
- `source_window_repair_audit_20261026.json`: all seven saved quote-failure attempts.

These checks were performed in stages; they are not one new 50-case generation
run or a new answer/citation accuracy score. Intermediate prototypes are retained
for traceability and must not be presented as final results.

## Before another full generation evaluation

Run targeted generation on the repaired cases to check model compliance, and
agree the ambiguous scoring bases above. This process has no Gemini key, so
live recovery cannot be verified here. The remaining issues are not honestly
described as “all fixed”: semantic review, rubric ambiguity and provider behavior
remain. Keep abstention when required evidence or interpretation is unresolved.
