"""Audit draft source pages without promoting cases or consulting model outputs."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pymupdf


def normalize(text):
    return re.sub(r"\W+", "", unicodedata.normalize("NFKC", text).casefold())


def page_match(evidence, page):
    needle, haystack = normalize(evidence), normalize(page)
    if not needle:
        return 0.0
    if needle in haystack:
        return 1.0
    # Text layout/extraction can differ. Partial overlap is not proof of support.
    windows = [needle[i : i + 80] for i in range(0, len(needle) - 79, 80)]
    return sum(window in haystack for window in windows) / len(windows) if windows else 0.0


def main():
    draft_path = Path("evaluation/drafts/cases_50.json")
    cases = json.loads(draft_path.read_text())
    upstream = {
        item["financebench_id"]: item
        for item in map(
            json.loads,
            Path("data/raw/financebench/data/financebench_open_source.jsonl")
            .read_text(encoding="utf-8")
            .splitlines(),
        )
    }
    records = []
    original = json.loads(Path("evaluation/cases.json").read_text(encoding="utf-8"))
    if cases[: len(original)] != original:
        raise ValueError("Original regression cases were changed")
    for case in cases[len(original) :]:
        item = upstream[case["case_id"]]
        pages = []
        for evidence in item["evidence"]:
            path = Path("data/raw/financebench/pdfs") / (evidence["doc_name"] + ".pdf")
            raw = evidence["evidence_page_num"]
            with pymupdf.open(path) as pdf:
                candidates = []
                for index in sorted({raw - 1, raw, raw + 1}):
                    if 0 <= index < len(pdf):
                        text = pdf[index].get_text()
                        candidates.append(
                            {
                                "physical_page": index + 1,
                                "evidence_overlap": page_match(evidence["evidence_text"], text),
                                "page_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                            }
                        )
                candidates.sort(key=lambda c: c["evidence_overlap"], reverse=True)
            pages.append({"document": path.name, "upstream_page": raw, "candidates": candidates})
        answer = case["expected_answer"].strip()
        numeric = bool(re.fullmatch(r"\$?-?[\d,.]+%?", answer))
        records.append(
            {
                "case_id": case["case_id"],
                "question": case["question"],
                "reference_answer": answer,
                "question_type": item.get("question_reasoning") or "not_labelled_upstream",
                "required_scoring": "numeric_unit_aware" if numeric else "reviewed_semantic_rubric",
                "page_checks": pages,
                "answer_verification": "pending_manual_evidence_review",
            }
        )
        print(case["case_id"], [p["candidates"][0]["evidence_overlap"] for p in pages], flush=True)
    report = {
        "draft_sha256": hashlib.sha256(draft_path.read_bytes()).hexdigest(),
        "note": "Page-text overlap is not answer verification or a scoring rubric.",
        "cases": records,
    }
    Path("evaluation/drafts/source_audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
