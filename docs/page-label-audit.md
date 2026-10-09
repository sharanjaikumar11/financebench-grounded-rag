# PDF page-label audit

Labels refer to one-based physical PDF pages. The questions and expected answers
are unchanged. Corrections below were checked against extracted source text,
including financial row labels and period context, not just matching numbers.
This is an evaluation-data correction, not evidence of improved generation.

| Case | Previous pages | Audited pages | Source evidence |
| --- | --- | --- | --- |
| 3M 2018 capex | 46,47 | 46,60 | Purchases of PP&E: (1,577), 2018, millions; p60 cash flow statement |
| 3M 2018 net PP&E | 58,59 | 58,81 | Net PP&E 8,738 million; balance sheet and supplemental balance sheet note |
| Amazon 2019 income | 38,39 | unchanged | Net income 11,588; 2019 column |
| Best Buy 2019 inventory | 51,52 | 52 | Merchandise inventories 5,409 |
| Boeing 2018 PP&E | 51,52 | 52,85 | Net PP&E 12,645; balance sheet and PP&E note |
| Costco 2021 assets | 38,39 | 38,64 | Total assets 59,268; balance sheet and segment total |
| JPMorgan Q2 2022 | 20,21 | 21 | Three months ended June 30: CIB 3,725 versus CCB 3,100, CB 994, AWM 1,004, Corporate (174) |
| Microsoft 2016 COGS | 51,52 | 52 | Total cost of revenue 32,780 |
| PepsiCo 2021 capex | 63,64 | 53,63,71 | Capital spending 4,625 million; cash-flow reconciliation, cash flows and segment total |
| Verizon 2021 derivatives | 47 | 85 | Outstanding notionals: cross currency 32,502, interest rate 19,779, forward starting 1,000, FX forwards 932 |

3M capital-intensity remains without a page label: its qualitative criterion needs
separate adjudication. The $8.70 billion PP&E reference is approximate; the source
reports $8.738 billion. It remains unchanged for benchmark continuity.

Page overlap still does not prove that the cited chunk supports a claim, and this
list is not an exhaustive list of every valid supporting page. Keep historical
scores associated with their original label version; rerun both configurations
under the audited labels for a fair comparison.

Rescoring the saved comparison evidence (no new retrieval or generation) changes
baseline expected-page recall from 7/10 to 9/10, and reranked recall from 5/10 to
6/10. This is solely a label correction. It does not demonstrate a retrieval or
answer-accuracy improvement; the reranker remains disabled by default.
