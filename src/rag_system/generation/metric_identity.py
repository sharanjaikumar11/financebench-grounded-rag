"""Conservative identity checks for attribution-sensitive calculation operands.

Not a general semantic verifier: period/column alignment and direct lookups remain
outside this check. No benchmark entities, answers or reference pages are used.
"""

import re

INCOME = re.compile(r"\bnet\s+(?:income|earnings|profit|loss)\b", re.I)
OWNERS = r"(?:share\s*holders?|share\s*owners?|stock\s*holders?|owners of (?:the )?parent)"
ATTRIBUTION = re.compile(
    r"\b(?:net\s+(?:income|earnings|profit|loss))\b.{0,100}?"
    r"\battributable\s+to\s+(?:(?:the|common|ordinary)\s+)*" + OWNERS,
    re.I,
)


def requests_shareholder_income(question):
    return bool(ATTRIBUTION.search(" ".join(question.split())))


def validate_metric_identity(payload, question):
    if not requests_shareholder_income(question):
        return "accepted"
    calculations = payload.get("calculations")
    if not isinstance(calculations, list):
        return "accepted"  # Calculation schema validation handles malformed input.
    for calculation in calculations:
        if not isinstance(calculation, dict):
            continue
        operands = calculation.get("operands")
        if not isinstance(operands, list):
            continue
        for operand in operands:
            if not isinstance(operand, dict):
                continue
            metric = operand.get("metric")
            if not isinstance(metric, str) or not INCOME.search(metric):
                continue
            if not ATTRIBUTION.search(" ".join(metric.split())):
                return "income_attribution_mismatch"
            index = operand.get("evidence_index")
            if type(index) is not int or not 0 <= index < len(payload["evidence"]):
                continue  # Invalid indices are rejected by calculation validation.
            quote = " ".join(payload["evidence"][index]["quote"].split())
            if not ATTRIBUTION.search(quote):
                return "income_attribution_not_in_evidence"
    return "accepted"


METRIC_IDENTITY_PROMPT = (
    "\nMETRIC IDENTITY: This question explicitly requests net income attributable to "
    "shareholders. For calculations, identify the income operand with that exact metric "
    "meaning and quote the attribution row label together with its value. Consolidated "
    "net income and income attributable to noncontrolling interests are not substitutes. "
    "Do not rename a consolidated row as shareholder income or choose a different metric "
    "because the rounded ratio matches. If the supplied evidence lacks the requested "
    "income basis, abstain. No reference answer is available to infer missing values."
)
