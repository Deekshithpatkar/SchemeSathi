import logging
from typing import Any
from fastapi import FastAPI
from app import config
from app.db import get_db_counts, get_all_schemes
from app.eligibility import check_eligibility

app = FastAPI(title="Scheme Saathi API", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    """Return health status of the service."""
    logging.info("Health check requested")
    response = {"status": "ok"}
    logging.info("Health check response: %s", response)
    return response


@app.get("/debug/db")
def debug_db() -> dict:
    """Return row counts from schemes and scheme_chunks tables."""
    logging.info("Debug DB endpoint requested")
    try:
        counts = get_db_counts()
        logging.info("Debug DB response: %s", counts)
        return counts
    except Exception as exc:
        logging.error("Failed to query database counts: %s", exc)
        return {"error": str(exc), "step": "debug_db"}


@app.post("/check-eligibility")
def check_user_eligibility(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Check user profile against scheme rules and return eligible schemes."""
    logging.info("Checking eligibility endpoint called with: %s", profile)
    try:
        schemes = get_all_schemes()
        results = check_eligibility(profile, schemes)
        logging.info("Eligibility results: %s", results)
        return results
    except Exception as exc:
        logging.error("Error during eligibility check: %s", exc)
        return [{"error": str(exc), "step": "rules"}]
