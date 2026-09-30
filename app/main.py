import logging
from fastapi import FastAPI
from app import config
from app.db import get_db_counts

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
