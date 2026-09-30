import logging
from fastapi import FastAPI
from app import config

app = FastAPI(title="Scheme Saathi API", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    """Return health status of the service."""
    logging.info("Health check requested")
    response = {"status": "ok"}
    logging.info("Health check response: %s", response)
    return response
