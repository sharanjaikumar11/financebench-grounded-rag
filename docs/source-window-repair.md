# Optional source-window repair

Implemented 2026-10-26, separate from the original submission requirements.

## Problem and change

The previous repair prompt identified other source IDs containing a misplaced
quote, but its copy-check section repeated only the incorrectly assigned source.
Matching source text could remain buried in the full original context.

With `EVIDENCE_REPAIR_EXCERPTS=1`, matching sources now appear first in the
copy-check section, followed by the originally assigned sources. Each copied
window contains at most 1,800 characters; the section has a 9,000-character
source-text budget. Windows start near the exact quote match where available.
The complete original source prompt remains available. Long quotes or multiple
matches in one source may not fit the repeated window; it is copy assistance,
not replacement evidence. The budget covers copied text, not JSON overhead.

No new sources, automatic citation reassignment, fuzzy quote matching, reference
answers or company-specific rules are introduced. The model must return corrected
evidence, which passes through the existing quote, calculation and period checks.

## Verification

- 231 unit tests pass; Ruff passes on changed Python files.
- All seven quote-failure attempts in the latest 50-case collection were inspected
  offline. Every repeated excerpt is a substring of an actual supplied source
  after whitespace normalization and stays within the configured size limits.
- Adobe's two failed attempts now repeat S1 before S2, exposing the actual header.
- American Express's second failed attempt repeats S6 before S3, exposing the
  exact matching source for its misplaced excerpt.
- Audit: `evaluation/results/source_window_repair_audit_20261026.json`.

This is prompt verification, not new generation. No answer recovery or accuracy
gain is claimed. Reference labels remain unchanged. Missing statement rows for
other abstentions still require retrieval investigation before another full run.
