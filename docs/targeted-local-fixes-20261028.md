# Targeted local fixes — 28 October 2026

Scope: optional reliability improvements, separate from the lead's required
submission. No benchmark labels, reference answers or retrieval rules changed.

## Changes

- Calculation IDs and operand names accept mixed-case ASCII letters. The
  20-character bound, letter-first rule, uniqueness, exact case matching,
  cited operand checks and restricted arithmetic AST remain enforced.
- Gemini structured replies receive a bounded 4,096 output tokens instead of
  1,024. Text-mode output remains 256 tokens. This allows room for evidence and
  operands but does not guarantee complete JSON or a correct response.
- Per-attempt diagnostics retain the requested/called model, fallback usage,
  output limit, and available model version and finish reason.
- Collection errors retain bounded cause types, numeric HTTP status and a safe
  category; raw exception messages and SDK response bodies are not logged.
  Empty provider replies are distinguishable from HTTP failures. Diagnostics
  reset per request and before each collection case to avoid stale information.

## Local validation

- 282 unit tests passed, including mixed-case names, unsafe names, exact-case
  mismatch, structured/text budgets, finish reasons, metadata reset, empty
  replies, fallback behavior and secret-free error classification.
- Saved v3 replay: `evaluation/results/identifier_replay_20261028.json`.
  Five of ten cases have an accepted saved attempt, previously three. Adobe and
  Kraft Heinz are recovered; the three previously accepted cases remain accepted.
- This is offline validator acceptance, not measured answer/citation accuracy.
- Saved v2 replay under its original flags retains eight accepted cases;
  `evaluation/results/identifier_v2_regression_replay_20261028.json` records it.
- Ruff checks pass for all changed Python files.
  No new API requests were made. Output-budget effects require a future live check.

## Remaining limitations

The old AES provider error cannot be diagnosed retrospectively. Activision still
has truncated JSON and an invalid repaired formula in its saved responses.
Three saved cases abstain. Ratio presentation and financial definition ambiguity
still require answer review. A full 50-case run is not the next validation step;
use the targeted subset first, with a new output filename, when live testing resumes.
