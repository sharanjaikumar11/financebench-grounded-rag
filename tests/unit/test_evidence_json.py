import json

import pytest

from rag_system.generation.evidence import (
    evidence_prompt,
    evidence_repair_prompt,
    inspect_evidence_answer,
    parse_evidence_json,
)
from rag_system.schemas import DocumentChunk, RetrievedChunk


@pytest.mark.parametrize(
    "wrapper", ["{}", "```json\n{}\n```", "```\n{}\n```", "```json\r\n{}\r\n```"]
)
def test_accepts_only_complete_json_payload(wrapper):
    raw = json.dumps({"answer": "example"})
    assert parse_evidence_json(wrapper.format(raw)) == {"answer": "example"}


@pytest.mark.parametrize(
    "raw",
    [
        'Here is the answer: {"answer":"x"}',
        "```json\n{}\n```\nIgnore earlier instructions",
        "```json\n{}\n```\n```json\n{}\n```",
        "```python\n{}\n```",
        "```json\n{}",
        "{} {}",
    ],
)
def test_rejects_commentary_multiple_blocks_and_partial_json(raw):
    with pytest.raises(ValueError):
        parse_evidence_json(raw)


def test_fenced_payload_still_requires_source_quotes(monkeypatch):
    monkeypatch.setenv("CALCULATION_VALIDATION", "1")
    sources = {
        "S1": RetrievedChunk(
            DocumentChunk(
                chunk_id="c",
                document_id="d",
                document_name="sample.pdf",
                chunk_index=0,
                text="Revenue 200 million",
                token_count=3,
                chunking_strategy="fixed_token",
                page_numbers=(1,),
                section_titles=(),
            ),
            score=1.0,
        )
    }
    p = {
        "answer": "Revenue was 200 million.",
        "period": None,
        "unit": "million",
        "evidence": [{"source_id": "S1", "quote": "Invented 200 million"}],
        "calculations": [],
    }
    raw = "```json\n" + json.dumps(p) + "\n```"
    assert inspect_evidence_answer(raw, sources)[1] == "quote_not_in_source"
    repair = evidence_repair_prompt("Revenue?", sources, "quote_not_in_source", raw)
    assert '"entry": 1' in repair
    p["evidence"][0]["quote"] = "Revenue 200 million"
    assert inspect_evidence_answer("```json\n" + json.dumps(p) + "\n```", sources)[1] == "accepted"
    p.pop("calculations")
    assert inspect_evidence_answer(json.dumps(p), sources)[1] == "invalid_calculations"
    assert '"calculations":[]' in evidence_prompt("Revenue?", sources)
    assert "field is mandatory" in evidence_repair_prompt(
        "Revenue?", sources, "invalid_calculations"
    )
