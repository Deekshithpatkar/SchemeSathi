from fastapi.testclient import TestClient
from app.main import app
from app.db import get_connection

client = TestClient(app)


def test_database_tables_and_extension() -> None:
    """Verify that pgvector extension is installed and both tables exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check vector extension
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            ext = cur.fetchone()
            assert ext is not None, "Extension 'vector' is not installed"
            assert ext["extname"] == "vector"

            # Check schemes table exists
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'schemes';"
            )
            schemes_tbl = cur.fetchone()
            assert schemes_tbl is not None, "Table 'schemes' does not exist"

            # Check scheme_chunks table exists
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'scheme_chunks';"
            )
            chunks_tbl = cur.fetchone()
            assert chunks_tbl is not None, "Table 'scheme_chunks' does not exist"


def test_debug_db_endpoint() -> None:
    """Verify that GET /debug/db returns 200 and count fields."""
    response = client.get("/debug/db")
    assert response.status_code == 200
    data = response.json()
    assert "schemes_count" in data, f"Expected 'schemes_count' in response, got: {data}"
    assert "chunks_count" in data, f"Expected 'chunks_count' in response, got: {data}"
    assert isinstance(data["schemes_count"], int)
    assert isinstance(data["chunks_count"], int)
