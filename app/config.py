import os
import logging
from dotenv import load_dotenv

# Configure basic logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load environment variables from .env file
load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/schemes")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))
