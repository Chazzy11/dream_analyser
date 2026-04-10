# Dream Analyser — Claude Code Guide

## Project Overview

FastAPI service that analyzes dream descriptions and generates evolving visual symbols. Dreams are scored on two dimensions and stored per user; the symbol grows more complex with each dream logged.

Deployed on Railway via Docker. Live at the URL in the README.

## Architecture

```
dream_interpreter/
├── main.py            # FastAPI app + embedded HTML/JS web UI
├── analyser.py        # Core scoring engine (TextBlob + keyword matching)
├── database.py        # In-memory store (no persistence — data lost on restart)
├── models.py          # Pydantic models for all request/response shapes
└── symbol_generator.py # matplotlib PNG generator, returns base64 string
```

### Two-Dimensional Scoring Model

Every dream is scored on two independent axes:

| Axis | Range | Meaning |
|------|-------|---------|
| `upper_downer_score` | −1 to 1 | Emotional valence: −1 = very negative, +1 = very positive |
| `static_dynamic_score` | −1 to 1 | Energy level: −1 = very still/passive, +1 = very active |

These two scores place each dream in one of four quadrants (Dynamic Upper, Static Upper, Dynamic Downer, Static Downer). The quadrant history drives the evolving symbol.

### Key Design Decisions

- **In-memory only**: `DreamDatabase` uses plain dicts. No SQLAlchemy, no file persistence. This is intentional for the demo — `user_id` defaults to `"anonymous"` when omitted.
- **Confidence score**: Derived from text length (longer = more confident) + keyword hit density. Caps at 1.0.
- **Symbol layers**: One layer added per dream, capped at 10. Colours map to emotional tone; shapes indicate energy level.
- **scikit-learn** is listed as a dependency but currently unused — reserved for a planned TF-IDF upgrade to the analyser.
- **Web UI** is embedded directly in `main.py` as an HTML string (no template engine). Keep it that way unless adding Jinja2.

## Development Commands

```bash
make install        # Install dependencies via Poetry
make run            # Start dev server on http://localhost:8000
make test           # Run pytest
make test-coverage  # Run pytest with coverage (XML + terminal)
make lint           # Run pylint across src + tests
make fmt            # Format with isort then Black
make setup-nltk     # Download punkt + brown NLTK data (required for TextBlob)
make clean          # Remove build artefacts and caches
```

Run `make setup-nltk` once after a fresh install — TextBlob will fail without it.

## Testing

- Framework: pytest with pytest-asyncio
- HTTP client: httpx (via `AsyncClient` + `ASGITransport`)
- Three test files mirror the three main modules: `test_analyser.py`, `test_api.py`, `test_symbol_generator.py`
- Target coverage: 83%+ (tracked in CI)
- Run `make test-coverage` to see per-file line coverage

## Code Conventions

- **Formatter**: Black, line length 88
- **Imports**: isort
- **Linter**: Pylint, minimum score 8.0 (enforced in CI via `make lint-ci`)
- **Type hints**: Required on all public functions
- **Docstrings**: Google-style on all classes and public methods
- **Private helpers**: Prefix with `_` (e.g. `_calculate_emotional_score`)
- **Models**: All API input/output uses Pydantic `BaseModel` with field-level validation

## CI/CD

Two GitHub Actions workflows:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `dream_analyser.yml` | push/PR to main & develop | Tests on Python 3.9–3.12 + Black/isort/pylint checks |
| `build.yml` | push/PR to main | Builds Docker image; pushes to ghcr.io on merge to main |
