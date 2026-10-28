"""Secret-free run provenance for reproducible evaluation."""

import hashlib
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run_metadata(cases_path: Path, index_path: Path, retrieval_mode: str, top_k: int) -> dict:
    def git(*args):
        try:
            return subprocess.check_output(
                ["git", *args], text=True, stderr=subprocess.DEVNULL, timeout=5
            ).strip()
        except (OSError, subprocess.SubprocessError):
            return None

    defaults = {
        "ANSWER_PROVIDER": "gemini",
        "GEMINI_MODEL": "gemini-3.1-flash-lite",
        "GEMINI_FALLBACK_MODEL": "gemini-3.5-flash-lite",
        "GEMINI_THINKING_LEVEL": "minimal",
        "GROQ_MODEL": "openai/gpt-oss-20b",
        "GROUNDED_OUTPUT_MODE": "text",
        "STATEMENT_AWARE_RANKING": "0",
        "FINANCIAL_INTENT_RANKING": "0",
        "CONTEXT_DIVERSITY_RANKING": "0",
        "EVIDENCE_REPAIR_EXCERPTS": "0",
        "CALCULATION_VALIDATION": "0",
        "COMPARISON_VALIDATION": "0",
        "METRIC_IDENTITY_VALIDATION": "0",
        "NUMERIC_ROW_COVERAGE": "0",
        "PERIOD_VALIDATION": "0",
        "OPERAND_COVERAGE": "0",
        "FINANCIAL_DECIMAL_INPUT": "0",
        "ABSENCE_VALIDATION": "0",
        "RERANKER_MODEL": "",
        "RERANKER_CANDIDATE_K": "30",
    }
    stat = index_path.stat()
    prompt_dir = Path(__file__).resolve().parents[1] / "generation"
    status = git("status", "--porcelain")
    return {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(status) if status is not None else None,
        "dataset_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "dataset_file": cases_path.name,
        "index_file": index_path.name,
        "index_size_bytes": stat.st_size,
        "index_mtime_ns": stat.st_mtime_ns,
        "index_identity_note": "Size/mtime are not a content hash or immutable index revision.",
        "embedding_model": "all-MiniLM-L6-v2",
        "retrieval_mode": retrieval_mode,
        "top_k": top_k,
        "settings": {key: os.getenv(key, value) for key, value in defaults.items()},
        "prompt_sha256": {
            name: hashlib.sha256((prompt_dir / name).read_bytes()).hexdigest()
            for name in (
                "prompts.py",
                "evidence.py",
                "calculations.py",
                "comparisons.py",
                "metric_identity.py",
                "period_validation.py",
                "absence_validation.py",
            )
        },
        "model_revision_note": "Configured aliases only; actual provider revision/fallback usage not captured.",
    }
