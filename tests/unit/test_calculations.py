import copy
import json
from dataclasses import replace
from decimal import Decimal, DecimalException

import pytest

from rag_system.generation.answering import GroundedAnswerGenerator
from rag_system.generation.calculations import (
    _decimal,
    calculation_repair_issues,
    directional_contradiction,
    evaluate,
    validate_calculations,
)
from rag_system.generation.evidence import evidence_prompt, inspect_evidence_answer
from rag_system.schemas import DocumentChunk, RetrievedChunk


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Debt increased from 150868 million in 2021 to 150639 million in 2022.", True),
        ("Debt decreased from 150868 million in 2021 to 150639 million in 2022.", False),
        ("Income rose from -20 million to -10 million.", False),
        ("Income fell from -20 million to -10 million.", True),
        ("Debt increased from 10 million to 10 million.", True),
        ("Sales increased from 900 million to 1 billion.", False),
    ],
)
def test_explicit_direction_checks(text, expected):
    assert directional_contradiction(text) is expected


def test_direction_checked_after_computing_placeholders():
    p = payload()
    p["answer"] = "Revenue decreased from 40 million to {{growth}} million."
    assert validate_calculations(p)[1] == "directional_contradiction"


def payload():
    return {
        "answer": "Revenue grew by {{growth}}%.",
        "period": "2025",
        "unit": "percent",
        "evidence": [{"source_id": "S1", "quote": "Revenue 2025 120 2024 80 million"}],
        "calculations": [
            {
                "id": "growth",
                "expression": "(new-old)/old*100",
                "result": "50.0",
                "decimal_places": 1,
                "operands": [
                    {
                        "name": "new",
                        "value": "120",
                        "evidence_index": 0,
                        "metric": "revenue",
                        "period": "2025",
                        "unit": "USD million",
                    },
                    {
                        "name": "old",
                        "value": "80",
                        "evidence_index": 0,
                        "metric": "revenue",
                        "period": "2024",
                        "unit": "USD million",
                    },
                ],
            }
        ],
    }


def test_mixed_case_identifiers_keep_exact_case_matching():
    p = payload()
    p["answer"] = "Growth {{growthRate}}%."
    calc = p["calculations"][0]
    calc["id"] = "growthRate"
    calc["operands"][0]["name"] = "incomeNew"
    calc["expression"] = "(incomeNew-old)/old*100"
    assert validate_calculations(p)[1] == "accepted"
    calc["expression"] = "(incomenew-old)/old*100"
    assert validate_calculations(p)[1] == "invalid_calculations"


@pytest.mark.parametrize("name", ["2025_rate", "a.b", "a()", "a" * 21, "évalue", "__import__"])
def test_unsafe_or_unbounded_names_remain_rejected(name):
    p = payload()
    p["calculations"][0]["id"] = name
    p["answer"] = "Result {{" + name + "}}"
    assert validate_calculations(p)[1] == "invalid_calculations"


def source():
    return RetrievedChunk(
        DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            document_name="example.pdf",
            chunk_index=0,
            text="Revenue 2025 120 2024 80 million",
            token_count=7,
            chunking_strategy="fixed_token",
            page_numbers=(3,),
            section_titles=(),
        ),
        score=1.0,
    )


def test_repair_reports_sign_and_formula_errors_without_changing_payload():
    p = payload()
    p["evidence"][0]["quote"] = "Dividend outflow (120) Income 80"
    p["calculations"][0]["expression"] = "120/80"
    s = source()
    s = replace(s, chunk=replace(s.chunk, text=p["evidence"][0]["quote"]))
    before = copy.deepcopy(p)
    issues = calculation_repair_issues(p, {"S1": s})
    assert {i["code"] for i in issues} == {
        "signed_operand_mismatch",
        "financial_literals_in_expression",
        "expression_operand_names_mismatch",
        "check_operand_evidence_link",
    }
    assert (
        next(i for i in issues if i["code"] == "signed_operand_mismatch")["quoted_signed_value"]
        == "-120"
    )
    assert p == before
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"


def test_evidence_link_hints_are_verified_candidates_not_automatic_repairs():
    p = payload()
    p["evidence"] = [
        {"source_id": "S1", "quote": "Revenue 80"},
        {"source_id": "S2", "quote": "Income 120"},
        {"source_id": "S1", "quote": "Invented 120"},
    ]
    sources = {
        "S1": replace(source(), chunk=replace(source().chunk, text="Revenue 80")),
        "S2": replace(source(), chunk=replace(source().chunk, text="Income 120")),
    }
    before = copy.deepcopy(p)
    issues = calculation_repair_issues(p, sources)
    link = next(i for i in issues if i["code"] == "check_operand_evidence_link")
    assert link["matching_evidence_indices"] == [1]
    assert p == before
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"
    p["calculations"][0]["operands"][0]["evidence_index"] = 1
    assert validate_calculations(p)[1] == "accepted"


def test_repair_numeric_hint_requires_quote_membership():
    p = payload()
    p["evidence"][0]["quote"] = "Invented (120)"
    issues = calculation_repair_issues(p, {"S1": source()})
    assert not any(i["code"] == "signed_operand_mismatch" for i in issues)


def test_repair_invalid_name_and_decimal_are_not_echoed():
    p = payload()
    p["calculations"][0]["operands"][0].update(name="2025_rate", value="(120)")
    issues = calculation_repair_issues(p, {"S1": source()})
    assert {"invalid_or_duplicate_operand_name", "invalid_decimal_string"} <= {
        i["code"] for i in issues
    }
    assert "2025_rate" not in json.dumps(issues)


def test_valid_calculation_has_no_repair_issues():
    assert calculation_repair_issues(payload(), {"S1": source()}) == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("(1,234.50)", "-1234.50"),
        ("6,489", "6489"),
        ("-2,400", "-2400"),
        ("(116)", "-116"),
        ("0.80", "0.80"),
    ],
)
def test_financial_decimal_notation_preserves_value(monkeypatch, raw, expected):
    monkeypatch.setenv("FINANCIAL_DECIMAL_INPUT", "1")
    assert _decimal(raw) == Decimal(expected)


@pytest.mark.parametrize(
    "raw",
    ["1,23", "12,34,567", "(-120)", "(120", "120)", "$120", "1e3", "1.234,50", "--120", "NaN"],
)
def test_ambiguous_financial_formats_rejected(monkeypatch, raw):
    monkeypatch.setenv("FINANCIAL_DECIMAL_INPUT", "1")
    with pytest.raises(ValueError):
        _decimal(raw)


def test_financial_input_does_not_correct_wrong_sign_or_invent_operand(monkeypatch):
    monkeypatch.setenv("FINANCIAL_DECIMAL_INPUT", "1")
    p = payload()
    p["evidence"][0]["quote"] = "Capital expenditure (1,200)"
    calc = p["calculations"][0]
    calc["operands"] = [dict(calc["operands"][0], value="(1,200)")]
    calc["expression"] = "-new"
    assert validate_calculations(p)[1] == "accepted"
    calc["operands"][0]["value"] = "1,200"
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"
    calc["operands"][0]["value"] = "(1,201)"
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"


def test_decimal_rendering_and_bad_arithmetic():
    p = payload()
    assert validate_calculations(p) == ("Revenue grew by 50.0%.", "accepted")
    p["calculations"][0]["result"] = "49.0"
    assert validate_calculations(p) == ("Revenue grew by 50.0%.", "accepted")
    p["calculations"][0].pop("result")
    assert validate_calculations(p) == ("Revenue grew by 50.0%.", "accepted")


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').getcwd()",
        "new.real",
        "new**10000000",
        "[new][0]",
        "new//old",
        "new%old",
        "True+new",
        "new+999",
        "new/0",
        "new" * 300,
        "(new-old)/(old-old)",
    ],
)
def test_unsafe_or_unbounded_expressions_rejected(expression):
    with pytest.raises((ValueError, SyntaxError, DecimalException)):
        evaluate(expression, {"new": Decimal(120), "old": Decimal(80)})


def test_signed_source_values_and_conversion():
    p = payload()
    p["evidence"][0]["quote"] = "Capital spending (2,500) million"
    c = p["calculations"][0]
    c["operands"] = [dict(c["operands"][0], value="-2500")]
    c.update(expression="-new/1000", result="2.5")
    assert validate_calculations(p)[1] == "accepted"
    c["operands"][0]["value"] = "2500"
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"


@pytest.mark.parametrize("value", ["12", "20", "1200"])
def test_operand_cannot_match_partial_number(value):
    p = payload()
    p["calculations"][0]["operands"][0]["value"] = value
    assert validate_calculations(p)[1] == "calculation_operand_not_in_evidence"


def test_schema_and_placeholder_checks():
    p = payload()
    for mutate in [
        lambda x: x.pop("calculations"),
        lambda x: x.update(answer="Revenue grew by 50%"),
        lambda x: x.update(answer="{{growth}} {{growth}}"),
        lambda x: x["calculations"][0].update(decimal_places=True),
        lambda x: x["calculations"][0]["operands"][0].update(evidence_index=-1),
        lambda x: x["calculations"][0]["operands"][0].update(evidence_index=True),
        lambda x: x["calculations"][0]["operands"][0].update(value="NaN"),
        lambda x: x["calculations"][0]["operands"][0].update(period=""),
        lambda x: x["calculations"].append(copy.deepcopy(x["calculations"][0])),
    ]:
        changed = copy.deepcopy(p)
        mutate(changed)
        assert validate_calculations(changed)[1] == "invalid_calculations"


def test_round_half_up():
    p = payload()
    c = p["calculations"][0]
    c.update(expression="new/old", result="1.01", decimal_places=2)
    p["evidence"][0]["quote"] = "Values 201 200"
    c["operands"][0]["value"] = "201"
    c["operands"][1]["value"] = "200"
    assert validate_calculations(p)[1] == "accepted"


def test_opt_in_runs_after_source_validation(monkeypatch):
    p = payload()
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    result, status = inspect_evidence_answer(json.dumps(p), {"S1": source()})
    assert status == "accepted"
    assert result.text == "Revenue grew by 50.0%. [S1]"
    p["evidence"][0]["quote"] = "Invented row 120 80"
    assert inspect_evidence_answer(json.dumps(p), {"S1": source()})[1] == "quote_not_in_source"


def test_disabled_mode_and_direct_lookup(monkeypatch):
    p = payload()
    p.update(answer="Revenue was 120 million.", calculations=[])
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    assert inspect_evidence_answer(json.dumps(p), {"S1": source()})[1] == "accepted"
    p.pop("calculations")
    monkeypatch.delenv("CALCULATION_VALIDATION")
    assert inspect_evidence_answer(json.dumps(p), {"S1": source()})[1] == "accepted"
    assert "CALCULATION PROTOCOL" not in evidence_prompt("Revenue?", {"S1": source()})


@pytest.mark.parametrize("repair_succeeds", [True, False])
def test_generator_repairs_once_then_accepts_or_abstains(monkeypatch, repair_succeeds):
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    bad = payload()
    bad["calculations"][0]["operands"][0]["value"] = "130"

    class Provider:
        def __init__(self):
            self.prompts = []

        def generate(self, prompt):
            self.prompts.append(prompt)
            return json.dumps(payload() if len(self.prompts) == 2 and repair_succeeds else bad)

    provider = Provider()
    result = GroundedAnswerGenerator(provider, True).answer("Growth?", (source(),))
    assert len(provider.prompts) == 2
    assert "Copy signed operand values" in provider.prompts[1]
    assert result.insufficient_context is not repair_succeeds
    assert result.diagnostics[0]["status"] == "calculation_operand_not_in_evidence"
    assert result.diagnostics[0]["calculation_protocol"] == "decimal-render-v2"


def test_generator_computes_instead_of_retrying_model_arithmetic(monkeypatch):
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    p = payload()
    p["calculations"][0]["result"] = "999.0"

    class Provider:
        calls = 0

        def generate(self, prompt):
            self.calls += 1
            return json.dumps(p)

    provider = Provider()
    result = GroundedAnswerGenerator(provider, True).answer("Growth?", (source(),))
    assert provider.calls == 1
    assert result.text == "Revenue grew by 50.0%. [S1]"
    assert "999" not in result.text


def test_signed_outflow_repair_preserves_evidence_and_renders_magnitude(monkeypatch):
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    p = payload()
    p["answer"] = "Capital spending was {{growth}} billion."
    p["evidence"][0]["quote"] = "Capital spending (2,500) million"
    c = p["calculations"][0]
    c["operands"] = [dict(c["operands"][0], value="2500")]
    c.update(expression="new/1000", decimal_places=3)
    from dataclasses import replace

    item = source()
    item = replace(item, chunk=replace(item.chunk, text=p["evidence"][0]["quote"]))

    class Provider:
        calls = 0

        def generate(self, prompt):
            self.calls += 1
            if self.calls == 2:
                assert "keep the minus sign" in prompt
                c["operands"][0]["value"] = "-2500"
                c["expression"] = "-new/1000"
            return json.dumps(p)

    result = GroundedAnswerGenerator(Provider(), True).answer("Capital spending?", (item,))
    assert result.text == "Capital spending was 2.500 billion. [S1]"
    assert [d["status"] for d in result.diagnostics] == [
        "calculation_operand_not_in_evidence",
        "accepted",
    ]


def test_free_cash_flow_adds_signed_capex():
    p = payload()
    p["evidence"][0]["quote"] = "Operating cash 900; capital spending (125)"
    c = p["calculations"][0]
    c["operands"][0]["value"] = "900"
    c["operands"][1]["value"] = "-125"
    c.update(expression="new+old", decimal_places=0)
    p["answer"] = "Free cash flow was {{growth}}."
    assert validate_calculations(p) == ("Free cash flow was 775.", "accepted")
