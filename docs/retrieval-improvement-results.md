# Generic routing and financial-intent retrieval — 2026-10-13

## Measured result

The unchanged 50-case draft achieved the requested **greater than 85% labelled
page recall and 100% expected-filing retrieval recall** with the experimental
five-anchor profile. This is not a guarantee of universal or uniquely correct
filing routing. Several ambiguous questions search multiple eligible filings.

| Configuration | Filing hits | Labelled-page hits |
| --- | --- | --- |
| Preserved baseline, K=3 | 43/50 (86%) | 26/49 (53.06%) |
| First routing-only development run, K=3 | 45/50 (90%) | 28/49 (57.14%) |
| First concept-aware development run, K=3 | 49/50 (98%) | 38/49 (77.55%) |
| Final routing + concept-aware + filing diversity, K=5 | **50/50 (100%)** | **45/49 (91.84%)** |

Final original-11 subset: 11/11 filing hits, 10/10 labelled-page hits.
Final added-39 subset: 39/39 filing hits, 35/39 labelled-page hits (89.74%).
One original question has no page label and is excluded from the page denominator.
Final elapsed time: 256.64 seconds (about 4m17s), including model initialization.
Run times are not a controlled performance benchmark; caching can differ.

The final profile changes both ranking/routing and K. Do not attribute the full
gain solely to any one change or compare its cost directly with K=3. Questions,
expected answers, page labels, index and benchmark membership were not altered.
Development used observed failures; this is not a held-out generalization result.

## Implemented changes

- Normalize explicit short fiscal years and quarter wording such as `FY24` and
  `Q2 of FY2024`. Short-year expansion currently assumes the 2000s corpus.
- Match case-insensitive company names with token boundaries; derive conservative
  unique acronym/prefix candidates from indexed names, without a company lookup
  table. Alias heuristics still need held-out ambiguity tests.
- Preserve same-period earnings releases when filing type is ambiguous. If the
  requested-quarter filing is absent, retain eligible annual evidence instead of
  silently substituting a different quarterly period.
- Preserve company scope even when no year is supplied. Empty candidate sets
  remain empty; indexed routing no longer falls back to fabricated filenames.
- Support parameterized document-name sets and explicit API filter overrides.
- Add optional general accounting/concept aliases and evidence scoring for ratios,
  acquisitions, litigation, registration, segment results and other financial
  concepts. No reference answers, document-specific pages or case IDs appear in
  these retrieval rules.
- Reduce generic numeric/statement-heading preference for recognized concepts;
  downrank audit/certification prose and parent-only financial schedules.
- Under the experimental profile, diversify anchors across eligible documents
  and consider all sparse matches within a scoped filing set.
- Record inferred filters, retrieval/generation chunk counts, generation-context
  page hits and retrieval source-code hashes in the diagnostic report.

## Important generation limit

K=5 yields up to 15 retrieved neighbor-expanded chunks. The existing generator
still selects at most nine. Its selected context retained **40/49 labelled-page
hits (81.63%)**, losing five page hits present in full retrieval. Original-11
generation-context page coverage remains 10/10; added-39 coverage is 30/39.

No LLM was called for this diagnostic. Answer and citation accuracy have not been
remeasured. Keep the new ranking profile opt-in until generation context selection
and reviewed answer scoring are evaluated. API/demo defaults remain K=3; setting
the ranking flag alone does not reproduce the five-anchor result.

Remaining full-retrieval page misses:

- `financebench_id_01858`: date-unspecified dividend trend / reference-page choice.
- `financebench_id_10420`: ROA multi-statement evidence.
- `financebench_id_01079`: acquisition evidence and reference-answer review.
- `financebench_id_04784`: operating-margin change evidence.

Page hits alone do not prove all operands or claims are supported. The added cases
still require reference/rubric and semantic-duplicate review before generation
scoring. Do not relabel alternative pages just to meet an accuracy target.

## Reproduce the retrieval profile

From the project root in the activated environment:

```powershell
$env:STATEMENT_AWARE_RANKING = "1"
$env:FINANCIAL_INTENT_RANKING = "1"
Remove-Item Env:RERANKER_MODEL -ErrorAction SilentlyContinue
python scripts/run_audited_retrieval.py `
  --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 `
  --top-k 5 `
  --output evaluation/results/expanded_intent_k5_repeat.json
```

Preserve previous outputs. The source audit and original cases must pass the
diagnostic guards. No provider key or reindexing is required. Unset
`FINANCIAL_INTENT_RANKING` to disable concept-aware scoring and filing diversity;
generic routing fixes remain active.

Local reports (ignored by Git): `expanded_retrieval_audit.json`,
`expanded_routing_v1.json`, `expanded_intent_v1_k3.json`,
`expanded_intent_v2_k5.json`, all under `evaluation/results/`.
The final report includes code hashes; earlier development reports have less
complete provenance. This document preserves their aggregate measurements.

Validation: **131 tests passed**, two upstream deprecation warnings; Ruff lint,
format checks and `git diff --check` passed. No table indexing, commit or push
was performed. Next: improve evidence retention within the bounded generation
context, then complete rubric review and run live answer/citation evaluation.
