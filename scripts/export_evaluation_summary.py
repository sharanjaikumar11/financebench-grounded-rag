"""Export reviewable metrics without raw document text or provider responses."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    content = args.report.read_bytes()
    report = json.loads(content)
    metrics = (
        "case_count",
        "retrieval_recall",
        "answer_accuracy",
        "citation_accuracy",
        "grounding_rate",
        "page_labelled_case_count",
        "retrieval_page_recall",
        "abstention_rate",
        "answered_accuracy",
    )
    summary = {key: report[key] for key in metrics if key in report}
    summary["source_report"] = args.report.name
    summary["source_sha256"] = hashlib.sha256(content).hexdigest()
    summary["configuration_caveat"] = (
        "Legacy report does not capture model revision or environment settings. "
        "Do not infer those settings from this summary."
    )
    summary["failures"] = [
        {key: case.get(key) for key in ("case_id", "failures", "abstained", "retrieval_page_hit")}
        for case in report.get("failures", [])
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
