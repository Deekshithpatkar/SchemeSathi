import logging
import os
import sys

# Ensure project root is on sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg
from app import config

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schemes (
    id            SERIAL PRIMARY KEY,
    slug          TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    state         TEXT,
    source_url    TEXT NOT NULL,
    rules         JSONB NOT NULL,
    last_verified DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS scheme_chunks (
    id         SERIAL PRIMARY KEY,
    scheme_id  INTEGER REFERENCES schemes(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    embedding  vector(768)
);
"""


def init_database() -> None:
    """Initialize vector extension and required database tables."""
    logging.info("Connecting to database at configured URL...")
    try:
        with psycopg.connect(config.DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
        logging.info("Database schema initialized successfully.")
    except Exception as exc:
        logging.error("Failed to initialize database: %s", exc)
        raise


if __name__ == "__main__":
    init_database()
