"""Display live read-only index growth; Ctrl+C stops only this monitor."""

import argparse
import sqlite3
import time
from datetime import timedelta
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path, default=Path("data/processed/table_aware_v1/vectors.sqlite3")
    )
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("interval must be at least one second")
    started = time.monotonic()
    try:
        while True:
            print("\033[2J\033[H", end="")
            print("FinanceBench table indexing - live database growth")
            print(f"Monitor elapsed: {timedelta(seconds=int(time.monotonic() - started))}")
            try:
                with sqlite3.connect(
                    args.database.resolve().as_uri() + "?mode=ro", uri=True, timeout=2
                ) as db:
                    docs, chunks = db.execute(
                        "SELECT COUNT(DISTINCT document_name), COUNT(*) FROM chunks"
                    ).fetchone()
                    latest = db.execute(
                        "SELECT document_name FROM chunks ORDER BY rowid DESC LIMIT 1"
                    ).fetchone()
                print(f"Documents with stored chunks: {docs} | Chunks: {chunks:,}")
                print(f"Most recently written document: {latest[0] if latest else 'none'}")
                print(f"Database size: {args.database.stat().st_size / 1024**2:.1f} MiB")
            except sqlite3.Error as error:
                print(f"Waiting for index access: {error}")
            print("\nCounts include a partially indexed document; they do not certify completion.")
            print(
                "PDF parsing may take minutes without a database update. ETA is not reliable yet."
            )
            print(
                "The indexing terminal reports final success/failures. Ctrl+C stops this monitor only.",
                flush=True,
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped; indexing is unaffected.")


if __name__ == "__main__":
    main()
