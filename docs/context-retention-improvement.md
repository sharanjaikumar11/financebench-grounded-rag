# Optional bounded-context improvement — 2026-10-25

This is separate from the lead-only submission results. No live LLM evaluation,
new indexing, dataset changes or hard-coded case answers were used.

## Change

The existing selector spends its nine-source budget on a relevant anchor and
its neighbors before considering later evidence. Five useful page hits in the
saved K=5 retrieval run were lost at this stage.

The opt-in `CONTEXT_DIVERSITY_RANKING=1` selector adds generic financial-intent
relevance and reserves representatives from distinct document/chunk neighborhoods
before filling remaining space with available immediate neighbors. Selection
still returns at most nine unique chunks, ordered by document and chunk position.
It uses only the question and retrieved chunks, never expected answers or pages.
Default behavior is unchanged while live generation validation remains pending.

## Controlled replay

The replay loads the exact ordered chunk IDs from the completed saved
`expanded_intent_v2_k5.json` diagnostic and resolves their text from the index
opened read-only. Source names/pages are checked; every baseline page result must
match the saved run or execution fails. Retrieval is not rerun. Retrieval scores
are not required because neither selector uses them. The original record lacks
text hashes, so identity checks cannot prove immutable historical chunk contents.

| Measurement | Baseline | Opt-in selector |
| --- | ---: | ---: |
| Full-retrieval page hits (unchanged) | 45/49 | 45/49 |
| Selected-context page hits | 40/49 (81.63%) | 45/49 (91.84%) |
| Original-11 labelled-page hits | 10/10 | 10/10 |
| Page-hit regressions | — | 0 |
| Maximum context chunks | 9 | 9 |

Recovered cases: `financebench_id_07507`, `financebench_id_01091`,
`financebench_id_00839`, `financebench_id_02049`, `financebench_id_00566`.
These IDs identify evaluation outcomes only; they do not appear in selection rules.
The four full-retrieval page misses remain unresolved.

Both concept relevance and neighborhood reservation changed together, so the gain
cannot be attributed to either alone. This is a development replay of a draft
50-case set, not held-out evidence. Page retention does not establish sufficient
evidence, correct answers, complete table headers or semantic grounding. Spreading
the budget across neighborhoods can reduce adjacent context for any one passage.
Live answer/citation scoring must wait for reference/rubric review.

## Reproduction

```powershell
python scripts/compare_context_selection.py --input evaluation/results/expanded_intent_v2_k5.json --vector-store data/processed/local_sentence_transformers/vectors.sqlite3 --output evaluation/results/context_selection_repeat.json
```

Use an unused output filename. No key or model inference is required. The script
records source-report and selector hashes and checks the unchanged baseline.
Current output: `evaluation/results/context_selection_20261025.json`.

To enable the selector for a future controlled generation run, set
`$env:CONTEXT_DIVERSITY_RANKING = "1"`; unset it or set `0` for the baseline.
The flag alone does not reproduce K=5 retrieval or its financial-intent settings.

Next: review expanded reference answers/scoring, then compare generation under
identical retrieval and provider settings before considering a default change.

Validation: 140 tests passed with two existing dependency warnings; changed
Python files passed Ruff lint/format. Sandboxed API TestClient execution stalled;
the full suite passed after approved execution outside the sandbox. No commit
or push was performed.
