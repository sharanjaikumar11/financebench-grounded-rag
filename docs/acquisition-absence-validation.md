# Acquisition absence validation

Optional improvement, separate from original submission reports.

## Problem

The saved Best Buy reply states that no acquisitions were reported in FY2023
and FY2021. Its cited acquisition cash-flow line and FY2022 event descriptions
do not establish those absence claims. A zero cash-flow amount is not proof
that no acquisition occurred.

## Change

`ABSENCE_VALIDATION=1` enables a conservative check after source-quote validation.
Recognized categorical acquisition-absence claims require an explicit absence
statement in the quoted evidence covering the claimed years. A statement about
no material acquisitions cannot support an unqualified no-acquisitions claim;
plans or expectations cannot establish historical absence.

The existing repair attempt can cite suitable evidence, describe supported
events while explicitly identifying missing coverage, or abstain. It does not
automatically change the answer or fabricate evidence. A stated information gap,
such as AMCOR's incomplete earlier-year coverage, remains distinct from claiming
that nothing occurred. Partial answers still require separate completeness review.

The feature defaults off, is enabled in the targeted launcher and is recorded
in provenance. The prompt also clarifies the absence-of-evidence distinction.

## Verification

- 268 unit tests pass; Ruff passes on changed Python files.
- Offline replay of targeted v2, with financial decimal input enabled, rejects
  Best Buy's unsupported absence claim and retains Activision's 1.9% calculation.
- Eight cases have an accepted saved attempt, versus nine with decimal parsing
  alone. The other two are 3M's abstention and Best Buy's rejected claim.
- This is neither a live run nor eight confirmed correct answers. AES metric
  definitions and partial multi-year coverage remain unresolved.
- Result: `evaluation/results/absence_validation_replay_20261026.json`.

## Limits

This check recognizes a narrow set of English acquisition-absence phrasings and
explicit four-digit years. It is not general semantic entailment, does not prove
entity identity, and can conservatively reject evidence where the year is only
in a separate heading. Other negative claims, implicit years and complex clauses
need semantic review. Original reference answers and page labels remain unchanged.

## Next targeted live check

Preflight passed for the same ten cases. Run in the keyed PowerShell terminal:

```powershell
.\scripts\run_targeted_generation.ps1 -OutputPath evaluation\results\generation_targeted_repairs_v3.json
```

Review whether Best Buy's repair removes unsupported claims and whether the live
Activision reply remains valid before a full 50-case evaluation.
