import logging
from typing import Optional
from google import genai
from app import config


def get_gemini_client() -> genai.Client:
    """Initialize and return a Google GenAI client instance."""
    return genai.Client(api_key=config.GOOGLE_API_KEY)


def get_embedding(text: str) -> list[float]:
    """Generate a vector embedding for the input text using Gemini."""
    logging.info("Requesting embedding for text of length %d", len(text))
    try:
        client = get_gemini_client()
        response = client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=text,
            config={"output_dimensionality": config.EMBEDDING_DIM},
        )
        embedding_values = response.embeddings[0].values
        logging.info("Generated embedding with dimension %d", len(embedding_values))
        return list(embedding_values)
    except Exception as exc:
        logging.error("Failed to generate embedding: %s", exc)
        raise
