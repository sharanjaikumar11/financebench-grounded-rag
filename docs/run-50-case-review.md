# Optional 50-case collection and reviewed scoring

Implemented 2026-10-25. **This does not certify that all 50 references are reviewed.**
The existing draft and original 11-case scores remain unchanged.

## What can run now

The source-audited draft can be used to collect generated responses without
pretending to have a validated answer-accuracy score. This is a separate command
from the scored runner, whose draft guard remains intact. It uses K=5, evidence
mode, statement/concept ranking, context diversity and no cross-encoder. It fixes
these settings internally and records provenance. No expected answers/pages are
passed to the answering service. The collection contains source excerpts and
provider replies: keep it local, not in Git or public chat.

In the activated, keyed PowerShell terminal at the project root:

```powershell
$env:ANSWER_PROVIDER = "gemini"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"
$env:GEMINI_FALLBACK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_THINKING_LEVEL = "minimal"
python scripts/run_50_generation_collection.py --output evaluation/results/generation_50_collection_20261025.json
```

Set GEMINI_API_KEY locally first; never paste it in chat. Use a fresh output
filename. The collector checkpoints each response, preserves errors as errors,
and reports original/addition/combined groups. No automatic retry/resume of
saved errors is implemented; preserve the run and investigate errors first.
Provider generation may itself perform its configured retry/repair behavior.

Run with `--preflight-only` to validate source-audit/original-case guards without
provider calls. This preflight passed locally; no provider key was available to
the agent, so no live 50-question run has been executed here.

## Final answer scoring

The `reviewed-adjudication-v1` workflow accepts explicit evidence-review records
for numeric, categorical, list and narrative answers. This is review-based
grading, not an automated semantic LLM judge. Each decision must include:

```json
{
  "collection_sha256": "SHA256_OF_THE_EXACT_COLLECTION_FILE",
  "decisions": [
    {
      "case_id": "CASE_ID",
      "reference_status": "verified",
      "answer_correct": true,
      "reviewer": "REVIEWER_ID",
      "reference_reason": "Checked source, period, units and all calculation inputs",
      "answer_reason": "Explain why all required claims pass or fail",
      "rubric": "Versioned case rubric or explicit grading requirements"
    }
  ]
}
```

Do not copy the example verdict without reviewing evidence. Numeric scalar
checks from numeric-rubric-v1 can assist review; they are not silently applied to
free-form answers. Narrative/list review must cover required claims, synonyms,
contradictions and completeness. A reviewer identity and text fields are an audit
record, not a technical guarantee that review was performed correctly.

After creating real decisions bound to the collection hash:

```powershell
python scripts/score_reviewed_50.py --collection evaluation/results/generation_50_collection_20261025.json --reviews evaluation/results/generation_50_reviews_v1.json --output evaluation/results/generation_50_scored_v1.json
```

The scorer keeps 11/39/50 denominators fixed. Missing reviews/provider errors
keep final answer accuracy null. Unknown/duplicate decisions, unverified
references and correct labels for answerable-case abstentions are rejected.
Citation-location accuracy uses expected filing/page overlap and remains
provisional where reference-page policy is not reviewed. It is not claim support.

## Pending, not hidden

- Complete the reference/calculation review documented in expanded-rubric-review.md.
- Resolve multi-year completeness, ambiguous ratios, percentage-point semantics
  and duplicate coverage; do not select replacements based on generated success.
- Record reference dispositions separately before examining model answers where
  feasible; preserve original and corrected references with reasons/versioning.
- Review all collected answers and finalize the report. Until then, there is no
  verified 50-case answer accuracy. These development results will not be directly
  comparable to the original legacy automatic checker without explaining policy.
- Dataset redistribution/licensing review remains separate.

This workflow enables honest collection now without disabling the existing
scored-evaluation safeguards or presenting unfinished review as complete.
