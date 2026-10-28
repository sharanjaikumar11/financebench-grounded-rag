# Controlled submission comparison — 2026-10-15

The finalized submission reference is [Evaluation report](experiment-report.md),
including per-case failure diagnostics, metric definitions, artifact hashes and
reproduction commands. This document is a concise comparison summary.

Both runs use the unchanged original 11 questions, the same 363-document corpus,
top-K 3, local MiniLM embeddings, hybrid retrieval, and evidence-mode Gemini.
The model setting was `gemini-3.1-flash-lite`, thinking `minimal`, with
`gemini-3.5-flash-lite` configured as fallback. Statement-aware ranking was on;
financial-intent ranking and the cross-encoder were off. These are configured
model names, not proof of which fallback served each response.

## Generation results

| Strategy | Answer accuracy | Citation accuracy | Labelled-page recall | Abstentions |
| --- | --- | --- | --- | --- |
| Fixed-token | 9/11 (81.82%) | 9/11 (81.82%) | 10/10 (100%) | 2/11 |
| Section-aware, recorded | 6/11 (54.55%) | 7/11 (63.64%) | 9/10 (90%) | 4/11 |
| Section-aware, corrected numeric scoring | 7/11 (63.64%) | 7/11 (63.64%) | 9/10 (90%) | 4/11 |

Expected-filing recall and the implemented grounding metric were 100% for both.
Grounding here checks citation source membership and accepts abstentions; it is
not a semantic entailment assessment. Citation accuracy checks expected filing
and labelled-page overlap. Eleven cases do not establish production reliability.

The numeric scorer previously missed currency after the amount and plural units
(for example, `8.738 USD billions`), selecting an earlier fiscal year instead.
Generic currency/unit parsing was corrected and tested with unrelated synthetic
values. Rescoring every saved answer changed one section-aware case and no
fixed-token cases. The existing 0.5% numeric tolerance and expected answers were
not changed. This is an evaluation correction, not a model improvement.
Original JSON reports remain unchanged under
`evaluation/results/submission_20261015_generation/`.

Fixed-token abstained on the capital-intensity and JPMorgan segment questions.
Section-aware additionally abstained on Costco assets and Verizon derivatives.
Investigate their retrieved evidence and rejected/insufficient outputs before
changing retrieval or prompting; do not substitute expected answers.

## Retrieval-only K comparison

| Strategy | K | Filing recall | Labelled-page recall | Selected generation-context page recall |
| --- | --- | --- | --- | --- |
| Fixed-token | 3 | 100% | 100% | 100% |
| Fixed-token | 5 | 100% | 100% | 100% |
| Fixed-token | 10 | 100% | 100% | 90% |
| Section-aware | 3 | 100% | 90% | 90% |
| Section-aware | 5 | 100% | 90% | 90% |
| Section-aware | 10 | 100% | 100% | 90% |

K denotes retrieval anchors; neighboring chunks may expand retrieval before the
generation context is capped at nine chunks. Increasing K therefore does not
guarantee better evidence in the final prompt. Raw retrieval reports are under
`evaluation/results/submission_20261015_retrieval/`.

## Decision and remaining checks

Keep fixed-token K=3 for the demonstrated configuration. The controlled result
supports this selection on this small set, not a universal advantage over
section-aware chunking. No answer or citation gains should be inferred from the
separate 50-case retrieval-only experiment.

- Numeric parsing regression tests and full suite: 136 passed, two upstream warnings.
- Changed Python files pass Ruff.
- [Bounded chunk-size/overlap sensitivity](chunk-sensitivity-results.md) is complete;
  its reduced-corpus retrieval results support retaining 200/40.
- Final presentation and submission-status reconciliation remain pending.
- Docker execution is not verified: the local Docker engine was unavailable.
- These local changes have not been committed or pushed in this phase.
