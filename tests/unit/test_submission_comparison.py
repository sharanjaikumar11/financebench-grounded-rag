import runpy
import sqlite3
from pathlib import Path

MODULE = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/run_submission_comparison.py")
)


def test_inspect_index_reads_membership_without_writing(tmp_path):
    path = tmp_path / "index.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE chunks (document_name TEXT, chunking_strategy TEXT)")
        connection.executemany(
            "INSERT INTO chunks VALUES (?,?)",
            [("a.pdf", "fixed_token"), ("a.pdf", "fixed_token"), ("b.pdf", "fixed_token")],
        )
    before = path.read_bytes()
    assert MODULE["inspect_index"](path) == ({"a.pdf", "b.pdf"}, {"fixed_token"})
    assert path.read_bytes() == before
