"""Versioned adjudication for mixed numeric/narrative evaluation.

Human/agent reviewers must inspect evidence, not just copy reference wording.
Unresolved entries keep the final accuracy null; no denominator cherry-picking.
"""

VERSION = "reviewed-adjudication-v1"


def summarize_review(rows, expected_count):
    if len({r["case_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate cases")
    complete = len(rows) == expected_count and all(r["status"] == "completed" for r in rows)
    decided = [r for r in rows if isinstance(r.get("answer_correct"), bool)]
    correct = sum(r["answer_correct"] for r in decided)
    citations = [r for r in rows if r.get("status") == "completed"]
    all_decided = complete and len(decided) == expected_count
    return {
        "expected_case_count": expected_count,
        "collected_case_count": len(rows),
        "answer_review_count": len(decided),
        "unresolved_count": expected_count - len(decided),
        "answer_accuracy": correct / expected_count if all_decided and expected_count else None,
        "confirmed_correct_count": correct,
        "citation_location_accuracy": sum(r["citation_correct"] for r in citations) / expected_count
        if complete and expected_count
        else None,
        "note": "Citation location is not entailment; accuracy stays null until collection and all reviews are complete.",
    }


def apply_review(cases, reviews):
    if len({r["case_id"] for r in reviews}) != len(reviews):
        raise ValueError("Duplicate review decisions")
    known = {c["case_id"] for c in cases}
    if any(r["case_id"] not in known for r in reviews):
        raise ValueError("Unknown review case")
    by_id = {r["case_id"]: r for r in reviews}
    result = []
    for case in cases:
        row = dict(case)
        row["answer_correct"] = None
        decision = by_id.get(case["case_id"])
        if decision is not None:
            if case["status"] != "completed":
                raise ValueError("Cannot adjudicate an uncollected/provider-error case")
            if decision.get("reference_status") != "verified":
                raise ValueError("Reference must be verified before adjudication")
            if not isinstance(decision.get("answer_correct"), bool):
                raise ValueError("Decision must be a boolean")
            for field in ("reviewer", "reference_reason", "answer_reason", "rubric"):
                if not isinstance(decision.get(field), str) or not decision[field].strip():
                    raise ValueError(f"Missing review field: {field}")
            if case.get("abstained") and decision["answer_correct"]:
                raise ValueError("Answerable benchmark abstentions cannot pass")
            row["answer_correct"] = decision["answer_correct"]
            row["review"] = decision
        result.append(row)
    return result
