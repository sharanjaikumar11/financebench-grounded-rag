# Expanded evaluation diagnostic — 2026-10-13

Later same-day improvement: the experimental K=5 profile reached 50/50 filing
hits and 45/49 labelled-page hits. See
[retrieval improvement results](retrieval-improvement-results.md) for settings,
comparison and the lower 40/49 generation-context coverage. The baseline below
is preserved, not overwritten.

## Completed

- Prepared 50 draft cases: unchanged original 11 plus 39 deterministic additions
  from 32 companies. Selection does not inspect model performance.
- Matched upstream evidence excerpts to physical PDF pages for all 39 additions.
  This verifies source locations, not reference-answer correctness.
- Added fail-fast draft guards, run provenance, and a separate retrieval-only
  diagnostic with progress checkpoints and original/addition/combined reporting.
- Executed all 50 retrieval queries on the existing fixed-token SQLite index.
- Ruff passed; 118 tests passed with two upstream deprecation warnings.

## Measured retrieval results

| Group | Expected-filing recall | Any labelled evidence-page recall |
| --- | --- | --- |
| Original 11 | 11/11 (100%) | 10/10 (100%) |
| Added 39, draft | 32/39 (82.05%) | 16/39 (41.03%) |
| Combined 50, draft | 43/50 (86%) | 26/49 (53.06%) |

One original case has no page labels. Run duration: 380.36 seconds (6m20s),
including model initialization. Hybrid retrieval, top-K 3 anchors, adjacent
context included, statement-aware ranking enabled, cross-encoder disabled.
Local complete output: `evaluation/results/expanded_retrieval_audit.json`.
That output is ignored by Git; this document preserves the measured summary.

The output also reports strict all-labelled-page coverage. That is not evidence
sufficiency: some baseline page lists are alternative valid locations, while
analytical additions can need multiple pages. Do not conflate these meanings.
No new answer/citation accuracy was measured. These results do not replace or
extend the previously reported 11-case generation metrics to 50 cases.

## Findings and remaining work

1. Seven additions missed the expected filing. Inspect generic fiscal-year
   normalization (`FY22`, `FY20`), quarter syntax (`Q2 of FY2023`), company aliases,
   earnings-vs-annual routing, and questions without explicit dates. Do not pass
   expected documents into retrieval or insert case-specific routing rules.
2. Sixteen additions missed labelled pages despite finding the expected filing.
   Review chunk evidence and multi-page financial calculations before changing
   retrieval or expanding context. A labelled-page miss can also reflect an
   alternative supporting location, requiring evidence review.
3. Review semantic overlaps (Costco assets, Microsoft COGS), acquisition reference
   completeness, and inventory-turnover denominator ambiguity. Record exclusions
   before generation and replace deterministically, never based on model success.
4. Define reviewed scoring rubrics for signed numbers, percentages versus
   percentage points, multi-value/narrative answers, and analytical calculations.
   The existing simple numeric/substring scorer is insufficient for all additions.
5. Freeze the reviewed set with upstream attribution and redistribution review;
   then measure generation separately on original, new, and combined cases.
   GEMINI_API_KEY was unavailable to the evaluation process in this run. Configure
   it locally without sharing it in chat. Do not score the pending draft.

This is a development diagnostic, not an independently held-out benchmark.
Broader assessment work (chunker answer-quality comparison, safety cases,
clean-checkout/container validation) remains listed in `submission-status.md`.
No table indexing was restarted. No changes were committed or pushed in this pass.
