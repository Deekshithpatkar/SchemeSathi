import json
import logging
from pathlib import Path
from typing import Any
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
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


def get_all_schemes() -> list[dict[str, Any]]:
    """Retrieve all schemes from the database, falling back to schemes.json if empty."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT slug, name, state, source_url, rules, last_verified FROM schemes;")
                rows = cur.fetchall()
                if rows:
                    return list(rows)
    except Exception as exc:
        logging.warning("Database unavailable, falling back to data/schemes.json: %s", exc)

    data_path = Path(__file__).parent.parent / "data" / "schemes.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_schemes_into_db(schemes_list: list[dict[str, Any]]) -> int:
    """Insert or update scheme records in PostgreSQL database."""
    logging.info("Upserting %d schemes into database", len(schemes_list))
    query = """
    INSERT INTO schemes (slug, name, state, source_url, rules, last_verified)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (slug) DO UPDATE SET
        name = EXCLUDED.name,
        state = EXCLUDED.state,
        source_url = EXCLUDED.source_url,
        rules = EXCLUDED.rules,
        last_verified = EXCLUDED.last_verified;
    """
    inserted = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for s in schemes_list:
                cur.execute(query, (
                    s["slug"],
                    s["name"],
                    s.get("state"),
                    s["source_url"],
                    Jsonb(s["rules"]),
                    s["last_verified"],
                ))
                inserted += 1
        conn.commit()
    logging.info("Successfully upserted %d schemes", inserted)
    return inserted
