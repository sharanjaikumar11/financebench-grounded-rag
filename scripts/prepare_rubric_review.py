"""Create a non-scoring review ledger; never promote or rewrite benchmark cases."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def suggested_rubric(question, answer):
    """Triage only: a suggested rubric is not evidence verification."""
    if re.fullmatch(r"\$?-?[\d,.]+%?", answer.strip()):
        if answer.strip().endswith("%"):
            return "percentage_or_percentage_point_change"
        return "signed_numeric_with_explicit_unit_and_rounding"
    if re.match(r"^(yes|no)\b", answer, re.I):
        return "verdict_plus_required_supporting_claims"
    if re.search(r"which|among", question, re.I):
        return "categorical_answer_with_comparison_evidence"
    return "required_claim_set_with_synonyms_and_contradiction_check"


def build_ledger(draft, original, audit):
    if draft[: len(original)] != original:
        raise ValueError("Original cases changed")
    checks = {c["case_id"]: c for c in audit["cases"]}
    rows = []
    for index, case in enumerate(draft):
        pages = case.get("expected_pages", [])
        if index >= len(original):
            pages = []
            for check in checks[case["case_id"]]["page_checks"]:
                exact = [
                    p["physical_page"] for p in check["candidates"] if p["evidence_overlap"] == 1.0
                ]
                if len(exact) != 1:
                    raise ValueError("Ambiguous source audit")
                pages.extend(exact)
        rows.append(
            {
                "case_id": case["case_id"],
                "cohort": "original_11" if index < len(original) else "added_39",
                "question": case["question"],
                "reference_answer": case["expected_answer"],
                "document": case["expected_document"],
                "physical_pages": sorted(set(pages)),
                "suggested_rubric": suggested_rubric(case["question"], case["expected_answer"]),
                "review_status": "legacy_baseline_preserved"
                if index < len(original)
                else "pending_answer_and_rubric_review",
                "required_review": [
                    "reference support and completeness",
                    "unit/sign/rounding",
                    "mandatory versus alternative pages",
                    "semantic duplicates",
                ],
                "approved_for_new_scoring": False,
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new review file")
    draft_path = Path("evaluation/drafts/cases_50.json")
    audit_path = Path("evaluation/drafts/source_audit.json")
    original_path = Path("evaluation/cases.json")
    digest = hashlib.sha256(draft_path.read_bytes()).hexdigest()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit["draft_sha256"] != digest:
        parser.error("Source audit is stale")
    rows = build_ledger(
        json.loads(draft_path.read_text(encoding="utf-8")),
        json.loads(original_path.read_text(encoding="utf-8")),
        audit,
    )
    report = {
        "status": "triage_only_not_scoring_ready",
        "draft_sha256": digest,
        "source_audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        "original_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(rows)} review entries; no cases promoted or changed")


if __name__ == "__main__":
    main()
