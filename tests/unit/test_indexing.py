from pathlib import Path

from rag_system.services.indexing import discover_supported_documents, index_directory
from rag_system.services.query import IndexingResult


class FakeService:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def index_document(self, path: Path) -> IndexingResult:
        self.paths.append(path)
        if path.name == "duplicate.txt":
            return IndexingResult("duplicate", None, 0)
        if path.name == "bad.md":
            raise RuntimeError("parse failure")
        return IndexingResult("indexed", "doc-id", 1)


def test_discovery_and_indexing_processes_only_supported_files_in_order(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("text")
    (tmp_path / "a.md").write_text("# heading")
    (tmp_path / "duplicate.txt").write_text("text")
    (tmp_path / "bad.md").write_text("# heading")
    (tmp_path / "ignored.csv").write_text("not supported")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.pdf").write_bytes(b"not parsed by fake")
    service = FakeService()

    result = index_directory(service, tmp_path)

    assert [path.name for path in discover_supported_documents(tmp_path)] == [
        "a.md", "b.txt", "bad.md", "duplicate.txt", "c.pdf"
    ]
    assert result.indexed == 3
    assert result.duplicates == 1
    assert result.failed == ("bad.md: parse failure",)
