# Technical decisions

Updated 28 October 2026 to cover the complete implemented project and latest
50-case review. Older small-set comparisons below explain earlier choices.

## Current generation and validation choices

Use structured evidence for the evaluated profile: exact quotes, source IDs,
periods, units and bounded arithmetic operands. Decimal arithmetic renders results
instead of trusting model-calculated numbers; expressions allow only a restricted
AST, not Python eval. Signed outflows retain their sign, with explicit negation
for magnitudes. Case-sensitive ASCII operand names may use mixed case within a
20-character bound. Verified candidate quote indices guide repair without silently
reassigning evidence. One repair attempt keeps latency and API cost bounded.

Period and metric-identity checks catch selected wrong-year or attribution errors.
Extrema validation compares evidence-linked candidates. Acquisition absence needs
explicit evidence. A narrow from/to direction check blocks numerically contradictory
increase/decrease prose. None of these checks is a general semantic-entailment model.

Structured Gemini output uses a 4,096-token cap to leave room for quotes/operands;
text output remains 256. Temperature zero and minimal thinking are the recorded
evaluation settings, not guarantees of determinism or best accuracy. Provider
diagnostics store bounded error categories/status codes, model and finish reason,
not raw exception messages. Capacity fallback and evidence repair are distinct.

Five anchors were used in the 50-case collection; the demo/API default remains
three. Up to nine sources reach generation. Operand-aware context selection and
neighbor expansion help preserve required rows, but do not reconstruct table layout.
Table-aware corpus indexing is not active, and no separate cross-encoder is enabled.

## Current measured trade-off

The latest full run achieves 100% filing recall, 95.92% labelled-page recall and
72% citation-location matching. Agent review finds 42/50 source-supported answers,
six unsuccessful cases and two unresolved definitions. Final answer accuracy is
pending; do not call the upper 88% bound achieved accuracy. Conservative validation
can reject answerable cases, while quote membership can still admit incorrect prose.
See [evaluation](experiment-report.md) and [failure analysis](failure-analysis.md).

## Embeddings

`all-MiniLM-L6-v2` is used locally for embeddings. It removes embedding API rate limits during corpus indexing and produces 384-dimensional vectors. The provider loads the model from the local Hugging Face cache only, so retrieval and evaluation do not silently depend on network access. Gemini remains restricted to grounded answer generation.

## Vector store

SQLite stores vectors and provenance locally. SQLite FTS5 provides keyword candidates for hybrid retrieval. This keeps the supplied FinanceBench corpus reproducible without hosted vector infrastructure.

## Chunking

Both fixed-token and page/section-aware strategies are indexed separately.
The current controlled 11-case K=3 generation comparison scored fixed-token
9/11 answers/citations versus section-aware 7/11 after numeric scorer correction.
The bounded size/overlap comparison supports retaining 200 whitespace tokens
with 40 overlap: 10/10 selected-context page hits, versus 8/10 for 100/40 and
200/0. It ties 300/40 with less context and 200/80 with fewer chunks. These
limited development experiments do not establish global optimality.
See [experiment report](experiment-report.md) and
[sensitivity results](chunk-sensitivity-results.md) for controls and limitations.

## Grounding

The improved evaluation path uses `GROUNDED_OUTPUT_MODE=evidence` and
`STATEMENT_AWARE_RANKING=1`. These are opt-in, not implied by the default setup.
Exact quote membership validates provenance, not semantic entailment. Numeric
answer checking and reference-page overlap also have limited scope.

The generation prompt restricts answers to retrieved sources, requires citation labels, and returns `INSUFFICIENT_CONTEXT` if evidence is absent or citations are invalid. It explicitly treats financial-statement tables as evidence: a supported answer must connect the row label, relevant column/date, reported unit, and value. Adjacent retrieved chunks may jointly establish a table header and its row.

## Retrieval improvements

Dense-only fixed-token retrieval scored 33.3% recall@10 on the initial three FinanceBench cases because similar filings from incorrect years ranked highly. Exact filing metadata filtering increased recall@10 to 100%. Hybrid retrieval is implemented and uses reciprocal-rank fusion of dense and FTS5 results.

## Financial-statement retrieval robustness

Filing selection remains conservative: a document filter is applied only when the company and reporting period identify one indexed filing. Questions that explicitly name a quarter prefer the matching 10-Q. Annual questions prefer a matching 10-K when both annual and quarterly filings exist. Comparative annual questions prefer the latest stated fiscal year, since that filing normally contains the comparison period.

For retrieval only, common financial-language variants expand to standard statement terminology (for example, capital expenditure to property-and-equipment purchases and cost of goods sold to cost of revenue or sales). The system does not expand the answer prompt or hard-code company-specific answers.

Once scoped to a single filing, hybrid retrieval considers all of that filing's chunks before selecting anchors. A generic financial-keyword score promotes relevant statement rows over incidental narrative mentions. The final anchors are diversified across nearby chunk positions, and one neighboring chunk on each side is then included as context. This preserves table headers and related rows without filling the answer context with repeated fragments.

## Availability and citation usability

## When reranking helps

Reranking helps when candidate retrieval finds relevant passages but orders them
poorly. A cross-encoder scores query/passage pairs jointly at additional latency.
Our tested general-purpose MiniLM cross-encoder reduced audited page recall from
9/10 to 6/10, so it is not enabled by default. Generic financial row scoring is a
separate heuristic, not a learned cross-encoder or table-aware extraction.

## Irrelevant context and absent answers

Retrieving the correct document is not enough: the required row, period and unit
must be in context. Evidence mode validates source IDs and verbatim excerpts,
allows one repair attempt, then abstains on invalid evidence. A model may abstain
immediately. Source membership cannot detect all plausible but unsupported claims;
human review or an additional entailment evaluation is needed. Provider failures
are errors, not evidence that a document lacks the answer.

## Scaling the collection by 100x

Measure bottlenecks before migrating. Replace exhaustive local vector scanning
with an approximate-nearest-neighbor index when needed; preserve lexical search
and metadata filters. Add background ingestion, incremental/versioned indexing,
document access controls, storage-backed PDF delivery, monitoring and backups.
Batch embeddings and evaluate latency, memory, retrieval quality and cost under
concurrency. These are proposed production extensions, not implemented claims.

## RAG versus fine-tuning

Prefer RAG for changing, private or source-attributable knowledge: updating the
corpus does not require retraining, and citations expose supporting evidence.
Prefer fine-tuning for stable behavior, formatting, terminology or task patterns
when sufficient quality training examples and evaluations exist. Fine-tuning is
not a reliable replacement for an up-to-date factual store and does not itself
provide provenance. The approaches can be combined; no fine-tuning was performed.

## Availability implementation

Gemini generation uses temperature zero and a configurable `GEMINI_THINKING_LEVEL` (default `minimal`) to provide enough reasoning capacity for table interpretation. If the configured primary model returns a temporary capacity error (such as HTTP 503), the application retries once using an optional separately configured fallback model. Other failures are surfaced as a clear error instead of being represented as an unsupported answer.

The Streamlit demo retains citation objects and, when the referenced FinanceBench PDF is present in the source directory, starts a loopback-only PDF server and renders `http://127.0.0.1:8502/<document>.pdf#page=N` links. This lets the browser open the cited PDF at its first cited page without exposing the source directory through Streamlit's static-file route. A plain-text citation remains when the local PDF is unavailable.
