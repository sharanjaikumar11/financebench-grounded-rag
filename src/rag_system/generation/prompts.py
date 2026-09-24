"""Prompt construction for source-grounded answers."""

from __future__ import annotations

from collections.abc import Mapping

from rag_system.schemas import RetrievedChunk

INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


def grounded_answer_prompt(
    question: str, source_map: Mapping[str, RetrievedChunk]
) -> str:
    """Build a prompt that restricts the model to retrieved evidence."""
    sources = "\n\n".join(
        f"[{label}] document_id={item.chunk.document_id}; "
        f"document_name={item.chunk.document_name}; "
        f"pages={list(item.chunk.page_numbers)}; "
        f"sections={list(item.chunk.section_titles)}\n{item.chunk.text}"
        for label, item in source_map.items()
    )
    return (
        "Answer the question using only the supplied sources. "
        "Do not add facts not supported by them. "
        f"Return exactly {INSUFFICIENT_CONTEXT} only when the sources lack the facts needed to answer. "
        "Give the direct answer first and keep it concise. Preserve the unit requested in the "
        "question; for a yes/no question, begin with exactly Yes or No. "
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
        "Every factual statement in a supported answer must include one or more source labels "
        "in the format [S1]. Cite only source labels that directly support that answer.\n\n"
        f"Question: {question}\n\nSources:\n{sources}"
    )
