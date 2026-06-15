# Contributing to AI Code Review Assistant

Thank you for your interest in contributing! Here's how to get started.

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/aarush23g/AI-Code-Review-Assistant-Github.git
   cd AI-Code-Review-Assistant-Github
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1   # Windows
   source .venv/bin/activate     # Linux/macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Verify setup**
   ```bash
   pytest tests/ -v
   ```

## Code Style

This project enforces consistent code style using:

- **[Black](https://black.readthedocs.io/)** — Code formatting (line length: 88)
- **[Ruff](https://docs.astral.sh/ruff/)** — Linting
- **[mypy](https://mypy-lang.org/)** — Type checking

Before committing, run:
```bash
black .
ruff check .
mypy app/
```

## Testing

- All tests live in `tests/`
- Tests use `pytest` with `pytest-asyncio` for async support
- Shared fixtures are in `tests/conftest.py`

Run the full suite:
```bash
pytest tests/ -v
```

Run a specific test file:
```bash
pytest tests/test_webhook.py -v
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass: `pytest tests/ -v`
4. Ensure code is formatted: `black --check .`
5. Ensure linting passes: `ruff check .`
6. Submit a PR with a clear description of changes

## Architecture Overview

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system architecture.

Key directories:
```
app/              # Application code
├── api/          # FastAPI routes and middleware
├── core/         # Config, logging, security
├── github/       # GitHub API client
├── review/       # LLM review logic and prompt building
├── schemas/      # Pydantic models
├── services/     # Business logic orchestration
└── storage/      # Database layer
tests/            # Test suite
evaluation/       # Benchmarking framework
dashboard/        # Streamlit metrics dashboard
notebooks/        # Jupyter analysis notebooks
docs/             # Documentation
```

## Evaluation Framework

To run the evaluation benchmark:
```bash
python -m evaluation.evaluate --mode security --rate-limit 2.0
python -m evaluation.metrics evaluation/results/run_<timestamp>.json
```

## Questions?

Open an issue or reach out via the repository discussions.
