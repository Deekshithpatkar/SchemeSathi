from fastapi.testclient import TestClient
from app.main import app
from app.search import search_schemes

client = TestClient(app)


def test_search_gruha_lakshmi_documents() -> None:
    """Verify that searching for Gruha Lakshmi documents returns the scheme with URL."""
    results = search_schemes("documents needed for Gruha Lakshmi", limit=3)
    assert len(results) > 0
    slugs = [r["slug"] for r in results]
    assert "gruha-lakshmi" in slugs

    # Verify expected metadata fields are present
    top_match = next(r for r in results if r["slug"] == "gruha-lakshmi")
    assert top_match["name"] == "Gruha Lakshmi Scheme"
    assert "source_url" in top_match and top_match["source_url"].startswith("http")
    assert "content" in top_match and len(top_match["content"]) > 0


def test_search_unemployed_graduates() -> None:
    """Verify semantic search retrieves Yuva Nidhi for unemployed graduates question."""
    results = search_schemes("monthly financial support for unemployed graduates in Karnataka", limit=3)
    slugs = [r["slug"] for r in results]
    assert "yuva-nidhi" in slugs


def test_search_farmer_income_support() -> None:
    """Verify semantic search retrieves PM-Kisan for farmer financial support."""
    results = search_schemes("income support for landholding farmers", limit=3)
    slugs = [r["slug"] for r in results]
    assert "pm-kisan" in slugs or "raitha-siri" in slugs


def test_search_women_bus_travel() -> None:
    """Verify semantic search retrieves Shakti scheme for women bus travel."""
    results = search_schemes("free bus travel for women in Karnataka", limit=3)
    slugs = [r["slug"] for r in results]
    assert "shakti-scheme" in slugs


def test_search_api_endpoint() -> None:
    """Verify GET /search API endpoint returns 200 and relevant scheme results."""
    response = client.get("/search?q=documents needed for Gruha Lakshmi")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    slugs = [item["slug"] for item in data]
    assert "gruha-lakshmi" in slugs
    assert "content" in data[0]
    assert "source_url" in data[0]
