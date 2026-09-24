"""Prompt construction for source-grounded answers."""

from __future__ import annotations

from collections.abc import Mapping

from rag_system.schemas import RetrievedChunk

INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


def _render_sources(source_map: Mapping[str, RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{label}] document_id={item.chunk.document_id}; "
        f"document_name={item.chunk.document_name}; "
        f"pages={list(item.chunk.page_numbers)}; "
        f"sections={list(item.chunk.section_titles)}\n{item.chunk.text}"
        for label, item in source_map.items()
    )


def grounded_answer_prompt(
    question: str, source_map: Mapping[str, RetrievedChunk]
) -> str:
    """Build a prompt that restricts the model to retrieved evidence."""
    sources = _render_sources(source_map)
    return (
        "Answer the question using only the supplied sources. "
        "Do not add facts not supported by them. "
        f"Return exactly {INSUFFICIENT_CONTEXT} only when the sources lack the facts needed to answer. "
        "Give exactly one direct answer sentence of at most 40 words. Do not explain the retrieval "
        "process, summarize every source, or list alternate figures. Preserve the unit requested in "
        "the question; for a yes/no question, begin with exactly Yes or No. "
        "Perform only arithmetic or concise inference directly supported by source figures, state "
        "the calculation briefly when it is needed, and preserve the unit requested in the question. "
        "For qualitative questions, make a concise conclusion only when the retrieved evidence "
        "supports the conclusion. "
        "Financial-statement tables are evidence: use their row labels, column headers, dates, "
        "units, and figures together. Do not return INSUFFICIENT_CONTEXT merely because the "
        "year header and the requested table row occur in adjacent supplied sources. "
        "Recognize standard financial-reporting equivalents when the source makes the meaning "
        "clear, including capital expenditure/capital spending and purchases or additions of "
        "property, plant and equipment; cost of goods sold and cost of revenue or sales; and "
        "inventory and inventories. Parentheses in a cash-flow statement denote a cash outflow; "
        "when the question asks for the expenditure amount, report its magnitude unless the "
        "question asks for the cash-flow sign. For a highest, lowest, largest, or smallest "
        "question, compare the directly listed table values and state the matching label. "
        "A consolidated net-income line supports the reported net income when the sources do not "
        "show a separate attribution amount. "
        "When a requested metric is explicitly present in a table, report that figure with its "
        "reported unit and cite every source needed to identify the correct period and value. "
        "End the sentence with one or more source labels in the format [S1]. Cite only source "
        "labels that directly support that answer.\n\n"
        f"Question: {question}\n\nSources:\n{sources}"
    )


def grounded_answer_retry_prompt(
    question: str, source_map: Mapping[str, RetrievedChunk]
) -> str:
    """Ask for a second, citation-validated pass after a cautious abstention."""
    return (
        "Re-evaluate the question as a financial-statement extraction task. The first pass returned "
        f"{INSUFFICIENT_CONTEXT}; do not repeat that response automatically. Inspect every supplied "
        "source for a direct table row, statement line, or comparison that answers the question. "
        "A source is sufficient when its row label (or a standard reporting equivalent), relevant "
        "period, and figure or comparison establish the answer; use adjacent supplied chunks to "
        "connect a header, unit, and value. Extract the reported value or selected label exactly, "
        "convert units only when the source provides the needed conversion, and cite the supporting "
        "source label in [S1] format. Give exactly one answer sentence and do not abstain merely "
        "because the table is compact, the value "
        "uses parentheses for an outflow, or the question uses a common synonym for the row label. "
        "If no directly supporting source exists after that inspection, return "
        f"exactly {INSUFFICIENT_CONTEXT}.\n\nQuestion: {question}\n\nSources:\n{_render_sources(source_map)}"
    )
