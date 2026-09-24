# Technical decisions

## Embeddings

`all-MiniLM-L6-v2` is used locally for embeddings. It removes embedding API rate limits during corpus indexing and produces 384-dimensional vectors. The provider loads the model from the local Hugging Face cache only, so retrieval and evaluation do not silently depend on network access. Gemini remains restricted to grounded answer generation.

## Vector store

SQLite stores vectors and provenance locally. SQLite FTS5 provides keyword candidates for hybrid retrieval. This keeps the supplied FinanceBench corpus reproducible without hosted vector infrastructure.

## Chunking

Both fixed-token (200 tokens, 40 overlap) and page/section-aware strategies were indexed separately. Both retrieved all three evaluated expected filings at K=3, K=5, and K=10 after filing metadata filtering. Fixed-token is the API default because it provides a stable overlapping context window; section-aware remains available for comparison.

## Grounding

The generation prompt restricts answers to retrieved sources, requires citation labels, and returns `INSUFFICIENT_CONTEXT` if evidence is absent or citations are invalid. It explicitly treats financial-statement tables as evidence: a supported answer must connect the row label, relevant column/date, reported unit, and value. Adjacent retrieved chunks may jointly establish a table header and its row.

## Retrieval improvements

Dense-only fixed-token retrieval scored 33.3% recall@10 on the initial three FinanceBench cases because similar filings from incorrect years ranked highly. Exact filing metadata filtering increased recall@10 to 100%. Hybrid retrieval is implemented and uses reciprocal-rank fusion of dense and FTS5 results.

## Financial-statement retrieval robustness

Filing selection remains conservative: a document filter is applied only when the company and reporting period identify one indexed filing. Questions that explicitly name a quarter prefer the matching 10-Q. Annual questions prefer a matching 10-K when both annual and quarterly filings exist. Comparative annual questions prefer the latest stated fiscal year, since that filing normally contains the comparison period.

For retrieval only, common financial-language variants expand to standard statement terminology (for example, capital expenditure to property-and-equipment purchases and cost of goods sold to cost of revenue or sales). The system does not expand the answer prompt or hard-code company-specific answers.

Once scoped to a single filing, hybrid retrieval considers all of that filing's chunks before selecting anchors. A generic financial-keyword score promotes relevant statement rows over incidental narrative mentions. The final anchors are diversified across nearby chunk positions, and one neighboring chunk on each side is then included as context. This preserves table headers and related rows without filling the answer context with repeated fragments.

## Availability and citation usability

Gemini generation uses temperature zero and a configurable `GEMINI_THINKING_LEVEL` (default `minimal`) to provide enough reasoning capacity for table interpretation. If the configured primary model returns a temporary capacity error (such as HTTP 503), the application retries once using an optional separately configured fallback model. Other failures are surfaced as a clear error instead of being represented as an unsupported answer.

The Streamlit demo retains citation objects and renders them as local `file:///...#page=N` links when the referenced FinanceBench PDF is present in the source directory. This makes the cited page directly inspectable while retaining a plain-text citation fallback when the local file is unavailable.
