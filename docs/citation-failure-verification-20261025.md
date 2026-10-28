# Citation failure verification — 25 October 2026

## Scope and result

Reviewed **all 16 citation-location failures** from `generation_50_repair_excerpts_20261025.json`: **8 supported alternative citations, 2 partially supported answers, and 6 abstentions with no citation**.

The original strict score remains **34/50 (68%)**. This audit finds incomplete reference coverage; it does not demonstrate a new generation improvement or 90–95% citation accuracy. The other 34 location passes have not undergone full semantic review here, so a full semantic citation score is not available.

Source collection SHA-256: `4af43630c2c1812639aa97a52cdf2870efe8d2cc3240748494b905794a96f9ed`.

## Ten answers with citations

Page numbers below are **physical PDF pages (1-based)**; printed page labels may differ. Adjacent pages included in a citation do not necessarily support a claim.

| Case / topic | Actual cited file and pages | Reference file and pages | Review |
|---|---|---|---|
| financebench_demo_jpmorgan_2022q2_highest_net_income: JPMorgan | JPMORGAN_2022Q2_10Q.pdf — 177 | JPMORGAN_2022Q2_10Q.pdf — 21 | Supported alternative |
| financebench_id_01858: 3M dividends | 3M_2023Q2_10Q.pdf — 73 | 3M_2023Q2_10Q.pdf — 62 | Supported alternative |
| financebench_id_01279: AMD cash flow | AMD_2022_10K.pdf — 51 | AMD_2022_10K.pdf — 58 | Supported alternative |
| financebench_id_01346: Corning tax rate | CORNING_2022_10K.pdf — 76, 77 | CORNING_2022_10K.pdf — 24 | Supported alternative |
| financebench_id_00839: Foot Locker CEO | FOOTLOCKER_2023_10K.pdf — 18 | FOOTLOCKER_2022_8K_dated_2022-08-19.pdf — 2 | Partial; not accepted as full support |
| financebench_id_00382: MGM EBITDAR | MGMRESORTS_2022_10K.pdf — 99, 100 | MGMRESORTS_2022Q4_EARNINGS.pdf — 13 | Supported alternative |
| financebench_id_00302: Pfizer PP&E | PFIZER_2021_10K.pdf — 88, 89 | PFIZER_2021_10K.pdf — 59 | Supported alternative |
| financebench_id_00566: Verizon debt | VERIZON_2022_10K.pdf — 55, 56 | VERIZON_2022_10K.pdf — 77 | Supported alternative |
| financebench_id_04784: Walmart margin | WALMART_2019_10K.pdf — 34 | WALMART_2019_10K.pdf — 48 | Supported alternative |
| financebench_id_00540: AES inventory | AES_2022_10K.pdf — 140 | AES_2022_10K.pdf — 130, 132 | Partial; not accepted as full support |

### JPMorgan — financebench_demo_jpmorgan_2022q2_highest_net_income

Q2 2022 segment table reports net income (millions): CCB 3,100; CIB 3,725; Commercial 994; AWM 1,004; Corporate -174. The cited page supports the maximum and amount.

Source: [JPMORGAN_2022Q2_10Q.pdf](../data/raw/financebench/pdfs/JPMORGAN_2022Q2_10Q.pdf#page=177).

### 3M dividends — financebench_id_01858

The page states 65 consecutive years of dividend increases and describes the February and May 2023 dividends. This supports the answer's explicit as-of-2023 qualification.

Source: [3M_2023Q2_10Q.pdf](../data/raw/financebench/pdfs/3M_2023Q2_10Q.pdf#page=73).

### AMD cash flow — financebench_id_01279

FY2022 net cash flows (millions) are operating 3,565, investing 1,999 and financing -3,264. All three amounts and the comparison are supported.

Source: [AMD_2022_10K.pdf](../data/raw/financebench/pdfs/AMD_2022_10K.pdf#page=51).

### Corning tax rate — financebench_id_01346

The tax reconciliation reports 22.9% for 2022 and 20.2% for 2021, a 2.7 percentage-point increase. The reference uses rounded rates; this is a precision difference, not fabricated evidence. Cited page 76 is unnecessary.

Source: [CORNING_2022_10K.pdf](../data/raw/financebench/pdfs/CORNING_2022_10K.pdf#page=77).

### Foot Locker CEO — financebench_id_00839

The page confirms Mary Dillon was Ulta Beauty CEO from July 2013 through June 2021. It does not establish that Ulta is a similar company to Foot Locker. Prior CEO experience is supported; the full affirmative comparison remains unresolved.

Source: [FOOTLOCKER_2023_10K.pdf](../data/raw/financebench/pdfs/FOOTLOCKER_2023_10K.pdf#page=18).

### MGM EBITDAR — financebench_id_00382

Page 99 defines the segments and Adjusted Property EBITDAR. Page 100 reports FY2022 amounts (thousands): Las Vegas Strip 3,142,308; Regional Operations 1,294,630; MGM China -203,136. The 10-K supports the answer although the reference names the earnings release.

Source: [MGMRESORTS_2022_10K.pdf](../data/raw/financebench/pdfs/MGMRESORTS_2022_10K.pdf#page=99).

### Pfizer PP&E — financebench_id_00302

The PP&E note reports net PP&E (millions) of 14,882 in 2021 versus 13,745 in 2020. The increase is supported. Cited page 89 concerns intangible assets and is unnecessary.

Source: [PFIZER_2021_10K.pdf](../data/raw/financebench/pdfs/PFIZER_2021_10K.pdf#page=88).

### Verizon debt — financebench_id_00566

For 2022, current debt 9,963 plus long-term debt 140,676 equals 150,639 million. For 2021, 7,443 plus 143,425 equals 150,868 million. The decrease is supported under the answer's explicit definition. Cited page 55 is unnecessary.

Source: [VERIZON_2022_10K.pdf](../data/raw/financebench/pdfs/VERIZON_2022_10K.pdf#page=56).

### Walmart margin — financebench_id_04784

The operating income percentage of net sales row reports 4.3% for 2019 and 4.1% for 2018, supporting the 0.2 percentage-point change. Caveat: these displayed margins use net sales, not total revenue. Using the same page's operating income and total revenue gives about 0.184 percentage points, also rounding to 0.2. This citation supports the stated calculation; denominator wording should be explicit.

Source: [WALMART_2019_10K.pdf](../data/raw/financebench/pdfs/WALMART_2019_10K.pdf#page=34).

### AES inventory — financebench_id_00540

The accounting policy describes fuel/raw materials and spare parts used for generation and maintenance. It does not establish that conventional inventory management or turnover is meaningless. The inventory description is supported; the categorical conclusion is not established by this citation.

Source: [AES_2022_10K.pdf](../data/raw/financebench/pdfs/AES_2022_10K.pdf#page=140).


## Six abstentions

These returned `INSUFFICIENT_CONTEXT` with no citation. There is no emitted citation to validate. Do not treat rejected intermediate answers as successful outputs or mark these cases correct based on available reference text.

| Case | Question topic | Recorded attempt statuses |
|---|---|---|
| financebench_id_00499 | 3M capital intensity | model_abstention |
| financebench_id_10420 | AES ROA | model_abstention |
| financebench_id_07507 | Adobe operating-income growth | quote_not_in_source → model_abstention |
| financebench_id_01079 | AMCOR acquisitions | model_abstention |
| financebench_id_10499 | Kraft Heinz inventory turnover | quote_not_in_source → model_abstention |
| financebench_id_07966 | Activision capex/revenue | quote_not_in_source → model_abstention |

## Recommended follow-up

1. Have a reviewer approve supported alternative pages as evaluation-only annotations, retaining original labels and reporting strict location results separately.
2. Require additional evidence for company similarity in Foot Locker and avoid the unsupported categorical inventory conclusion for AES.
3. Diagnose the six abstentions separately: retrieve complete operands, periods and cross-year evidence; inspect rejected quotes without relaxing evidence checks.
4. Review the remaining 34 location passes before claiming full semantic citation accuracy. Keep the same 50 questions and denominator for comparisons.

No answer values or case-specific retrieval rules were added to the application. No live evaluation was rerun. This is an optional expanded-evaluation audit, separate from the lead's original submission results.

Machine-readable evidence, original outputs, decisions and PDF hashes: [full audit](../evaluation/results/citation_failure_verification_20261025.json).
