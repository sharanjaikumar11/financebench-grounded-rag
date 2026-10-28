"""Opt-in numeric rubric v1: strict scalar scoring, never guess from prose.

Not wired to the legacy runner. References must be independently reviewed before
use. Ambiguous outputs require review rather than silently passing or failing.
"""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

VERSION = "numeric-rubric-v1"
Unit = Literal["usd", "ratio", "percent", "percentage_points"]


@dataclass(frozen=True)
class NumericRubric:
    expected: Decimal
    unit: Unit
    decimal_places: int
    reviewed: bool = False
    allow_percent_for_ratio: bool = False

    def __post_init__(self):
        if not isinstance(self.expected, Decimal) or not self.expected.is_finite():
            raise ValueError("Expected must be a finite Decimal in canonical units")
        if self.unit not in {"usd", "ratio", "percent", "percentage_points"}:
            raise ValueError("Unsupported unit")
        if not isinstance(self.decimal_places, int) or not 0 <= self.decimal_places <= 10:
            raise ValueError("decimal_places must be between 0 and 10")
        if self.allow_percent_for_ratio and self.unit != "ratio":
            raise ValueError("Percent conversion is only valid for ratio rubrics")


@dataclass(frozen=True)
class NumericScore:
    status: Literal["correct", "incorrect", "needs_review", "blocked"]
    reason: str
    version: str = VERSION


_SCALAR = re.compile(
    r"(?P<prefix>USD|\$)?\s*"
    r"(?P<number>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*"
    r"(?P<suffix>USD)?\s*"
    r"(?P<scale>billions?|millions?|bn|mn)?\s*"
    r"(?P<unit>percentage points?|percent|%|pp|times|x)?",
    re.I,
)


def score_numeric(answer: str, rubric: NumericRubric) -> NumericScore:
    """Score a scalar with explicit units; prose/multiple values need review.

    USD references are base dollars; ratio references are decimal ratios;
    percent and percentage-point references use their displayed numeric units.
    ROUND_HALF_UP is explicit and versioned, not a blanket absolute tolerance.
    """
    if not rubric.reviewed:
        return NumericScore("blocked", "Reference and rubric are not reviewed")
    text = answer.strip().replace("\u2212", "-")
    if text == "INSUFFICIENT_CONTEXT":
        return NumericScore("incorrect", "Abstention on an answerable numeric case")
    text = re.sub(r"(?:\s*\[S\d+\])+\s*$", "", text).strip()
    accounting = text.startswith("(") and text.endswith(")")
    if accounting:
        text = text[1:-1].strip()
    match = _SCALAR.fullmatch(text)
    if not match:
        return NumericScore("needs_review", "Not an unambiguous scalar; no first-number guessing")
    raw = match["number"]
    if accounting and raw.startswith(("-", "+")):
        return NumericScore("needs_review", "Conflicting sign notation")
    value = Decimal(raw.replace(",", "")) * (-1 if accounting else 1)
    currency = bool(match["prefix"] or match["suffix"])
    scale = (match["scale"] or "").lower()
    unit = (match["unit"] or "").lower()
    if currency:
        if unit:
            return NumericScore("needs_review", "Conflicting currency and ratio/percentage units")
        actual_unit = "usd"
        value *= Decimal(
            1000000000 if scale.startswith(("billion", "bn")) else 1000000 if scale else 1
        )
    else:
        if scale:
            return NumericScore("needs_review", "Magnitude without explicit currency")
        actual_unit = (
            "percent"
            if unit in {"%", "percent"}
            else "percentage_points"
            if unit.startswith("percentage point") or unit == "pp"
            else "ratio"
        )
    if actual_unit == "percent" and rubric.unit == "ratio" and rubric.allow_percent_for_ratio:
        value /= 100
        actual_unit = "ratio"
    if actual_unit != rubric.unit:
        return NumericScore("needs_review", "Units differ or a required unit is absent")
    quantum = Decimal(1).scaleb(-rubric.decimal_places)
    correct = value.quantize(quantum, rounding=ROUND_HALF_UP) == rubric.expected.quantize(
        quantum, rounding=ROUND_HALF_UP
    )
    return NumericScore("correct" if correct else "incorrect", "Compared at rubric precision")
