# Calculation schema compatibility repair

This optional improvement follows the first live calculation experiment. It does
not change the original submission metrics or benchmark labels.

## Changes

- Accept plain JSON or one complete Markdown JSON fence. Reject surrounding
  commentary, multiple objects/blocks, non-JSON language fences and partial fences.
- Apply the same parser to evidence repair diagnostics so fenced replies still
  identify the exact invalid evidence entries.
- Include the mandatory `calculations` field in the main JSON output example,
  not only in appended instructions. Repair guidance explicitly distinguishes an
  empty list for direct/qualitative answers from structured arithmetic.
- Keep source IDs, exact quote membership, operand membership, arithmetic and
  result-placeholder checks unchanged. Missing calculations still fail validation.

## Verification

198 unit tests passed; Ruff passed on the changed runtime, replay script and tests.
Tests cover valid fences, extra commentary, multiple blocks, malformed wrappers,
unchanged quote rejection and mandatory calculation fields.

Replayed every saved attempt in
`generation_50_calculation_validation.json` without retrieval or provider calls:

| Measure | Original | Replay |
|---|---:|---:|
| Cases with an accepted response/attempt | 23 | 24 |
| Invalid JSON attempts | 21 | 1 |

The one newly accepted saved case is `financebench_id_00566`. Removing a formatting
error often exposes a later failure: replay records 22 invalid-calculation attempts,
18 quote mismatches, 3 operand-membership failures and 3 result mismatches.
Counts are attempts, not unique cases. No original accepted case was lost in this replay.

This is **not a new accuracy score**. Saved repair replies were generated under old
diagnostics; the replay does not simulate responses to changed prompts. The prompt
clarification's impact is unmeasured, and accepted responses still need semantic review.

Results: `evaluation/results/calculation_schema_replay_20261025.json`.

```powershell
python scripts\replay_evidence_validation.py --collection evaluation\results\generation_50_calculation_validation.json --output evaluation\results\calculation_schema_replay_new.json
```

Before a fresh live comparison, set both `CALCULATION_VALIDATION=1` and
`EVIDENCE_REPAIR_EXCERPTS=1`, retain the previous model/thinking settings, and use
a new output filename. Keep this feature opt-in. Deterministic result rendering
without relying on the model's arithmetic and metric/period validation remain next
implementation candidates; neither is claimed complete here.
