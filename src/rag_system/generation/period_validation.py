"""Conservative conflicts with singular dated statement headings, not column inference."""

import re
from collections.abc import Mapping

from rag_system.schemas import RetrievedChunk

_HEADING = re.compile(
    r"\b(?:for\s+the\s+)?year\s+ended\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+((?:19|20)\d{2})\b",
    re.IGNORECASE,
)


def validate_operand_periods(payload: dict, sources: Mapping[str, RetrievedChunk]) -> str:
    """Call after calculation schema and quote validation. Ambiguity is not a conflict."""
    for calculation in payload["calculations"]:
        for operand in calculation["operands"]:
            years = set(re.findall(r"(?:19|20)\d{2}", operand["period"]))
            if len(years) != 1:
                continue
            evidence = payload["evidence"][operand["evidence_index"]]
            text = " ".join(sources[evidence["source_id"]].chunk.text.split())
            quote = " ".join(evidence["quote"].split())
            if text.count(quote) != 1:
                continue
            # Only a nearby explicit singular heading, with no competing years
            # between heading and row, supplies a sufficiently clear conflict.
            prefix = text[: text.index(quote)]
            headings = list(_HEADING.finditer(prefix))
            if not headings:
                continue
            heading = headings[-1]
            if len(prefix) - heading.start() > 1200:
                continue
            between = prefix[heading.end() :]
            if re.search(r"\b(?:19|20)\d{2}\b|\byears\s+ended\b", between, re.IGNORECASE):
                continue
            if heading.group(1) not in years:
                return "calculation_period_conflict"
    return "accepted"
