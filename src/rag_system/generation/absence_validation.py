"""Conservative acquisition-absence checks; not a general entailment verifier."""

import re

_ABSENCE = re.compile(
    r"\b(?:no\s+|(?:did|does|has|have|had|were|was)\s+not\s+"
    r"(?:report(?:ed)?|complete(?:d)?|make|made|undertake|have|had|conduct(?:ed)?)\s+(?:any\s+)?)"
    r"(?P<scope>(?:major|material|significant)\s+)?acquisitions?\b",
    re.I,
)
_YEAR = re.compile(r"\b(?:FY\s*)?((?:19|20)\d{2})\b", re.I)


def _claims(text):
    for clause in re.split(r"[;.!?]|\b(?:while|whereas|but)\b", text, flags=re.I):
        matches = list(_ABSENCE.finditer(clause))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(clause)
            suffix = clause[match.end() : end]
            # Stop before a separate positive assertion rather than assigning
            # its year to the absence statement.
            suffix = re.split(r",\s*(?:and\s+)?(?:in|during)\b", suffix, maxsplit=1, flags=re.I)[0]
            years = set(_YEAR.findall(suffix))
            if not years:
                prefix = clause[max(0, match.start() - 50) : match.start()]
                found = _YEAR.findall(prefix)
                years = set(found[-1:])
            yield years, (match.group("scope") or "").strip().lower()


def validate_acquisition_absence(payload):
    claims = list(_claims(payload["answer"]))
    if not claims:
        return "accepted"
    supported = {}
    for entry in payload["evidence"]:
        quote = entry["quote"]
        # Planned activity and lack of information do not establish historical absence.
        if re.search(r"plan|expect|intend|forecast|no (?:information|evidence)", quote, re.I):
            continue
        for years, scope in _claims(quote):
            supported.setdefault(scope, set()).update(years)
    for years, scope in claims:
        if not years or not years <= (supported.get(scope, set()) | supported.get("", set())):
            return "unsupported_acquisition_absence"
    return "accepted"
