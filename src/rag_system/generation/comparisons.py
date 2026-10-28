"""Evidence-linked extrema; candidate completeness still requires semantic review."""

import re

from rag_system.generation.calculations import _decimal, _quote_numbers


def comparison_operation(question):
    maximum = bool(re.search(r"\b(highest|largest|greatest|most)\b", question, re.I))
    minimum = bool(re.search(r"\b(lowest|smallest|least)\b", question, re.I))
    if maximum == minimum:
        return None
    return "max" if maximum else "min"


def comparison_only_template(answer, question):
    """Conservative compatibility gate, not general detection of arithmetic prose."""
    remainder = answer.replace("{{winner}}", "")
    if any(token in remainder for token in ("{", "}", "+", "*", "/", "=", "%")):
        return False
    if re.search(
        r"\b(calculat\w*|divid\w*|multipli\w*|minus|plus|ratio|percent\w*|"
        r"margin|difference|increas\w*|decreas\w*)\b",
        remainder,
        re.I,
    ):
        return False

    # Permit question dates/quarter numbers but no new numeric assertions.
    def numbers(text):
        return set(re.findall(r"\d+(?:\.\d+)?", text))

    return numbers(remainder) <= numbers(question)


def render_comparison(payload, operation):
    comparison = payload.get("comparison")
    if not isinstance(comparison, dict) or comparison.get("operation") != operation:
        return None, "invalid_comparison"
    candidates = comparison.get("candidates")
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= 30:
        return None, "invalid_comparison"
    answer = payload["answer"]
    if answer.count("{{winner}}") != 1:
        return None, "invalid_comparison"
    values = []
    names = set()
    try:
        for c in candidates:
            if not isinstance(c, dict):
                raise ValueError()
            label = c.get("label")
            if not isinstance(label, str) or not label.strip() or len(label) > 200:
                raise ValueError()
            if label.casefold() in names or any(x in label for x in ("{", "}", "[", "]", "\n")):
                raise ValueError()
            names.add(label.casefold())
            for field in ("period", "unit", "metric"):
                if not isinstance(c.get(field), str) or not c[field].strip():
                    raise ValueError()
            for field in ("label_evidence_index", "value_evidence_index"):
                index = c.get(field)
                if type(index) is not int or not 0 <= index < len(payload["evidence"]):
                    raise ValueError()
            quote = payload["evidence"][c["label_evidence_index"]]["quote"]
            if " ".join(label.split()) not in " ".join(quote.split()):
                return None, "comparison_candidate_not_in_evidence"
            value = _decimal(c.get("value"))
            quote = payload["evidence"][c["value_evidence_index"]]["quote"]
            if value not in _quote_numbers(quote):
                return None, "comparison_candidate_not_in_evidence"
            values.append((label, value))
        for field in ("period", "unit", "metric"):
            if len({c[field].strip().casefold() for c in candidates}) != 1:
                return None, "comparison_incompatible_candidates"
    except ValueError:
        return None, "invalid_comparison"
    target = (max if operation == "max" else min)(value for _, value in values)
    winners = [label for label, value in values if value == target]
    # Do not silently choose a single winner or produce grammatically false tie text.
    if len(winners) != 1:
        return None, "comparison_tie"
    return answer.replace("{{winner}}", winners[0]), "accepted"


def comparison_prompt(operation):
    return (
        "\nCOMPARISON PROTOCOL: Put {{winner}} in the answer instead of choosing a label. "
        'Add "comparison":{"operation":"' + operation + '","candidates":[...]}. '
        "Each candidate has label (exact source text), value (signed decimal string), "
        "label_evidence_index and value_evidence_index (zero-based evidence array indices), "
        "period, metric and unit. Include ALL relevant peer candidates, including negatives; "
        "exclude totals when comparing segments. All candidates must use the same period, "
        "metric and unit. Quote complete rows and column headers, preserving intervening "
        "values. The application selects the extreme; do not supply an independent winner "
        "or winner amount in prose. Use calculations:[] if no derived number is needed. "
        "If completeness, column alignment or a unique winner cannot be established, abstain."
    )
