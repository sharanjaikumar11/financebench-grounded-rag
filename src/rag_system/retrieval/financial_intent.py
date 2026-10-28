"""Generic financial concepts for lexical expansion and evidence ranking.

These rules contain no filing names, page numbers, reference values or case IDs.
They are an opt-in text-ranking experiment, not a table extractor.
"""

import re

from rag_system.schemas import RetrievedChunk


def operand_patterns(query: str) -> tuple[str, ...]:
    """Required row families for explicit multi-input financial questions."""
    patterns = []
    if re.search(r"return on assets|\broa\b", query, re.I):
        patterns += [r"total assets", r"net (?:income|loss|earnings)(?: loss)?"]
    if re.search(r"inventory turnover", query, re.I):
        patterns += [
            r"inventor(?:y|ies)",
            r"(?:total )?cost of (?:sales|revenue|products sold|goods sold)",
        ]
    if re.search(r"payout", query, re.I):
        patterns += [
            r"(?:cash )?dividends(?: paid)?",
            r"net income attributable to (?:common )?(?:shareowners|shareholders)(?: of [a-z ]{1,65})?",
        ]
    if re.search(r"capex|capital expenditures?", query, re.I) and re.search(
        r"revenue|sales", query, re.I
    ):
        patterns += [
            r"capital expenditures|purchases of property (?:and )?equipment",
            r"(?:total )?(?:net )?(?:revenues|revenue|sales)",
        ]
    return tuple(patterns)


def has_transaction_event(text: str) -> bool:
    text = " ".join(text.lower().split())
    dated = re.search(
        r"\b(?:on|in) (?:january|february|march|april|may|june|july|august|september|october|november|december) "
        r"(?:\d{1,2},? )?(?:19|20)\d{2}\b",
        text,
    )
    return bool(
        dated and re.search(r"completed (?:the )?acquisition|(?:we|company) acquired", text)
    )


def transaction_coverage_order(
    candidates: list[RetrievedChunk], query: str, limit: int
) -> list[RetrievedChunk]:
    """Fill an absent transaction-note slot without reranking already covered queries."""
    if not re.search(r"acquisitions?", query, re.I) or limit < 1:
        return candidates
    if any(has_transaction_event(item.chunk.text) for item in candidates[:limit]):
        return candidates
    match = next((item for item in candidates if has_transaction_event(item.chunk.text)), None)
    return [match] + [item for item in candidates if item != match] if match else candidates


def operand_coverage_order(
    candidates: list[RetrievedChunk], query: str, limit: int
) -> list[RetrievedChunk]:
    """Reserve existing candidates for distinct operands, retaining ranked remainder."""
    if limit < 1:
        return candidates
    chosen = []
    for pattern in operand_patterns(query):
        kind = (
            r"balance sheets?"
            if "assets" in pattern or "inventor" in pattern
            else r"statements? of cash flows?"
            if "dividend" in pattern or "expenditures" in pattern
            else r"statements? of (?:income|operations|earnings)"
        )
        heading = re.compile(
            r"\bconsolidated " + kind + r".{0,130}?(?:years? ended|in millions|in thousands)", re.I
        )
        headers = [
            item.chunk
            for item in candidates
            if heading.search(" ".join(item.chunk.text.split()))
            and not re.search(r"we have audited|condensed consolidating", item.chunk.text, re.I)
        ]

        def has_nearby_header(item):
            return any(
                h.document_id == item.chunk.document_id
                and h.chunking_strategy == item.chunk.chunking_strategy
                and 0 <= item.chunk.chunk_index - h.chunk_index <= 2
                for h in headers
            )

        for item in sorted(candidates, key=has_nearby_header, reverse=True):
            text = re.sub(r"[^a-z0-9]+", " ", item.chunk.text.lower())
            if re.search(r"condensed consolidating|parent guarantor|we have audited", text):
                continue
            if re.search(r"\b(?:" + pattern + r")\s+\d", text):
                if item not in chosen:
                    chosen.append(item)
                break
        if len(chosen) >= limit:
            break
    return chosen + [item for item in candidates if item not in chosen]


# Query concept -> standard source terminology (used in any company's filings).
CONCEPTS = (
    (
        r"working capital|quick ratio",
        ("current assets", "current liabilities", "cash and cash equivalents", "inventories"),
    ),
    (r"ebitda|\bd&a\b", ("operating income", "depreciation and amortization", "net revenues")),
    (
        r"business segment.*net income|segment.*highest",
        ("segment results", "business segment", "net income"),
    ),
    (r"\bcogs\b|cost of goods sold", ("cost of revenue", "cost of sales", "cost of products sold")),
    (
        r"capex|capital expenditures?|capital intensive",
        (
            "capital expenditures",
            "purchases of property and equipment",
            "additions to property plant and equipment",
        ),
    ),
    (
        r"payout|cash dividends paid",
        ("dividends paid", "dividends", "net income attributable to shareowners"),
    ),
    (
        r"attributable to shareholders|attributable to shareowners",
        (
            "net income attributable to shareowners",
            "net income attributable to shareholders",
        ),
    ),
    (r"\bnet ar\b|accounts? receivable", ("accounts receivable", "trade receivables")),
    (r"\brevenue\b", ("net sales", "net revenues", "revenue")),
    (r"operating income", ("operating income", "income from operations")),
    (r"net income|net earnings", ("net income", "net income loss", "net earnings")),
    (r"\bppne\b|\bpp&e\b|fixed asset", ("property plant and equipment", "property and equipment")),
    (r"total assets|return on assets|\broa\b", ("total assets", "net income")),
    (
        r"inventory turnover",
        ("inventories", "inventory", "cost of sales", "cost of revenue", "cost of products sold"),
    ),
    (r"effective tax", ("effective tax rate", "effective income tax rate")),
    (r"acquisitions?", ("acquisitions", "acquired", "business combinations")),
    (
        r"legal battles|litigation|lawsuits?",
        ("legal proceedings", "litigation", "contingencies", "lawsuits"),
    ),
    (
        r"geograph|primarily operates",
        ("business overview", "reportable segments", "geographic", "divisions"),
    ),
    (
        r"registered.*exchange|securities.*registered",
        ("securities registered", "section 12", "title of each class", "trading symbol"),
    ),
    (r"\bceo\b|chief executive", ("chief executive officer", "appointed", "previously", "served")),
    (
        r"stable.*dividend|dividend.*trend",
        ("dividends", "consecutive years", "consecutive year", "dividend increases"),
    ),
    (
        r"paid dividends|dividends.*shareholders",
        ("dividends declared", "quarterly dividend", "cash dividends"),
    ),
    (r"\bdebt\b.*balance sheet", ("total debt", "long term debt", "debt maturing")),
    (
        r"cash flow.*(?:operations|investing|financing)|(?:operations|investing|financing).*cash flow",
        ("operating activities", "investing activities", "financing activities"),
    ),
)


def concept_phrases(query: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            phrase
            for pattern, phrases in CONCEPTS
            if re.search(pattern, query, re.I)
            for phrase in phrases
        )
    )


def numeric_row_phrases(text: str, query: str) -> tuple[str, ...]:
    """Recognize requested concepts followed by figures, not mere prose mentions."""
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return tuple(
        phrase
        for phrase in concept_phrases(query)
        if re.search(r"\b" + re.escape(phrase) + r"\s+(?:net\s+)?\d", normalized)
    )


def intent_relevance(text: str, query: str) -> float:
    """Prefer concept-bearing evidence; avoid auditing prose and generic headings."""
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    phrases = concept_phrases(query)
    matches = [phrase for phrase in phrases if phrase in normalized]
    score = min(len(matches), 4) * 0.35
    for phrase in matches:
        if re.search(re.escape(phrase) + r"\s+(?:net\s+)?\d", normalized):
            score += 0.25
    question = query.lower()
    income = r"(?:consolidated )?statements? of (?:income|operations)|income statements?"
    balance = r"balance sheets?|statements? of financial (?:position|condition)"
    cash = r"statements? of cash flows?"
    for requested, heading in (
        (r"income statement|statement of income", income),
        (r"balance sheet|financial position", balance),
        (r"cash flow statement|statement of cash flows", cash),
    ):
        if re.search(requested, question) and re.search(heading, normalized):
            score += 0.6
    if re.search(
        r"we have audited|independent registered public accounting|i have reviewed this|internal control over financial reporting",
        normalized,
    ):
        score -= 1.2
    if re.search(
        r"financial information of (?:the )?parent|financial information of registrant", normalized
    ):
        score -= 0.65
    return score
