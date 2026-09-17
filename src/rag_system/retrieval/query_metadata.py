"""Conservative filing-metadata extraction from finance questions."""

from __future__ import annotations

import re
from collections.abc import Mapping

_YEAR = re.compile(r"\b(?:FY)?(20\d{2})\b", re.IGNORECASE)
_COMPANY_PATTERNS = (
    re.compile(r"\b(?:for|at|of)\s+([A-Z0-9][A-Z0-9 .&-]*?)(?:\?|,|\.|\s+based\b|\s+give\b|\s+answer\b|\s+what\b|\s+is\b|$)"),
    re.compile(r"\bIs\s+([A-Z0-9][A-Z0-9 .&-]*?)(?:\s+(?:a|an|the)\b)", re.IGNORECASE),
)


def filing_metadata_filter(question: str) -> Mapping[str, object]:
    """Return an exact filing-name filter only when company and fiscal year are clear."""
    year = _YEAR.search(question)
    company = next((pattern.search(question) for pattern in _COMPANY_PATTERNS if pattern.search(question)), None)
    if not year or not company:
        return {}
    normalized_company = re.sub(r"[^A-Za-z0-9]", "", company.group(1)).upper()
    if not normalized_company:
        return {}
    return {"document_name": f"{normalized_company}_{year.group(1)}_10K.pdf"}
