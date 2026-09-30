import logging
from typing import Any
from pgvector.psycopg import register_vector
from app.db import get_connection
from app.llm import get_embedding


def search_schemes(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Search scheme chunks by semantic similarity using pgvector cosine distance."""
    logging.info("Searching schemes with query: '%s', limit: %d", query, limit)
    query_vector = get_embedding(query)

    search_sql = """
    SELECT 
        s.slug,
        s.name,
        s.source_url,
        s.last_verified,
        c.content,
        ROUND((c.embedding <=> %s::vector)::numeric, 4) AS distance
    FROM scheme_chunks c
    JOIN schemes s ON s.id = c.scheme_id
    ORDER BY c.embedding <=> %s::vector ASC
    LIMIT %s;
    """

    with get_connection() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(search_sql, (query_vector, query_vector, limit))
            rows = cur.fetchall()

    results = [dict(row) for row in rows]
    logging.info("Search returned %d chunks for query '%s'", len(results), query)
    return results
