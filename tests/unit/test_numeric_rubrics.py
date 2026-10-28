from decimal import Decimal

import pytest

from rag_system.evaluation.numeric_rubrics import NumericRubric, score_numeric


@pytest.mark.parametrize("answer", ["-0.02", "(0.02)", "−0.02 [S1]"])
def test_negative_ratios_keep_sign(answer):
    rule = NumericRubric(Decimal("-0.02"), "ratio", 2, reviewed=True)
    assert score_numeric(answer, rule).status == "correct"
    assert score_numeric("0.02", rule).status == "incorrect"
    assert score_numeric("-0.01", rule).status == "incorrect"


@pytest.mark.parametrize(
    "answer", ["$2,500,000", "USD 2.5 million", "2.5 USD millions", "$0.0025 billion"]
)
def test_currency_scaling(answer):
    rule = NumericRubric(Decimal("2500000"), "usd", 0, reviewed=True)
    assert score_numeric(answer, rule).status == "correct"


def test_percent_is_not_percentage_points():
    rule = NumericRubric(Decimal("-3"), "percentage_points", 1, reviewed=True)
    assert score_numeric("-3 percentage points", rule).status == "correct"
    assert score_numeric("-3%", rule).status == "needs_review"
    assert score_numeric("3 pp", rule).status == "incorrect"


def test_ratio_percentage_conversion_requires_explicit_permission():
    rule = NumericRubric(Decimal("0.25"), "ratio", 2, reviewed=True)
    assert score_numeric("25%", rule).status == "needs_review"
    permitted = NumericRubric(Decimal("0.25"), "ratio", 2, True, True)
    assert score_numeric("25%", permitted).status == "correct"


@pytest.mark.parametrize(
    "answer", ["FY2022 value was 0.25", "0.25 or 0.30", "NaN", "1,23", "(-0.25)", "USD 25%"]
)
def test_ambiguous_output_is_not_silently_scored(answer):
    rule = NumericRubric(Decimal("0.25"), "ratio", 2, reviewed=True)
    assert score_numeric(answer, rule).status == "needs_review"


def test_unreviewed_reference_is_blocked():
    assert score_numeric("1", NumericRubric(Decimal("1"), "ratio", 2)).status == "blocked"


def test_rounding_and_abstention():
    rule = NumericRubric(Decimal("1.24"), "ratio", 2, reviewed=True)
    assert score_numeric("1.235", rule).status == "correct"
    assert score_numeric("1.234", rule).status == "incorrect"
    assert score_numeric("INSUFFICIENT_CONTEXT", rule).status == "incorrect"


def test_bad_rubric_rejected():
    with pytest.raises(ValueError):
        NumericRubric(Decimal("NaN"), "ratio", 2)
    with pytest.raises(ValueError):
        NumericRubric(Decimal("1"), "ratio", -1)
