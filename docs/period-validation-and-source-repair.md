# Optional period validation and source repair

Separate from the lead-required submission. Benchmark answers, reference pages
and the retrieval index are unchanged.

## Changes

- Invalid quotes receive repair hints listing other supplied source IDs containing
  the exact whitespace-normalized excerpt. The model must return corrected
  evidence; the validator never automatically relabels a citation.
- `PERIOD_VALIDATION=1`, together with `CALCULATION_VALIDATION=1`, rejects an
  operand year conflicting with a nearby singular dated statement heading.
  The existing repair attempt can find suitable evidence or abstain.
- The period flag and validator hash are captured in evaluation provenance.

## Offline checks, 2026-10-26

Replayed `generation_50_numeric_row_coverage.json` without API calls. Results:
`evaluation/results/period_validation_replay_20261026.json`.

- Previously accepted answers: 42. Accepted saved answers after validation: 41.
- The confirmed Kraft Heinz wrong-year calculation is rejected; no other
  previously accepted response changes status.
- No abstention is recovered by replaying unchanged provider responses.
- 229 unit tests pass. Source reassignment hints retain strict quote validation.

These are validation outcomes, not new accuracy measurements. Adobe's saved
header quote belongs to S1 rather than S2; new generation must test whether
the repair hint leads to a corrected answer.

## Limitations

The period check covers calculation operands, singular month/day/year headings
within 1,200 characters before a uniquely occurring quoted row, and contexts
without intervening competing years. It skips ambiguous multi-year tables,
repeated rows and operands without one identifiable year. It does not establish
column alignment, semantic correctness, candidate completeness or that all
required arithmetic was declared. Passing is not proof of correctness.

## Next live comparison

Keep the baseline model and thinking settings. In the activated, locally keyed
PowerShell terminal:

```powershell
$env:CALCULATION_VALIDATION = "1"
$env:COMPARISON_VALIDATION = "1"
$env:METRIC_IDENTITY_VALIDATION = "1"
$env:EVIDENCE_REPAIR_EXCERPTS = "1"
$env:NUMERIC_ROW_COVERAGE = "1"
$env:PERIOD_VALIDATION = "1"
python scripts\run_50_generation_collection.py --output evaluation\results\generation_50_period_validation.json
```

Keep the original baseline. Review corrected answers and citations before
publishing accuracy; citation-location matches alone are insufficient.
