import json
from pathlib import Path

import pytest

from rag_system.evaluation.datasets import EvaluationCase, load_evaluation_cases
from rag_system.evaluation.runner import EvaluationResponse, EvaluationRunner
from rag_system.schemas import Citation, DocumentChunk, GroundedAnswer, RetrievedChunk


def source(document_name: str = "3M_2018_10K.pdf") -> RetrievedChunk:
    return RetrievedChunk(
        chunk=DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name=document_name,
            chunk_index=0,
            text="Capital expenditure was $1577.00.",
            token_count=4,
            chunking_strategy="fixed_token",
            page_numbers=(59,),
            section_titles=("Cash Flows",),
        ),
        score=0.9,
    )


def answer(document_name: str = "3M_2018_10K.pdf") -> GroundedAnswer:
    return GroundedAnswer(
        text="Capital expenditure was $1577.00. [S1]",
        citations=(
            Citation("S1", "doc-1", document_name, (59,), ("Cash Flows",)),
        ),
        insufficient_context=False,
    )


class FakeSystem:
    def __init__(self, response: EvaluationResponse) -> None:
        self.response = response

    def answer(self, question: str) -> EvaluationResponse:
        return self.response


def test_runner_measures_all_required_metrics_for_a_passing_case() -> None:
    case = EvaluationCase("case-1", "Question", "$1577.00", "3M_2018_10K.pdf")
    report = EvaluationRunner().run(FakeSystem(EvaluationResponse((source(),), answer())), [case])

    assert report.retrieval_recall == 1.0
    assert report.answer_accuracy == 1.0
    assert report.grounding_rate == 1.0
    assert report.citation_accuracy == 1.0
    assert report.failures == ()


def test_runner_records_each_failure_category() -> None:
    case = EvaluationCase("case-1", "Question", "$1577.00", "3M_2018_10K.pdf")
    response = EvaluationResponse(
        (source("other.pdf"),),
        GroundedAnswer("Wrong", (), False),
    )
    report = EvaluationRunner().run(FakeSystem(response), [case])

    assert report.failures[0].failures == (
        "retrieval_miss",
        "incorrect_answer",
        "unsupported_answer",
        "incorrect_citation",
    )


def test_case_loader_validates_nonempty_unique_case_ids(tmp_path: Path) -> None:
    valid = tmp_path / "cases.json"
    valid.write_text(json.dumps([{"case_id": "one", "question": "q", "expected_answer": "a", "expected_document": "d.pdf"}]))
    assert load_evaluation_cases(valid)[0].case_id == "one"

    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]")
    with pytest.raises(ValueError):
        load_evaluation_cases(invalid)
