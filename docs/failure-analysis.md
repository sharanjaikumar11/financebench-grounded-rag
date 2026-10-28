# Failure analysis

## Current full-run findings — 28 October 2026

Latest collection: `generation_50_20261028_142603.json`. All 50 requests completed
without provider errors; 45 answered and five abstained. Citation-location matches
are 36/50. Agent evidence review classifies 42 supported, six unsuccessful and two
unresolved; final answer accuracy is pending. The older measurements below are history.

| Failure | Current handling / limitation |
| --- | --- |
| 3M capital intensity; Amazon shareholder income | Model abstains; selected evidence and requested inference/attribution still need work. |
| Adobe operating-income growth | Both attempts fail exact quote membership. |
| Activision capex percentage | Quote failure then operand/evidence-link failure; success in targeted v5 did not repeat in full run. |
| Verizon debt direction | Correct totals accompany an incorrect increase claim; new narrow guard rejects both attempts, yielding abstention. |
| AMD quick ratio | Numerator includes prepaid/other current assets; source supports 1.57 rather than 1.77. Verdict alone does not make the answer correct. |
| AES ROA | Consolidated versus attributable net income gives different rounded ratios; definition unresolved. |
| AES inventory turnover | Average versus closing inventory gives 12.14 versus about 9.5; question does not specify convention. |
| PayPal reference discrepancy | Source supports positive working capital of 12,416 million; reference explanation says 1.6 billion. Preserve both and document source-based decision. |

PepsiCo capex and American Express tax rate recovered in the latest run. Full-run
variation shows why repeated generation should not be used to select only favorable
scores. One repair attempt does not guarantee recovery. No company-specific answers,
benchmark relabelling or weakened quote validation were introduced.

Other addressed failures include wrong-period filing routing, narrative passages
outranking statement rows, lost neighboring headers, signed numeric parsing,
mixed-case arithmetic identifiers, insufficient structured-output budget, and
unhelpful provider errors. Source links now serve actual PDFs over loopback HTTP.
Arithmetic and provenance validation still do not prove every claim's meaning.

Read [case-level answer review](answer-review-20261028.md) for the scoring rubric.
The [demo smoke checks](demo-verification-20261028.md) passed startup, error handling,
saved-answer display and PDF delivery. Fresh live demo generation remains unchecked
because this process has no provider key; do not confuse it with saved-run review.

## Historical development findings

## Retrieval baseline

The unfiltered dense fixed-token baseline returned the expected filing for 1 of 3 cases at K=10 (33.3%). Similar company filings from wrong fiscal years competed with the requested filing.

## Correction and result

The system infers a `document_name` filter only when a question clearly names both company and fiscal year. Hybrid retrieval then combines local dense retrieval and SQLite FTS5 BM25 ranking. This configuration achieved 3 of 3 expected-document retrieval hits at K=3, K=5, and K=10 for both tested chunking strategies.

## Subsequent failure modes and mitigations

The initial metadata rule did not distinguish a question about a fiscal quarter from an annual question, and an annual filing could compete with the relevant 10-Q. Filing inference now detects an explicit quarter and selects a uniquely matching quarterly filing. For annual questions where both filing types exist, it prefers the uniquely matching 10-K. The rule is only applied when the indexed metadata makes the choice unambiguous.

Financial-statement questions also exposed a ranking problem: a narrative mention of a metric could outrank the statement row containing the requested value. The retrieval query now expands generic financial synonyms, table candidates receive a generic keyword-and-numeric relevance boost, and anchors are diversified before adjacent context is added. These rules are based on statement structure rather than a company or benchmark question.

Some answers depend on a table header and its value row being in adjacent chunks. The generation prompt now instructs the model to combine directly supplied row, column, date, and unit evidence. This reduces unnecessary `INSUFFICIENT_CONTEXT` responses while retaining the requirement that every answer be supported by cited retrieved sources.

Generation evaluation identified unnecessary abstentions on financial aliases,
signed cash-flow amounts and comparisons. Prompts permit source-supported financial
equivalents and expenditure magnitudes, but preserve the requested income basis:
consolidated income is not a substitute when shareholder attribution is requested.
These are generic interpretation rules, not company-specific exceptions.

Gemini capacity errors (for example, HTTP 503) previously ended the request immediately. The application now retries an optional fallback model only for temporary capacity errors and otherwise displays a clear failure message. This is an availability improvement, not evidence that a generated answer is grounded.

The demo previously displayed source labels without a direct path to inspect the evidence. Citations now link to a loopback-only local PDF server and its first cited page when the file exists. The link is a usability aid; citation validity continues to depend on the retrieved evidence.

## Generation limitation

Grounded answer evaluation depends on a Gemini API key being available in the same terminal that runs the evaluation. The generator is configured with temperature zero and returns `INSUFFICIENT_CONTEXT` rather than fabricate an answer or citation when retrieved evidence is insufficient.

The 3-of-3 result above is historical, not a measurement of subsequent changes.
The historical saved row-matching generation run measured 9/11 answer and citation
accuracy, 11/11 document recall and 10/10 labelled-page recall. See the experiment
report and published summaries for remaining failed case IDs. Two abstentions
remain; improved page coverage does not guarantee generation success.

Structured output exposed another failure: the model abbreviated table rows
into non-verbatim quotes. Repair now identifies failed evidence entries and asks
for full contiguous rows and separate headers. Exact validation remains strict.
Statement/row scoring helped retrieval find the missing asset balance, but did not
increase aggregate generation accuracy in the latest run. Do not infer a causal
accuracy gain from retrieval alone.
