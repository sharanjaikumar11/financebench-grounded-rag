# Evaluation report

## Current 50-case evaluation — 28 October 2026

The latest collection is `evaluation/results/generation_50_20261028_142603.json`.
The case-by-case agent review is `evaluation/results/answer_review_20261028_142603.json`.
These are the current results; the 15 October experiments below are historical
controlled comparisons, not the score of the latest implementation.

| Measure | Latest result |
| --- | ---: |
| Completed cases / provider errors | 50 / 0 |
| Returned answers / abstentions | 45 / 5 |
| Expected-filing retrieval recall | 100% (50/50) |
| Labelled-page retrieval recall | 95.92% (47/49) |
| Strict reference citation-location matches | 72% (36/50) |
| Agent-reviewed source-supported answers | 84% (42/50) |
| Incorrect or abstained | 6/50 |
| Unresolved definition cases | 2/50 |

Final answer accuracy remains null pending the two AES decisions. Under the stated
review rubric the possible range is 84–88%; 88% has not been achieved or approved.
The agent review is not independent human adjudication. Five abstentions count as
unsuccessful and AMD's quick-ratio answer is incorrect despite its correct verdict.

Configuration: fixed-token 200/40, local MiniLM, hybrid SQLite/FTS5, five anchors,
at most nine generation sources, Gemini minimal thinking, structured evidence,
statement/financial/diversity ranking, operand and numeric-row coverage, arithmetic,
comparison, period, metric-identity and acquisition-absence validation. Cross-encoder
is disabled. Actual model/finish diagnostics and code hashes are stored in the run.
The last run includes the narrow direction-contradiction guard. It is not the same
configuration as the default three-anchor, text-mode demo.

Earlier full run `generation_50_20261028_130232.json` returned 46 answers and 35/50
citation-location matches. The latest run returned 45 answers and 36/50 matches:
PepsiCo and American Express recovered, Adobe and Activision regressed, and Verizon
now abstains after its incorrect directional claim is rejected. Do not attribute
all changes to one fix or substitute the targeted subset's 90% score for this score.

The original 11 cases plus 39 source-audited additions form a repeatedly tuned
development set. Expected-filing hits do not prove answer-bearing context, and
reference-page mismatch may reflect alternate valid evidence. No reference pages
or answers were changed to improve results. Source-supported precision is accepted
where no rounding is requested; see [review rubric](answer-review-20261028.md).
Remaining failures and reference discrepancies are documented in
[failure analysis](failure-analysis.md). No further full run is needed just to
publish these measurements.

## Historical controlled experiments — 15 October 2026

The following was finalized for the 2026-10-15 submission using saved controlled runs.
**Decision: retain fixed-token chunking with K=3 for the demo.** It achieved
9/11 (81.82%) answer accuracy and 9/11 (81.82%) citation accuracy. This is a
small development-set result, not a production-quality guarantee.

## 1. Scope and experimental controls

- Unchanged original `evaluation/cases.json`: 11 questions, 10 with page labels.
- Both complete indexes contain the same 363 filings. Fixed-token and
  section-aware are compared, not table-aware extraction.
- Demo chunk configuration: 200 whitespace-delimited tokens, 40-token overlap.
  These are not embedding-model tokenizer counts; both strategies can split tables.
- Local `all-MiniLM-L6-v2` embeddings, SQLite vectors and FTS5/BM25 hybrid retrieval.
- Same questions, prompt hashes and recorded generation settings across the pair:
  Gemini `gemini-3.1-flash-lite`, fallback `gemini-3.5-flash-lite`, thinking
  `minimal`, evidence output mode, statement-aware ranking on,
  financial-intent ranking off, cross-encoder off.
- Generation compared at K=3 only. Retrieval-only comparisons cover K=3, 5, 10.
  K means anchor chunks; adjacent context expands retrieval, then generation
  selects at most nine chunks. These are not strict K-chunk prompt experiments.
- No expected answers, question selection or tolerance were changed for these runs.

## 2. Generation comparison

| Metric | Fixed-token K=3 | Section-aware K=3, corrected scoring |
| --- | ---: | ---: |
| Expected-filing recall | 11/11 (100%) | 11/11 (100%) |
| Labelled-page recall, full retrieved context | 10/10 (100%) | 9/10 (90%) |
| Answer accuracy | 9/11 (81.82%) | 7/11 (63.64%) |
| Citation accuracy | 9/11 (81.82%) | 7/11 (63.64%) |
| Grounding membership rate | 11/11 (100%) | 11/11 (100%) |
| Abstention rate | 2/11 (18.18%) | 4/11 (36.36%) |
| Correct among answered, corrected scoring | 9/9 (100%) | 7/7 (100%) |

All remaining answer/citation failures after rescoring are abstentions, not
returned incorrect answers under this checker. That does not prove every
returned claim is semantically correct. Abstaining on an answerable benchmark
question still counts as an answer and citation failure.

## 3. Numeric scoring correction — not a model improvement

The original section-aware JSON reports **6/11 (54.55%) answer accuracy**.
Its answer for `financebench_id_04672` contains “8.738 USD billions” after
a fiscal year. The previous numeric parser did not recognize currency after
the amount or plural units and selected the preceding year instead.

The generic parser now recognizes those formats. The answer is accepted against
the $8.70 reference by the existing tolerance:
`abs(actual - expected) <= max(0.01, abs(expected) * 0.005)`.
Here the difference is 0.038 and the tolerance is 0.0435, in requested billions.
This is tolerance-based acceptance, not a claim that 8.738 equals 8.70 exactly.

Rescoring all 22 saved answers changes only this section-aware case:
6/11 becomes 7/11; fixed-token stays 9/11. Citations, retrieval and abstentions
are unchanged. No model was called for rescoring. Original JSON files remain
unchanged. Generic regression tests use unrelated synthetic values, including
wrong amounts that must still fail. The full suite passed 136 tests with two
upstream deprecation warnings after the fix.

## 4. Chunking and K comparison — retrieval only

Filing denominator is 11; both page denominators are 10 labelled questions.

| Strategy | K | Filing hits | Full-context page hits | Selected generation-context page hits |
| --- | ---: | ---: | ---: | ---: |
| Fixed-token | 3 | 11/11 | 10/10 | 10/10 |
| Fixed-token | 5 | 11/11 | 10/10 | 10/10 |
| Fixed-token | 10 | 11/11 | 10/10 | 9/10 |
| Section-aware | 3 | 11/11 | 9/10 | 9/10 |
| Section-aware | 5 | 11/11 | 9/10 | 9/10 |
| Section-aware | 10 | 11/11 | 10/10 | 9/10 |

Fixed-token K=3 covers all labelled pages without needing more anchors in this
set. Section-aware K=10 recovers full-retrieval page coverage, but the nine-chunk
selection still omits one reference page. More retrieved evidence does not
necessarily mean better evidence reaches the model. No generation accuracy at
K=5 or K=10 was measured in this comparison.

This supports the demonstrated fixed-token K=3 choice on these questions.
It does not establish that fixed-token is universally better or that 200/40 is
optimal. A separate [bounded chunk-size/overlap experiment](chunk-sensitivity-results.md)
is now complete on all 11 questions and 10 complete expected filings. At K=3,
200/40 achieved 10/10 selected-context page hits versus 8/10 for 100/40 and
200/0. It tied 300/40 with less context and 200/80 with fewer chunks. This
supports retaining 200/40 within that reduced-corpus, retrieval-only protocol;
it does not establish generation gains or a global optimum.

## 5. Remaining failures and targeted follow-up

| Case | Affected strategy | Observed diagnostic | Next investigation |
| --- | --- | --- | --- |
| `financebench_id_00499`: 3M capital intensity | Both | Model abstained; correct filing retrieved; no reference-page label | Review whether the selected context supports the required reasoning; add reviewed page labels before attributing a page-retrieval failure |
| `financebench_demo_jpmorgan_2022q2_highest_net_income` | Both | Labelled page retrieved, but `quote_not_in_source` on both attempts | Compare requested verbatim quotes to the cited chunks and check segment/header continuity |
| `financebench_demo_costco_2021_total_assets` | Section-aware | Labelled page retrieved, but `quote_not_in_source` on both attempts | Inspect row boundaries and source attribution; retain evidence validation |
| `financebench_demo_verizon_2021_derivatives` | Section-aware | Reference-page miss followed by model abstention | Inspect candidate ranking and neighborhood coverage before changing generation |

These are observed failure stages, not proven extraction root causes.
Page overlap alone does not establish that the necessary row, year, unit or all
comparison operands were available. Do not bypass validation, hard-code answers,
or remove difficult questions to improve the score.

## 6. Metric definitions and limitations

- **Expected-filing recall:** at least one retrieved chunk belongs to the expected
  filing. It measures a filing hit, not evidence completeness or ranking precision.
- **Labelled-page recall:** at least one retrieved chunk in the expected filing
  overlaps a reference page. Unlabelled questions are excluded. Valid evidence
  on another page can be missed by the labels; labels need human review.
- **Answer accuracy:** deterministic numeric tolerance/unit conversion, yes/no
  prefix matching, or text containment. It is not semantic entailment, and can
  mishandle multiple numbers, signs or nuanced explanations.
- **Citation accuracy:** a non-abstaining answer has at least one citation matching
  expected filing and, where labelled, a reference page. It does not require every
  claim or every citation to be correct.
- **Grounding rate:** cited document identities belong to retrieved sources;
  abstentions count as grounded. Thus 100% is not “zero hallucinations.”
- **Answered accuracy:** excludes abstentions; always report it alongside answer
  accuracy and coverage, not as a replacement for them.
- Only 11 repeatedly used development questions; one case changes accuracy by
  9.09 percentage points. There is no held-out generalization claim.
- One live run per strategy. Provider variability, sequential run order and
  unrecorded actual fallback/model revisions limit causal conclusions.
- Git was dirty during execution; the recorded commit alone cannot recreate all
  code. Index size/mtime are not immutable content hashes.
- Recorded durations are not controlled latency benchmarks. No production load,
  cost, security, or comprehensive unanswerable-query evaluation is established.

## 7. Provenance and reproduction

Raw generation artifacts (kept local; include source text/provider diagnostics):

| File under `evaluation/results/submission_20261015_generation/` | SHA-256 |
| --- | --- |
| `fixed_token_k3.json` | `0e25a8b80ef9c7316586cbc67435864fea38276241227ea6e5d4d062536064b2` |
| `section_aware_k3.json` | `05f30ca5f462a5b9b79e1e782debf0dae8846b620a9b632df943964a3591a440` |

Dataset SHA-256:
`8dd6027b61f82dc2f10c24c1bfc400bcee87cb054842cd3eed583ba912bd0769`.
Retrieval artifacts are the six strategy/K JSON files under
`evaluation/results/submission_20261015_retrieval/`.
The recorded generation answer fields retain the pre-correction score; use
Section 3 when interpreting them. This report is the current submission
reference; older published summaries retain their historical meaning.

To rerun from the project root, configure GEMINI_API_KEY locally, never in Git:

```powershell
$env:ANSWER_PROVIDER = "gemini"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
$env:GROUNDED_OUTPUT_MODE = "evidence"
$env:STATEMENT_AWARE_RANKING = "1"
$env:FINANCIAL_INTENT_RANKING = "0"
$env:RERANKER_MODEL = ""
python scripts/run_submission_comparison.py --output-directory evaluation/results/submission_retrieval_repeat
python scripts/run_submission_comparison.py --generation --top-k 3 --output-directory evaluation/results/submission_generation_repeat
```

Choose unused output directories; the runner refuses to overwrite prior runs.
Retrieval-only execution needs no Gemini key. A new live run is not guaranteed
to reproduce identical generated responses.

## 8. Historical development experiments

Earlier sequential generation runs recorded 8/11 answers and 7/11 citations
(`evidence_quote_repair.json`), then 9/11 for both
(`statement_quote_repair.json`, `row_matching_generation.json`).
These are development observations, not isolated causal ablations; legacy
configuration capture was incomplete.

The old three-question chunking comparison and legacy
`fixed_token_hybrid_top_k_3_metadata_filtered.json` are not the current reference.
Older runners may truncate neighbor context to K; do not mix those page-recall
numbers with this full-context protocol.

The earlier 50-case draft retrieval experiment and financial-intent ranking study
are described in [retrieval improvement results](retrieval-improvement-results.md).
Those retrieval-only measurements do not establish answer accuracy. The completed
50-case generation and evidence review are summarized at the start of this report.
Table-aware indexing was stopped and is not a completed experiment.
