"""Conservative filing-metadata extraction from finance questions."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_YEAR = re.compile(r"\b(?:FY)?(20\d{2})\b", re.IGNORECASE)


def normalize_fiscal_periods(question: str) -> str:
    """Expand explicitly fiscal short years, not arbitrary two-digit numbers."""
    question = re.sub(r"\bFY\s*['’]?(\d{2})\b", r"FY20\1", question, flags=re.I)
    return re.sub(r"\b(Q[1-4])\s+of\s+(?:fiscal\s+year\s+)?", r"\1 ", question, flags=re.I)


def indexed_filing_filter(question: str, document_names: Sequence[str]) -> dict[str, object]:
    """Scope to indexed companies/periods; preserve candidates when type is ambiguous."""
    question = normalize_fiscal_periods(question)

    def compact(value):
        return re.sub(r"[^A-Z0-9]", "", re.sub(r"\band\b", "", value, flags=re.I).upper())

    catalog = []
    for name in document_names:
        match = re.match(r"(.+?)_(20\d{2})(?:Q([1-4]))?_(.+?)(?:\.pdf)?$", name, re.I)
        if match:
            company, year, quarter, kind = match.groups()
            catalog.append((name, company.upper(), year, quarter, kind))
    companies = {item[1] for item in catalog}
    words = re.findall(r"[A-Za-z0-9]+", re.sub(r"\band\b", " ", question, flags=re.I))
    name_spans = {
        compact("".join(words[start : start + width]))
        for start in range(len(words))
        for width in range(1, 7)
    }
    matched = {company for company in companies if compact(company) in name_spans}
    if not matched:
        tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b", question)
        for token in tokens:
            possible = set()
            for company in companies:
                words = company.split("_")
                initials = "".join(word[0] for word in words)
                joined = "N".join(word[0] for word in words)
                if len(words) > 1 and len(token) >= 2 and token.upper() in {initials, joined}:
                    possible.add(company)
                elif token.isupper() and len(token) >= 3 and compact(company).startswith(token):
                    possible.add(company)
            if len(possible) == 1:
                matched.update(possible)
    if len(matched) != 1:
        return {}
    candidates = [item for item in catalog if item[1] in matched]
    years = re.findall(r"\b(?:FY)?(20\d{2})\b", question, re.I)
    if years:
        candidates = [item for item in candidates if item[2] == max(years)]
    quarter = re.search(r"\bQ([1-4])\b", question, re.I)
    if quarter:
        quarterly = [item for item in candidates if item[3] == quarter.group(1)]
        # An annual filing can contain quarterly dividends/comparative results.
        # If no requested-quarter filing exists, keep same-year annual evidence,
        # never substitute a different quarterly period.
        candidates = quarterly or [item for item in candidates if not item[3]]
    # Explicit document types constrain routing; otherwise retain same-period
    # earnings releases as well as annual reports for evidence-based retrieval.
    kind = re.search(r"\b10[- ]?([KQ])\b", question, re.I)
    if kind:
        candidates = [
            item for item in candidates if "10" + kind.group(1).upper() in item[4].upper()
        ]
    elif years and not quarter and not re.search(r"\bdated|\b\d{1,2},?\s+20\d{2}", question):
        annual = [item for item in candidates if "10K" in item[4].upper()]
        nonquarterly = [item for item in candidates if not item[3]]
        if annual and not any("EARNINGS" in item[4].upper() for item in candidates):
            candidates = annual
        elif nonquarterly and not any("EARNINGS" in item[4].upper() for item in candidates):
            candidates = nonquarterly
    names = sorted({item[0] for item in candidates})
    if not names:
        # A known company but absent period must not silently search other years.
        return {"document_names": []}
    return {"document_name": names[0]} if len(names) == 1 else {"document_names": names}


_COMPANY_PATTERNS = (
    re.compile(
        r"\b(?:for|at|of)\s+([A-Z0-9][A-Z0-9 .&-]*?)(?:\?|,|\.|\s+based\b|\s+give\b|\s+answer\b|\s+what\b|\s+is\b|$)"
    ),
    re.compile(r"\bIs\s+([A-Z0-9][A-Z0-9 .&-]*?)(?:\s+(?:a|an|the)\b)", re.IGNORECASE),
)


def filing_metadata_filter(question: str) -> Mapping[str, object]:
    """Return an exact filing-name filter only when company and fiscal year are clear."""
    year = _YEAR.search(question)
    company = next(
        (pattern.search(question) for pattern in _COMPANY_PATTERNS if pattern.search(question)),
        None,
    )
    if not year or not company:
        return {}
    normalized_company = re.sub(r"[^A-Za-z0-9]", "", company.group(1)).upper()
    if not normalized_company:
        return {}
    return {"document_name": f"{normalized_company}_{year.group(1)}_10K.pdf"}
