# Failure analysis

## Retrieval baseline

The unfiltered dense fixed-token baseline returned the expected filing for 1 of 3 cases at K=10 (33.3%). Similar company filings from wrong fiscal years competed with the requested filing.

## Correction and result

The system infers a `document_name` filter only when a question clearly names both company and fiscal year. Hybrid retrieval then combines local dense retrieval and SQLite FTS5 BM25 ranking. This configuration achieved 3 of 3 expected-document retrieval hits at K=3, K=5, and K=10 for both tested chunking strategies.

## Subsequent failure modes and mitigations

The initial metadata rule did not distinguish a question about a fiscal quarter from an annual question, and an annual filing could compete with the relevant 10-Q. Filing inference now detects an explicit quarter and selects a uniquely matching quarterly filing. For annual questions where both filing types exist, it prefers the uniquely matching 10-K. The rule is only applied when the indexed metadata makes the choice unambiguous.

Financial-statement questions also exposed a ranking problem: a narrative mention of a metric could outrank the statement row containing the requested value. The retrieval query now expands generic financial synonyms, table candidates receive a generic keyword-and-numeric relevance boost, and anchors are diversified before adjacent context is added. These rules are based on statement structure rather than a company or benchmark question.

Some answers depend on a table header and its value row being in adjacent chunks. The generation prompt now instructs the model to combine directly supplied row, column, date, and unit evidence. This reduces unnecessary `INSUFFICIENT_CONTEXT` responses while retaining the requirement that every answer be supported by cited retrieved sources.

Generation evaluation identified a separate abstention pattern: answer-bearing rows were retrieved, but the model sometimes treated standard reporting terminology, signed cash-flow amounts, or a table comparison as insufficient evidence. The prompt now explicitly permits source-supported financial equivalents (such as PP&E purchases for capital expenditure), the magnitude of a parenthesized expenditure, consolidated net income when no separate attribution is reported, and direct maximum/minimum comparisons. These are generic financial-statement interpretation rules, not stored answers or company-specific exceptions.

Gemini capacity errors (for example, HTTP 503) previously ended the request immediately. The application now retries an optional fallback model only for temporary capacity errors and otherwise displays a clear failure message. This is an availability improvement, not evidence that a generated answer is grounded.

The demo previously displayed source labels without a direct path to inspect the evidence. Citations now link to a loopback-only local PDF server and its first cited page when the file exists. The link is a usability aid; citation validity continues to depend on the retrieved evidence.

## Generation limitation

Grounded answer evaluation depends on a Gemini API key being available in the same terminal that runs the evaluation. The generator is configured with temperature zero and returns `INSUFFICIENT_CONTEXT` rather than fabricate an answer or citation when retrieved evidence is insufficient.

The 3-of-3 retrieval result above is the original small evaluation and must not be interpreted as a measurement of the subsequent routing and table-retrieval changes. The expanded 11-case run subsequently measured 100% expected-filing recall (11/11), 45.45% answer accuracy (5/11), 54.55% citation accuracy (6/11), and 100% grounding. These metrics are recorded in the experiment report and should be rerun when the generator model or prompts change.
