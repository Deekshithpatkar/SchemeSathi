import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb
from app.db import get_connection
from app.llm import get_embedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def chunk_text(text: str, max_chars: int = 350) -> list[str]:
    """Split text into manageable chunks respecting sentence boundaries."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    chunks: list[str] = []
    current = ""
    for s in sentences:
        formatted = s if s.endswith(".") else s + "."
        if len(current) + len(formatted) > max_chars and current:
            chunks.append(current.strip())
            current = formatted
        else:
            current = f"{current} {formatted}".strip()
    if current:
        chunks.append(current.strip())
    return chunks


def load_and_embed_schemes() -> None:
    """Read schemes.json, upsert schemes, chunk text, embed, and store in pgvector."""
    data_path = Path(__file__).parent.parent / "data" / "schemes.json"
    with open(data_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    logging.info("Loaded %d schemes from %s", len(schemes), data_path)

    upsert_scheme_sql = """
    INSERT INTO schemes (slug, name, state, source_url, rules, last_verified)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (slug) DO UPDATE SET
        name = EXCLUDED.name,
        state = EXCLUDED.state,
        source_url = EXCLUDED.source_url,
        rules = EXCLUDED.rules,
        last_verified = EXCLUDED.last_verified
    RETURNING id;
    """

    insert_chunk_sql = """
    INSERT INTO scheme_chunks (scheme_id, content, embedding)
    VALUES (%s, %s, %s);
    """

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for scheme in schemes:
                cur.execute(upsert_scheme_sql, (
                    scheme["slug"],
                    scheme["name"],
                    scheme.get("state"),
                    scheme["source_url"],
                    Jsonb(scheme["rules"]),
                    scheme["last_verified"],
                ))
                scheme_id = cur.fetchone()["id"]

                # Clear previous chunks for this scheme to avoid duplicates
                cur.execute("DELETE FROM scheme_chunks WHERE scheme_id = %s;", (scheme_id,))

                chunks = chunk_text(scheme.get("text", ""))
                logging.info("Embedding %d chunks for scheme '%s' (id=%d)", len(chunks), scheme["slug"], scheme_id)

                for chunk in chunks:
                    embedding = get_embedding(chunk)
                    cur.execute(insert_chunk_sql, (scheme_id, chunk, embedding))

        conn.commit()
    logging.info("Finished loading and embedding all schemes successfully.")


if __name__ == "__main__":
    load_and_embed_schemes()
