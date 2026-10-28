# Structured repair diagnostics

Optional improvement following the ten-case targeted generation run.

Repair now reports one-based calculation and operand positions, zero-based
evidence indices, and specific error codes for invalid names/decimal strings,
signed-value mismatch, missing numeric evidence, copied financial literals and
formula/operand-name mismatch. Multiple detected issues are reported together.
For a sign mismatch, the hint includes the signed value only after verifying
that the exact quoted excerpt belongs to the supplied source. It never edits
an operand, formula, source ID or answer automatically.

Unique quote-location hints now explicitly identify which evidence entry must
use which source if the model retains that supporting quote. These hints prove
location, not semantic support. The model still must return valid evidence.

## Verification

- 245 unit tests pass; Ruff passes on changed Python files.
- Saved-response audit covers all 12 rejected attempts in the targeted run.
- Coca-Cola and AES inventory report signed-operand mismatches; Activision reports
  three sign mismatches plus formula errors; American Express's malformed repair
  reports invalid names and formula errors. AES ROA's first attempt reports an
  invalid parenthesized decimal string.
- Replay changes **zero** saved validation decisions. No rules were relaxed.
- Audit: `evaluation/results/structured_repair_audit_20261026.json`.

No new API answers were generated and no recovery/accuracy gain is claimed.
The diagnostics are bounded repair assistance, not an exhaustive schema checker
or semantic verifier. Existing validators remain authoritative. Ambiguous income
bases, inventory denominators, qualitative criteria and unsupported absence
claims remain subject to review.

## Next targeted run

Use the locally keyed PowerShell terminal. Keep the original output:

```powershell
.\scripts\run_targeted_generation.ps1 -OutputPath evaluation\results\generation_targeted_repairs_v2.json
```

This reruns the same ten diagnostic cases with unchanged model/thinking settings.
Review the generated replies before proceeding to a full 50-case evaluation.
