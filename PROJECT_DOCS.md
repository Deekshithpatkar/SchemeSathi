# Scheme Saathi: Government Scheme Finder

A web app where a person describes their situation in plain words (later: by voice, in Kannada/Hindi) and gets the government schemes they qualify for, the documents they need, and how to apply.

## 1. How it works (one paragraph)

The user's text goes to an LLM that turns it into a small structured profile (age, occupation, land, state, income). A plain Python function checks that profile against eligibility rules stored in Postgres. For each eligible scheme, we search the scheme text (RAG) for details like documents and how to apply. The LLM then writes a friendly answer using ONLY that retrieved information. Eligibility is decided by our rules, never by the LLM.

```
user text -> extract profile (LLM) -> check rules (Python) -> search details (RAG) -> write answer (LLM)
```

## 1a. Scope

- **Phase 1:** Karnataka state schemes plus the main central schemes that apply to Karnataka residents (start with 5, grow to 15-20).
- **Languages:** English and Kannada, for both text and voice.
- **Later:** more states and Hindi.

## 2. Tech stack

| Part | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Simple, familiar |
| Web framework | FastAPI + Uvicorn | Small, auto-generated /docs page for testing |
| Database | PostgreSQL + pgvector extension | One database for schemes, rules AND embeddings |
| DB driver | psycopg (v3), plain SQL | No ORM, so every query is visible and easy to debug |
| Embeddings | Google Gemini embedding model | Uses the same Google API key |
| LLM | Google Gemini (model name set in .env) | Same key, good Indian-language support |
| Google SDK | `google-genai` | Official SDK |
| Validation | Pydantic | Checks the LLM's JSON output |
| Frontend | One HTML file + plain JavaScript, served by FastAPI | No build tools |
| Config | `.env` + python-dotenv | Keeps secrets out of code |
| Tests | pytest | For the eligibility rules |

Later phases: voice in English and Kannada (Google Cloud Speech-to-Text and Text-to-Speech, or Whisper / AI4Bharat as alternatives), Docker for deployment. Google Cloud speech services need a Google Cloud project with billing enabled, which is separate from the AI Studio key. Check current Kannada (kn-IN) support before starting voice.

## 3. Folder structure

```
scheme-saathi/
├── .env                  # secrets (NEVER commit)
├── .env.example          # same keys, fake values (commit this)
├── .gitignore
├── requirements.txt
├── README.md
├── app/
│   ├── main.py           # FastAPI app and all routes
│   ├── config.py         # loads .env, one place for settings
│   ├── db.py             # get_connection() and small query helpers
│   ├── llm.py            # ONLY file that calls Gemini (chat + embeddings)
│   ├── eligibility.py    # pure Python rule checker (no AI, no DB)
│   ├── extract.py        # text -> profile using the LLM
│   ├── search.py         # RAG: embed question, query pgvector
│   ├── answer.py         # builds the final answer
│   └── schemas.py        # Pydantic models
├── data/
│   └── schemes.json      # scheme records: text, url, rules
├── scripts/              # run by hand from the terminal, NOT part of the web server
│   ├── setup_db.py       # run once: creates the tables
│   ├── load_schemes.py   # run when data changes: reads schemes.json, embeds, inserts
│   └── update_schemes.py # (later) run weekly: detect policy changes
├── static/
│   └── index.html        # simple frontend
├── tests/                # one test file per checkpoint
│   ├── test_cp1_health.py
│   ├── test_cp2_db.py
│   ├── test_cp3_eligibility.py
│   └── ...               # more added as checkpoints are built
└── evaluate.py           # runs test profiles, prints accuracy
```

**`app/` vs `scripts/`:** `app/` is the code that runs while the web server is live. `scripts/` are small programs you run yourself with `python scripts/name.py` for setup or maintenance jobs (create tables, load data, check for policy updates). The web server never calls them.

## 4. Setup

### 4.1 Create the environment

```bash
mkdir scheme-saathi && cd scheme-saathi
python -m venv venv

# activate
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 4.2 requirements.txt

```
fastapi
uvicorn
python-dotenv
psycopg[binary]
pgvector
google-genai
pydantic
pytest
requests
beautifulsoup4
python-multipart
httpx
```

### 4.3 Create the .env file

Create a file named `.env` in the project root:

```
GOOGLE_API_KEY=your-google-api-key-here
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/schemes
LLM_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIM=768
```

Notes:
- Get the API key from Google AI Studio.
- Check Google's docs for the current model names. If a name is retired, only this file changes.
- `EMBEDDING_DIM` must match the `vector(768)` column in the database. If you change one, change both and re-run `load_schemes.py`.

Create `.gitignore` containing at least:

```
.env
venv/
__pycache__/
*.pyc
```

Create `.env.example` with the same keys but fake values, so others know what to fill in.

### 4.4 Postgres with pgvector (already installed on Windows)

1. Create the database (using psql or pgAdmin):
   ```sql
   CREATE DATABASE schemes;
   ```
2. Confirm pgvector is available by connecting to the `schemes` database and running:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   If this errors, the pgvector extension is not installed for your Postgres version; reinstall it before continuing.
3. Put the connection string in `.env` as `DATABASE_URL` (see 4.3).

`scripts/setup_db.py` also runs `CREATE EXTENSION IF NOT EXISTS vector;`, so it is safe to run repeatedly.

### 4.5 Database tables

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schemes (
    id            SERIAL PRIMARY KEY,
    slug          TEXT UNIQUE NOT NULL,   -- e.g. "pm-kisan"
    name          TEXT NOT NULL,
    state         TEXT,                   -- NULL means all-India
    source_url    TEXT NOT NULL,
    rules         JSONB NOT NULL,         -- eligibility rules
    last_verified DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS scheme_chunks (
    id         SERIAL PRIMARY KEY,
    scheme_id  INTEGER REFERENCES schemes(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    embedding  vector(768)
);
```

### 4.6 Scheme record format (data/schemes.json)

```json
{
  "slug": "pm-kisan",
  "name": "PM-Kisan Samman Nidhi",
  "state": null,
  "source_url": "https://pmkisan.gov.in",
  "last_verified": "2026-09-30",
  "rules": {
    "occupation": ["farmer"],
    "min_age": 18,
    "max_land_acres": null,
    "max_income": null,
    "categories": null
  },
  "text": "Full text about benefits, documents needed, how to apply..."
}
```

Rule fields that are `null` mean "no restriction." Text must come from the official source, and each record needs the source URL.

## 5. Coding rules (IMPORTANT: follow these strictly)

The code must look like a fresher wrote it carefully, not like generated boilerplate.

1. **Keep it simple.** Plain functions. No classes unless a Pydantic model needs one. No design patterns, no abstract base classes, no decorators beyond FastAPI routes.
2. **One job per file**, as in the folder structure above. `llm.py` is the only file that talks to Gemini, so the model can be swapped by editing one file.
3. **No ORM.** Use plain SQL with psycopg and `%s` placeholders. Never build SQL with f-strings.
4. **Short functions**, ideally under 25 lines, with clear names like `check_eligibility`, `find_matching_chunks`.
5. **Type hints on function arguments and returns**, and a one-line docstring on each function saying what it does.
6. **Comments explain WHY, not WHAT.** Keep them short and natural.
7. **Print or log at every step**, using Python's `logging` module: what came in, what went out. Example: `logging.info("Extracted profile: %s", profile)`.
8. **Handle errors clearly.** Wrap external calls (Gemini, DB) in try/except, log the real error, and return a readable message. Never swallow errors silently.
9. **No secrets in code.** All settings come from `config.py`, which reads `.env`.
10. **Do not add libraries** beyond `requirements.txt` without asking.
11. **Do not add features** that are not in the current checkpoint.
12. **Eligibility logic is plain Python if/else.** It must never call the LLM.
13. **If the LLM cannot find a field, it returns `null`.** Never guess age, income or land size.
14. Use plain, readable variable names. No clever one-liners.

## 6. Debugging setup

- Every route logs the request and the result.
- Every LLM call logs the prompt length and the raw response before parsing.
- `/docs` (Swagger) is the main way to test each endpoint.
- Add `GET /health` and `GET /debug/db` (returns scheme count and chunk count) so problems can be found quickly.
- When something fails, the API returns `{"error": "clear message", "step": "extract|rules|search|answer"}` so you know which stage broke.
- Run the app with `uvicorn app.main:app --reload`.

## 7. Checkpoints (build in this order; each ends with something runnable AND a test)

Every checkpoint has: what to build, how to run it, its own test file, and a "Done when" check. Run the test with `pytest tests/test_cpN_name.py -v`. Do not start the next checkpoint until the current test passes.

Tests that call Gemini or need real data are marked "integration". They are slower and their wording can vary, so they check structure (right fields, right scheme returned) and not exact sentences.

**CP1: Skeleton**
- Build: FastAPI app, `config.py`, `GET /health`.
- Run: `uvicorn app.main:app --reload`, open `/docs`.
- Test `test_cp1_health.py`: uses FastAPI `TestClient`, checks `/health` returns 200 and `{"status": "ok"}`.
- Done when: the test passes and `/health` works in the browser.

**CP2: Database**
- Build: `db.py`, `setup_db.py`, `GET /debug/db`.
- Run: `python scripts/setup_db.py`.
- Test `test_cp2_db.py`: connects to the database, checks both tables exist and the vector extension is on.
- Done when: `/debug/db` returns counts (0 is fine).

**CP3: Eligibility rules (no AI)**
- Build: `eligibility.py` (pure Python), Karnataka scheme records with rules loaded into `schemes`, `POST /check-eligibility`.
- Input: `{"age": 45, "occupation": "farmer", "land_acres": 2, "state": "Karnataka"}`
- Test `test_cp3_eligibility.py`: tests the function directly, no server needed. Cover: eligible profile, ineligible profile, age exactly at the limit, missing fields, wrong state, all-India scheme for a Karnataka user.
- Done when: matching schemes come back with a reason each, and an ineligible profile returns an empty list.

**CP4: RAG search**
- Build: embedding function in `llm.py`, `load_schemes.py` (chunk, embed, insert), `search.py`, `GET /search?q=...`.
- Run: `python scripts/load_schemes.py`.
- Test `test_cp4_search.py` (integration): for 3-5 known questions, checks the expected scheme appears in the top 3 results.
- Done when: "documents needed for Gruha Lakshmi" (or any scheme you loaded) returns the right chunks with scheme name and source URL.

**CP5: Extract profile**
- Build: `extract.py`, `POST /extract`, Pydantic validation.
- Input: `{"text": "I am a 45 year old farmer in Karnataka with 2 acres"}`
- Test `test_cp5_extract.py` (integration): checks the age, occupation, state and land fields come out right, and that fields the user did not mention are `null`.
- Done when: clean JSON returns with nulls for anything unsaid.

**CP6: Full text assistant (English)**
- Build: `answer.py`, `POST /ask`. Flow: extract, check rules, search, write answer. If key fields are missing, return a follow-up question instead of guessing.
- Test `test_cp6_ask.py` (integration): checks the response has schemes, sources, and a last-verified date, and that a vague question returns a follow-up question.
- Done when: one plain-English question returns eligible schemes, documents needed, how to apply, source links and the verified date.

**CP7: Kannada text**
- Build: accept a `language` field (`en` or `kn`), understand Kannada input in `/extract`, answer in Kannada in `/ask`.
- Test `test_cp7_kannada.py` (integration): a Kannada question returns Kannada text (check for Kannada Unicode characters) and the same schemes as the English version of the question.
- Done when: a Kannada question gets the correct schemes in Kannada. Have a native speaker read a few answers.

**CP8: Evaluation**
- Build: `evaluate.py` with 20-30 hand-labeled test profiles, some in Kannada.
- Run: `python evaluate.py`
- Test `test_cp8_eval.py`: checks the script runs and the labeled file loads without errors.
- Done when: it prints accuracy and a list of failures.

**CP9: Frontend (text)**
- Build: `static/index.html` with a text box, language dropdown, and answer area, served at `/`.
- Test `test_cp9_frontend.py`: checks `/` returns HTML containing the input box.
- Done when: the browser page gives the same answer as `/ask`.

**CP10: Voice (English and Kannada)**
- Build: `voice.py` (speech-to-text and text-to-speech), `POST /voice` that accepts an audio file plus language and returns the transcript and an audio answer. Add a mic button to the page.
- Test `test_cp10_voice.py` (integration): sends 2-3 saved sample recordings (one English, one Kannada) and checks the transcript is close to the expected text.
- Done when: you speak a question and hear a correct answer in the same language. Record 10-20 samples and note how often transcription fails.

**CP11: Update pipeline**
- Build: `scripts/update_schemes.py` that re-fetches official pages, compares with stored text, prints a diff, and flags changes for manual review.
- Test `test_cp11_update.py`: change a stored scheme's text by hand and check the script detects it.
- Done when: an edited scheme is reported as changed.

**CP12: Docker, deploy, README**
- Build: Dockerfile, deployment, README with architecture, evaluation numbers, limitations and privacy note.
- Done when: anyone can open your link, speak, and get an answer.

Later: more states, Hindi, document photo OCR, local model experiment.

**Test rules for Antigravity:**
- Keep each test short and readable, with clear names like `test_farmer_with_2_acres_is_eligible_for_pm_kisan`.
- Unit tests (CP1, CP3, CP9, CP11) must not call Gemini.
- Integration tests read keys from `.env` and are allowed to be slower.
- Never delete or weaken a failing test to make it pass; fix the code.

## 8. API contracts

| Method | Route | Input | Output |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok"}` |
| GET | `/debug/db` | none | scheme and chunk counts |
| POST | `/check-eligibility` | profile JSON | list of `{slug, name, reason}` |
| GET | `/search?q=` | question | top chunks with scheme name and URL |
| POST | `/extract` | `{"text": "..."}` | profile JSON with nulls |
| POST | `/ask` | `{"text": "...", "language": "en" or "kn"}` | answer, schemes, sources, or follow-up question |
| POST | `/voice` | audio file + `language` | transcript, answer text, answer audio (CP10) |

Profile fields: `age`, `occupation`, `land_acres`, `annual_income`, `state`, `category`, `gender`. Every field is optional.

## 9. Prompts (keep in the code as plain strings)

**Extraction prompt (CP6):**
"Read the user's message and fill this JSON with only what they clearly said. If something is not mentioned, use null. Do not guess. Return only JSON."

**Answer prompt (CP7):**
"You are a helpful assistant explaining government schemes. Use ONLY the context below. If the context does not contain the answer, say you are not sure and point to the source link. Do not invent eligibility rules, amounts or dates. Use simple language. Mention the source and the last verified date."

## 10. Rules of the project

- Eligibility comes from the rules table, never from the LLM.
- Every answer shows the official source link and a "last verified" date.
- Do not store personal details the user types. Log only what is needed for debugging, and turn logging of user text off in production.
- The app gives information, not legal or official advice. Show this on the page.
- Policy changes: the update script only flags changes for manual review. It never changes rules automatically.

## 11. Out of scope for now

Login and user accounts, payments, mobile app, states other than Karnataka, Hindi, model fine-tuning, local LLM, agent frameworks (LangChain and similar). Add these only if the base project is finished and tested.
