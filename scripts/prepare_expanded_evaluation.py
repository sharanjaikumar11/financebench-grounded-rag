"""Prepare 50 draft cases without selecting on model performance. Not a verified benchmark."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path


def select_additions(records, existing, count=39):
    ids = {case["case_id"] for case in existing}
    questions = {case["question"].strip().casefold() for case in existing}
    groups = defaultdict(list)
    for record in records:
        if (
            record["financebench_id"] not in ids
            and record["question"].strip().casefold() not in questions
        ):
            groups[record["company"]].append(record)

    def stable_key(record):
        return hashlib.sha256(record["financebench_id"].encode()).hexdigest()

    for group in groups.values():
        group.sort(key=stable_key)
    selected = []
    while len(selected) < count:
        progressed = False
        for company in sorted(groups):
            if groups[company] and len(selected) < count:
                record = groups[company].pop(0)
                key = record["question"].strip().casefold()
                if key not in questions:
                    selected.append(record)
                    questions.add(key)
                    progressed = True
        if not progressed and not any(groups.values()):
            raise ValueError("Not enough unique questions")
    return selected


def main():
    original = Path("evaluation/cases.json")
    dataset = Path("data/raw/financebench/data/financebench_open_source.jsonl")
    existing = json.loads(original.read_text())
    records = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]
    additions = select_additions(records, existing, 50 - len(existing))
    cases = list(existing)
    for item in additions:
        cases.append(
            {
                "case_id": item["financebench_id"],
                "question": item["question"],
                "expected_answer": item["answer"],
                "expected_document": item["doc_name"] + ".pdf",
                "expected_pages": [],
                "validation_status": "pending_source_review",
                "reasoning_type": item.get("question_reasoning"),
                "source_evidence_pages": [
                    {"document": e["doc_name"], "raw_page_number": e["evidence_page_num"]}
                    for e in item["evidence"]
                ],
            }
        )
    out = Path("evaluation/drafts/cases_50.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "status": "draft_not_for_scored_evaluation",
        "selection": "Round-robin company diversity, SHA256 ID order within company; no model outputs used",
        "source_dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "original_cases_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "original_count": len(existing),
        "added_count": len(additions),
        "added_companies": len({r["company"] for r in additions}),
        "source": "Local FinanceBench open-source dataset; preserve upstream attribution/license before distribution",
        "pending": "Validate PDF evidence, page numbering, index coverage, multi-document support, and scoring rubrics",
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
