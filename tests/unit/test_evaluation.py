import json
from pathlib import Path

import pytest

from rag_system.evaluation.datasets import EvaluationCase, load_evaluation_cases
from rag_system.evaluation.metrics import answer_correct, citation_correct
from rag_system.evaluation.runner import EvaluationResponse, EvaluationRunner, GroundedEvaluationSystem
from rag_system.evaluation.runner import RetrievalExperimentRunner
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


class FakeRetriever:
    def __init__(self, retrieved: tuple[RetrievedChunk, ...]) -> None:
        self.retrieved = retrieved
        self.calls: list[tuple[str, int, dict[str, object]]] = []

    def retrieve(
        self, question: str, top_k: int, metadata_filter: dict[str, object]
    ) -> tuple[RetrievedChunk, ...]:
        self.calls.append((question, top_k, metadata_filter))
        return self.retrieved


class IndexAwareFakeRetriever(FakeRetriever):
    def __init__(self, retrieved: tuple[RetrievedChunk, ...], inferred_filter: dict[str, object]) -> None:
        super().__init__(retrieved)
        self.vector_store = type(
            "VectorStore",
            (),
            {"infer_filing_metadata_filter": staticmethod(lambda _: inferred_filter)},
        )()


class FakeGenerator:
    def answer(self, question: str, retrieved: tuple[RetrievedChunk, ...]) -> GroundedAnswer:
        return answer()


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


def test_answer_metric_accepts_equivalent_financial_units_and_yes_no_verdicts() -> None:
    millions_case = EvaluationCase("case-1", "What is the value in USD millions?", "$1577.00", "source.pdf")
    billions_case = EvaluationCase("case-2", "What is the value in USD billions?", "$8.70", "source.pdf")
    verdict_case = EvaluationCase("case-3", "Is the company capital intensive?", "No", "source.pdf")

    assert answer_correct(millions_case, GroundedAnswer("$1.577 billion [S1]", (), False))
    assert answer_correct(billions_case, GroundedAnswer("$8,700 million [S1]", (), False))
    assert answer_correct(verdict_case, GroundedAnswer("No, it is not. [S1]", (), False))


def test_answer_metric_ignores_fiscal_year_when_selecting_a_financial_value() -> None:
    case = EvaluationCase("case-1", "What is FY2018 net PPNE in USD billions?", "$8.70", "source.pdf")

    assert answer_correct(
        case,
        GroundedAnswer("The FY2018 net PPNE was $8.738 billion. [S1]", (), False),
    )


def test_citation_metric_accepts_the_expected_source_among_direct_citations() -> None:
    case = EvaluationCase("case-1", "Question", "answer", "expected.pdf")
    cited = GroundedAnswer(
        "Answer [S1] [S2]",
        (
            Citation("S1", "doc-1", "other.pdf", (), ()),
            Citation("S2", "doc-2", "expected.pdf", (), ()),
        ),
        False,
    )

    assert citation_correct(case, cited)


def test_case_loader_validates_nonempty_unique_case_ids(tmp_path: Path) -> None:
    valid = tmp_path / "cases.json"
    valid.write_text(json.dumps([{
        "case_id": "one", "question": "q", "expected_answer": "a",
        "expected_document": "d.pdf", "expected_pages": [12, 13],
    }]))
    case = load_evaluation_cases(valid)[0]
    assert case.case_id == "one"
    assert case.expected_pages == (12, 13)

    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]")
    with pytest.raises(ValueError):
        load_evaluation_cases(invalid)


def test_retrieval_experiment_records_source_evidence_and_recall() -> None:
    case = EvaluationCase("case-1", "Question", "$1577.00", "3M_2018_10K.pdf", (59,))
    retriever = FakeRetriever((source(),))

    report = RetrievalExperimentRunner().run(retriever, [case], "fixed_token", 5)

    assert report.retrieval_recall == 1.0
    assert report.cases[0].expected_pages == (59,)
    assert report.cases[0].retrieved_pages == ((59,),)
    assert retriever.calls == [("Question", 5, {"chunking_strategy": "fixed_token"})]


def test_retrieval_experiment_records_exactly_the_requested_top_k() -> None:
    case = EvaluationCase("case-1", "Question", "$1577.00", "3M_2018_10K.pdf")
    retriever = FakeRetriever((source(), source("other.pdf")))

    report = RetrievalExperimentRunner().run(retriever, [case], "fixed_token", 1)

    assert report.cases[0].retrieved_documents == ("3M_2018_10K.pdf",)


def test_retrieval_experiment_can_apply_inferred_filing_metadata() -> None:
    case = EvaluationCase(
        "case-1", "What was FY2018 capital expenditure for 3M?", "$1577.00", "3M_2018_10K.pdf"
    )
    retriever = FakeRetriever((source(),))

    RetrievalExperimentRunner().run(retriever, [case], "fixed_token", 5, True)

    assert retriever.calls[0][2] == {
        "chunking_strategy": "fixed_token",
        "document_name": "3M_2018_10K.pdf",
    }


def test_retrieval_experiment_uses_indexed_metadata_when_static_parsing_cannot_identify_company() -> None:
    case = EvaluationCase(
        "case-amazon", "What was Amazon's FY2019 net income?", "$11,588", "AMAZON_2019_10K.pdf"
    )
    retriever = IndexAwareFakeRetriever((source("AMAZON_2019_10K.pdf"),), {
        "document_name": "AMAZON_2019_10K.pdf"
    })

    RetrievalExperimentRunner().run(retriever, [case], "fixed_token", 3, True)

    assert retriever.calls[0][2] == {
        "chunking_strategy": "fixed_token",
        "document_name": "AMAZON_2019_10K.pdf",
    }


def test_grounded_evaluation_system_retrieves_with_inferred_filing_metadata() -> None:
    retriever = FakeRetriever((source(),))
    system = GroundedEvaluationSystem(retriever, FakeGenerator(), 3)

    response = system.answer("What was FY2018 capital expenditure for 3M?")

    assert response.answer.insufficient_context is False
    assert retriever.calls[0][1:] == (3, {"document_name": "3M_2018_10K.pdf"})
