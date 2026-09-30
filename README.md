# Scheme Saathi: Government Scheme Finder

A web app where a person describes their situation in plain words (later: by voice, in Kannada/Hindi) and gets the government schemes they qualify for, the documents they need, and how to apply.

## Architecture

```
User text -> Extract profile (LLM) -> Check rules (Python) -> Search details (RAG) -> Write answer (LLM)
```

- **Phase 1 Target**: Karnataka state schemes & key Central schemes applicable to Karnataka.
- **Languages**: English and Kannada.
- **Key Principle**: Eligibility is strictly evaluated by deterministic Python rules over PostgreSQL, never guessed by the LLM.

## Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env` from `.env.example`:
   ```env
   GOOGLE_API_KEY=your_key_here
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/schemes
   LLM_MODEL=gemini-2.5-flash
   EMBEDDING_MODEL=gemini-embedding-001
   EMBEDDING_DIM=768
   ```
4. Run Checkpoint Tests:
   ```bash
   pytest tests/test_cp1_health.py -v
   ```
