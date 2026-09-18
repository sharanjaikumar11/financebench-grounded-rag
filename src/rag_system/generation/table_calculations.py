"""Source-grounded table parsing and numeric conversion for retrieved evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

from rag_system.schemas import RetrievedChunk

_TABLE_UNIT = re.compile(r"\b(?:dollars?\s+in|amounts?\s+in|in)\s+(thousands|millions|billions)\b", re.IGNORECASE)
_NUMBER = re.compile(r"(?<![A-Za-z0-9])\(?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\)?")
_ROW = re.compile(r"(?:^|\n)\s*([A-Za-z][A-Za-z ,&()/\-]{2,}?)\s+(\(?\$?\s*\d[\d,]*(?:\.\d+)?\)?(?:\s+\(?\$?\s*\d[\d,]*(?:\.\d+)?\)?){0,3})\s*(?=\n|$)")
_TARGET_UNIT = re.compile(r"\b(?:usd\s+)?(thousands|millions|billions)\b", re.IGNORECASE)

_UNIT_SCALE = {"thousands": 1_000.0, "millions": 1_000_000.0, "billions": 1_000_000_000.0}


@dataclass(frozen=True, slots=True)
class CalculationEvidence:
    """A deterministic calculation, linked to the retrieved source label."""

    source_label: str
    row_label: str
    source_unit: str
    target_unit: str
    values: tuple[float, ...]

    def render(self) -> str:
        values = ", ".join(f"{value:,.2f}" for value in self.values)
        return (
            f"[{self.source_label}] Parsed table row '{self.row_label}' is expressed in "
            f"{self.target_unit}: {values}. Source table unit: {self.source_unit}."
        )


class TableCalculator:
    """Parse line-oriented source tables with pandas and make explicit unit conversions."""

    def evidence(
        self, question: str, source_map: Mapping[str, RetrievedChunk]
    ) -> tuple[CalculationEvidence, ...]:
        target_unit = self._requested_unit(question)
        if target_unit is None:
            return ()
        evidence: list[CalculationEvidence] = []
        for source_label, item in source_map.items():
            source_unit = self._source_unit(item.chunk.text)
            if source_unit is None:
                continue
            frame = self._to_frame(item.chunk.text)
            if frame.empty:
                continue
            matched = self._matching_rows(question, frame)
            for row in matched.itertuples(index=False):
                raw_values = np.asarray(row.values, dtype=float)
                converted = raw_values * (_UNIT_SCALE[source_unit] / _UNIT_SCALE[target_unit])
                evidence.append(
                    CalculationEvidence(
                        source_label=source_label,
                        row_label=str(row.label),
                        source_unit=source_unit,
                        target_unit=target_unit,
                        values=tuple(float(value) for value in converted),
                    )
                )
        return tuple(evidence)

    @staticmethod
    def _requested_unit(question: str) -> str | None:
        match = _TARGET_UNIT.search(question)
        return match.group(1).casefold() if match else None

    @staticmethod
    def _source_unit(text: str) -> str | None:
        match = _TABLE_UNIT.search(text)
        return match.group(1).casefold() if match else None

    @staticmethod
    def _to_frame(text: str) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for match in _ROW.finditer(text):
            values = [
                _parse_number(number.group(0))
                for number in _NUMBER.finditer(match.group(2))
            ]
            if values:
                rows.append({"label": " ".join(match.group(1).split()), "values": values})
        return pd.DataFrame(rows, columns=["label", "values"])

    @staticmethod
    def _matching_rows(question: str, frame: pd.DataFrame) -> pd.DataFrame:
        terms = {
            term.casefold()
            for term in re.findall(r"[A-Za-z]+", question)
            if len(term) > 2 and term.casefold() not in {"what", "with", "from", "that", "give", "answer", "using"}
        }
        if not terms:
            return frame.iloc[0:0]
        scores = frame["label"].map(
            lambda label: len(terms & {term.casefold() for term in re.findall(r"[A-Za-z]+", label)})
        )
        return frame.loc[scores > 0].assign(_score=scores[scores > 0]).sort_values("_score", ascending=False).head(3)


def _parse_number(value: str) -> float:
    negative = "(" in value and ")" in value
    number = float(value.replace("$", "").replace(",", "").replace("(", "").replace(")", "").strip())
    return -number if negative else number
