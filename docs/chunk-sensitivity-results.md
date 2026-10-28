# Bounded chunk-size/overlap comparison

## Outcome

The completed local retrieval experiment supports retaining **200 whitespace
tokens with 40-token overlap** for the demo. It is a measured trade-off within
this experiment, not a global optimum or a production accuracy claim.

## Protocol

- All 11 unchanged original evaluation questions; 10 have reference-page labels.
- All pages of the 10 distinct expected filings, parsed once and reused across
  configurations. No gold-page cropping or expected-answer injection.
- This is a reduced corpus selected from expected document names. It is not a
  363-document routing benchmark. Query filters are inferred from each question,
  rather than supplied from its expected-document field.
- Five preselected fixed-token configurations: 100/40, 200/40, 300/40, 200/0,
  200/80. Each alternative changes one parameter relative to 200/40; holding
  overlap at 40 while changing size does not hold overlap percentage constant.
- Local all-MiniLM-L6-v2 embeddings; SQLite/FTS5 hybrid retrieval; K=3 anchors
  plus neighbors; at most nine selected generation-context chunks.
- Statement-aware ranking enabled; financial-intent ranking and cross-encoder
  disabled. No Gemini calls, generation scoring, table extraction or full-corpus
  reindexing. Existing production/demo indexes and defaults remain unchanged.

## Measured results

Filing recall is 11/11 (100%) in every row. Page denominators are 10.

| Chunk size / overlap | Chunk count | Full-context page hits | Selected-context page hits | Mean selected whitespace tokens | Index MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100 / 40 | 13,740 | 8/10 (80%) | 8/10 (80%) | 900 | 127.08 |
| **200 / 40** | **5,154** | **10/10 (100%)** | **10/10 (100%)** | **1,800** | **53.50** |
| 300 / 40 | 3,176 | 10/10 (100%) | 10/10 (100%) | 2,700 | 39.79 |
| 200 / 0 | 4,126 | 8/10 (80%) | 8/10 (80%) | 1,800 | 43.05 |
| 200 / 80 | 6,868 | 10/10 (100%) | 10/10 (100%) | 1,800 | 71.07 |

Selected-token totals include overlapping/repeated text; they are not unique
evidence counts or billable model tokens. Index MiB uses 1,048,576 bytes per MiB.

### Interpretation

- 100/40 misses the reference pages for 3M capex (`financebench_id_03029`) and
  Verizon derivatives. 200/40 covers both, but uses twice the context words.
- 200/0 misses Best Buy inventory and JPMorgan segment reference pages. Adding
  40-token overlap recovers those hits in this run, with about 25% more chunks.
  Chunk-boundary and ranking changes both contribute; this does not isolate
  overlap as a semantic repair mechanism.
- 300/40 ties page coverage with fewer chunks and smaller disk usage, but needs
  50% more selected context words. It is a valid alternative if storage is the
  priority; no measured answer-quality advantage is established.
- 200/80 ties 200/40 while creating about 33% more chunks. The extra overlap
  yields no page-coverage improvement on these questions.

Thus 200/40 balances observed coverage and selected-context size without the
additional index cost of 80-token overlap. It is not the smallest index option.

## Limitations

This is retrieval-only evidence on repeatedly used development questions and a
reduced, expected-filing-selected corpus. A page hit does not guarantee the right
row, year, unit or complete answer evidence. Larger chunks can gain page overlap
without improving relevance. Holding chunk count rather than a fixed token budget
means prompt sizes differ. Embedding tokenizer truncation was not measured;
whitespace chunk sizes are not model-token lengths. There are no confidence
intervals, held-out results or live answer/citation scores for these variants.

The five configuration phases took about 55.8 minutes in total (including indexing
and retrieval, excluding initial PDF parsing). These sequential, local CPU timings
include warm-up/load effects and are not a controlled performance benchmark.

## Artifacts and reproduction

- Runner: `scripts/run_chunk_sensitivity.py`.
- Git-reviewable manifest: [configuration results and source/report hashes](../evaluation/published/chunk_sensitivity_20261015.json).
- Local isolated indexes and per-case JSON:
  `evaluation/results/chunk_sensitivity_20261015/` (ignored by Git).
- The manifest records the dataset hash, all ten source PDF hashes, five result
  hashes, metrics, chunk counts, disk sizes and timings. Individual JSON reports
  include case-level page hits and run metadata. They contain no API keys.

From the project root with the local model and PDFs available:

```powershell
python scripts/run_chunk_sensitivity.py --output-directory evaluation/results/chunk_sensitivity_repeat
```

Use an unused output directory; the runner refuses overwrites. It fixes its own
ranking settings and uses four CPU threads. It never opens the full-corpus vector
stores. No provider key is needed.

Validation: full suite **138 passed**, two upstream deprecation warnings; new
runner and tests pass Ruff. No changes have been committed or pushed in this task.
