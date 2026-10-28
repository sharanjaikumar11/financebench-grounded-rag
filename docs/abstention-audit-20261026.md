# Eleven-abstention audit and bounded fixes

Reviewed all 11 abstentions in `generation_50_metric_identity.json` using saved
provider replies and the actual source chunks selected for generation. This is
an optional improvement audit, separate from lead-required submission results.

| Case/topic | Evidence finding | Main next action |
|---|---|---|
| 3M capital intensity (00499) | Selected context includes capex and net sales, but no agreed criterion establishing capital intensity. | Resolve qualitative rubric; do not force a yes/no from an arbitrary threshold. |
| JPMorgan segment maximum | First JSON is malformed; repair invents currency symbols/joins excerpts. Comparison table is available. | Improve schema/quote copying; do not accept reconstructed quotes. |
| AES ROA (10420) | Selected context is accounting-policy and financing notes; required net income and total-assets rows are missing. | Retrieve complete statement operands. |
| Adobe operating-income growth (07507) | Selected income-statement chunk ends at the start of cost of revenue. The next retrieved chunk contains operating income but was excluded. Provider invented missing rows. | Preserve retrieved numeric rows; implemented below. |
| AMCOR acquisitions (01079) | Context predominantly contains non-GAAP reconciliation/segment discussions, not complete acquisition coverage for all three years. | Improve transaction-note retrieval and assess reference completeness. |
| American Express tax rate (01351) | S4 has the rate row but not its year header; S6 explicitly states both rates and years in one sentence. Model repeatedly attaches a nonexistent header to S4. | Cite the narrative sentence or the actual separate header source. |
| Coca-Cola payout (06272) | Selected context contains consolidated income and dividends, not the required attributable-income row; the relevant row is absent from the saved retrieved pool. | Retrieval must find the requested income basis; do not substitute consolidated income. |
| Kraft Heinz turnover (10499) | Inventory is present; S2 starts below the main COGS row. S7 contains a consolidating COGS row, but quotes remove an intervening dash. | Preserve full table row and period; do not infer COGS from other expense rows. |
| Verizon debt (00566) | Both debt components are available. Model treats computed totals as directly quoted operands. | Sum quoted components inside the expression; repair guidance updated. |
| AES inventory (00540) | Balance-sheet chunks start below the inventory rows; inventory accounting policy alone does not provide balances. Provider invents inventory values and mishandles the cost sign. | Retrieve actual inventory balances; keep sign and operand-membership checks. |
| Activision capex/revenue (07966) | Revenue is present, but selected chunks do not contain the required capex series. | Retrieve cash-flow capex rows with year headers. |

Five cases abstained directly; six exhausted validation repair. These causes overlap:
validation failure may be a symptom of missing context, not just formatting.

## Implemented generic fixes

`NUMERIC_ROW_COVERAGE=1` reserves at most three existing source slots for distinct
requested concepts followed by figures. It uses generic financial terminology,
not company IDs, page labels or benchmark answers. It selects only from retrieved
chunks and retains the nine-source budget. Defaults off pending live evaluation.
It does not retrieve missing documents, parse table columns or guarantee row relevance.

Repair instructions now explain that derived totals must be computed from quoted
components, not passed as supposedly quoted operands. Quote repair also clarifies
separate-source headers, complete narrative evidence and preservation of currency
symbols as they actually appear.

## Validation

- 221 unit tests passed; Ruff passed on changed code and tests.
- Saved-pool replay reproduced the original source IDs for every baseline case
  before applying the new rule.
- Adobe's numeric operating-income row is retained with the rule enabled.
- Selected-context expected-page coverage remains **45/49**, with no page gains
  or losses. This does not prove complete evidence support for those 45 cases.
- Results: `evaluation/results/numeric_row_coverage_replay_20261026.json`.

No API calls or new answers were generated. Prompt-repair improvements cannot be
measured by replaying unchanged responses. Answer accuracy remains unadjudicated.

## Next controlled live run

Use a keyed PowerShell terminal with the same Gemini configuration:

```powershell
$env:CALCULATION_VALIDATION = "1"
$env:COMPARISON_VALIDATION = "1"
$env:METRIC_IDENTITY_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
$env:NUMERIC_ROW_COVERAGE = "1"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
python scripts\run_50_generation_collection.py --output evaluation\results\generation_50_numeric_row_coverage.json
```

Compare against the metric-identity run. Missing retrieval evidence and qualitative
rubric ambiguities listed above remain open; they are not claimed fixed here.
