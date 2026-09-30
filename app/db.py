import logging
from typing import Any
import psycopg
from psycopg.rows import dict_row
from app import config


def get_connection() -> psycopg.Connection:
    """Create and return a new PostgreSQL database connection."""
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row)


def get_db_counts() -> dict[str, int]:
    """Return row counts for schemes and scheme_chunks tables."""
    logging.info("Querying database for scheme and chunk counts")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS count FROM schemes;")
            schemes_row = cur.fetchone()
            schemes_count = schemes_row["count"] if schemes_row else 0

            cur.execute("SELECT COUNT(*) AS count FROM scheme_chunks;")
            chunks_row = cur.fetchone()
            chunks_count = chunks_row["count"] if chunks_row else 0

    counts = {
        "schemes_count": schemes_count,
        "chunks_count": chunks_count,
    }
    logging.info("Retrieved counts: %s", counts)
    return counts
