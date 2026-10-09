# Experiment report

## Current measured results

The local `row_matching_generation.json` evaluates the unchanged 11-case set:

| Metric | Result | Meaning |
| --- | ---: | --- |
| Expected-document recall | 11/11 | Correct filing retrieved |
| Expected-page recall | 10/10 labelled | Reference-page overlap in retrieved context |
| Answer accuracy | 9/11 (81.82%) | Deterministic answer checker |
| Citation accuracy | 9/11 (81.82%) | Expected document/page overlap |
| Grounding rate | 100% | Source membership; abstentions count as grounded |
| Abstention rate | 2/11 | No supported answer returned |

Git-reviewable summaries are in `evaluation/published/`. Raw reports remain local
because they contain source text and provider output. Summary hashes identify the
source artifacts. Legacy reports do not record model revisions or all environment
settings, so identical configurations cannot be established from artifacts alone.

## Generation and context experiments

| Local artifact | Answer accuracy | Citation accuracy |
| --- | ---: | ---: |
| evidence_quote_repair.json | 8/11 | 7/11 |
| statement_quote_repair.json | 9/11 | 9/11 |
| row_matching_generation.json | 9/11 | 9/11 |

The changes introduce separate verbatim excerpts, failure-specific repair, then
statement/row relevance preferences. Sequential runs are development evidence,
not isolated causal ablations: provider variability and incomplete configuration
recording limit attribution. The last retrieval change did not increase aggregate
generation accuracy. Repeat runs and held-out questions are still needed.

## Retrieval experiments

Dense unfiltered retrieval scored 1/3 at K=10 on the original three questions.
Metadata-filtered fixed-token and section-aware retrieval scored 3/3 expected-filing
recall at K=3, 5 and 10. These small results do not establish answer-quality parity.

On the expanded set, saved full-context evidence rescored after the page-label
audit gave 9/10 expected-page recall for hybrid retrieval and 6/10 for the optional
MiniLM cross-encoder. The cross-encoder remains disabled by default. Label
corrections are not model improvements. Earlier pre-audit results were 7/10 and 5/10.

The October 9 paired row-matching test used the same questions, index and full
neighbor context: expected-page recall rose from 9/10 to 10/10 without page-hit
regressions. The formerly missing net PP&E row was retrieved. This does not prove
entailment or unseen-question performance.

## Chunking selection and remaining experiment gap

Both fixed-token and section-aware implementations exist. The demo uses 200
whitespace-delimited tokens with 40 overlap, not model-token counts. Overlap and
neighbors help reconnect headers and rows; page/section boundaries avoid some
cross-section mixing. Both can still split financial tables.

The three-case document-recall comparison is too weak to show that 200/40 is
optimal. A chunk-size/overlap sensitivity experiment and an answer-quality
comparison of both strategies on the same expanded cases remain pending.
Do not describe this requirement as fully validated. Partial table-aware indexing
was stopped; that index is not a completed comparison or the demo default.

## Reproduction and artifact hygiene

Use README commands with `GROUNDED_OUTPUT_MODE=evidence` and
`STATEMENT_AWARE_RANKING=1` for the improved path. Preserve separate output names.
The retrieval-only runner truncates neighbor-expanded results to K; do not compare
its page coverage directly with full-context generation reports.

The legacy `fixed_token_hybrid_top_k_3_metadata_filtered.json` currently reports
11 cases and 27.27% filing recall. It is not the authoritative current result;
do not relabel it or overwrite it to match older prose. The full-context generation
report above and its published summary are the current reference.

## Limits

Eleven development cases are not a held-out production benchmark. Numeric answer
checking allows a tolerance and is not semantic evaluation. Citation overlap does
not verify every claim. Grounding membership does not establish entailment, and
safe abstentions inflate that metric. Human evidence review, unanswerable tests,
configuration capture and latency/cost measurements remain future work.
