import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.eligibility import check_eligibility

client = TestClient(app)


def load_test_schemes() -> list[dict]:
    """Helper to load schemes from data/schemes.json for unit testing."""
    data_path = Path(__file__).parent.parent / "data" / "schemes.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_eligible_karnataka_farmer() -> None:
    """Test eligible profile: 45 yo farmer in Karnataka with 2 acres."""
    schemes = load_test_schemes()
    profile = {
        "age": 45,
        "occupation": "farmer",
        "land_acres": 2.0,
        "state": "Karnataka",
    }
    results = check_eligibility(profile, schemes)
    slugs = [r["slug"] for r in results]

    # Eligible for PM-Kisan (Central) and Raitha Siri (Karnataka farmer <= 5 acres)
    assert "pm-kisan" in slugs
    assert "raitha-siri" in slugs
    assert "gruha-lakshmi" not in slugs


def test_ineligible_profile_returns_empty_list() -> None:
    """Test completely ineligible profile: 15 yo in Delhi with no occupation."""
    schemes = load_test_schemes()
    profile = {
        "age": 15,
        "occupation": "student",
        "state": "Delhi",
    }
    results = check_eligibility(profile, schemes)
    assert results == []


def test_age_exactly_at_limit() -> None:
    """Test edge cases where age is exactly at minimum and maximum limits."""
    schemes = load_test_schemes()

    # Age 18 farmer: qualifies for PM-Kisan (min_age 18)
    profile_18 = {
        "age": 18,
        "occupation": "farmer",
        "state": "Karnataka",
    }
    results_18 = check_eligibility(profile_18, schemes)
    slugs_18 = [r["slug"] for r in results_18]
    assert "pm-kisan" in slugs_18

    # Age 35 unemployed: qualifies for Yuva Nidhi (max_age 35)
    profile_35 = {
        "age": 35,
        "occupation": "unemployed",
        "state": "Karnataka",
    }
    results_35 = check_eligibility(profile_35, schemes)
    slugs_35 = [r["slug"] for r in results_35]
    assert "yuva-nidhi" in slugs_35

    # Age 36 unemployed: exceeds max_age 35 for Yuva Nidhi
    profile_36 = {
        "age": 36,
        "occupation": "unemployed",
        "state": "Karnataka",
    }
    results_36 = check_eligibility(profile_36, schemes)
    slugs_36 = [r["slug"] for r in results_36]
    assert "yuva-nidhi" not in slugs_36


def test_wrong_state_disqualifies_state_scheme() -> None:
    """Test that a resident of Maharashtra cannot qualify for Karnataka state schemes."""
    schemes = load_test_schemes()
    profile = {
        "age": 45,
        "occupation": "farmer",
        "land_acres": 2.0,
        "state": "Maharashtra",
    }
    results = check_eligibility(profile, schemes)
    slugs = [r["slug"] for r in results]

    # PM-Kisan is all-India, so it should match
    assert "pm-kisan" in slugs
    # Raitha Siri is Karnataka-only, so it should not match
    assert "raitha-siri" not in slugs


def test_missing_fields_handling() -> None:
    """Test that missing required occupation or state disqualifies properly without error."""
    schemes = load_test_schemes()
    profile_missing_occ = {
        "age": 25,
        "state": "Karnataka",
    }
    results = check_eligibility(profile_missing_occ, schemes)
    slugs = [r["slug"] for r in results]
    assert "pm-kisan" not in slugs
    assert "yuva-nidhi" not in slugs
    assert "raitha-siri" not in slugs


def test_all_india_scheme_for_karnataka_user() -> None:
    """Test that an all-India scheme (state: null) matches Karnataka user when rules pass."""
    schemes = load_test_schemes()
    profile = {
        "age": 30,
        "occupation": "farmer",
        "state": "Karnataka",
    }
    results = check_eligibility(profile, schemes)
    slugs = [r["slug"] for r in results]
    assert "pm-kisan" in slugs


def test_check_eligibility_api_endpoint() -> None:
    """Test POST /check-eligibility route using FastAPI TestClient."""
    profile = {
        "age": 45,
        "occupation": "farmer",
        "land_acres": 2.0,
        "state": "Karnataka",
    }
    response = client.post("/check-eligibility", json=profile)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    slugs = [item["slug"] for item in data]
    assert "pm-kisan" in slugs
    assert "raitha-siri" in slugs
