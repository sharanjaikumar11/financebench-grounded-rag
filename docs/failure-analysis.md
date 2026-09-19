# Failure analysis

## Retrieval baseline

The unfiltered dense fixed-token baseline returned the expected filing for 1 of 3 cases at K=10 (33.3%). Similar company filings from wrong fiscal years competed with the requested filing.

## Correction and result

The system infers a `document_name` filter only when a question clearly names both company and fiscal year. Hybrid retrieval then combines local dense retrieval and SQLite FTS5 BM25 ranking. This configuration achieved 3 of 3 expected-document retrieval hits at K=3, K=5, and K=10 for both tested chunking strategies.

## Generation limitation

Grounded answer evaluation depends on a Gemini API key being available in the same terminal that runs the evaluation. The generator is configured with temperature zero and returns `INSUFFICIENT_CONTEXT` rather than fabricate an answer or citation when retrieved evidence is insufficient.
