# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `src/graph_rag_recipes/`, including config, ingest, graph, retrieval, embeddings, generator, and UI helpers; keep cross-module contracts inside this package. `scripts/bootstrap_data.py` prepares HowToCook assets, while `scripts/run_pipeline.py` provides the CLI demo and references `GraphRAGPipeline`. Long-lived datasets belong in `data/raw/`, derived JSON lives in `data/processed/`, and only the sample files listed in `.gitignore` should be versioned. Treat `pyproject.toml` and `uv.lock` as the single source of dependency truth.

## Build, Test, and Development Commands
- `uv sync` – install the locked Python 3.11 environment.
- `uv run python scripts/bootstrap_data.py --limit 800 --force-processed` – fetch/clean HowToCook and refresh processed indices.
- `uv run python scripts/run_pipeline.py U123` – execute the end-to-end GraphRAG path for a seeded user.
- `uv run graph-rag-recipes "番茄炒蛋"` – call the console entry point with either a recipe title or user ID.
- `uv run pytest -q` – run the test suite locally; add `-k graph_builder` for targeted checks.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, keep `from __future__ import annotations` plus full type hints (see `pipeline.py`). Use `snake_case` for functions/modules, `PascalCase` for classes (`RecipeGraphBuilder`, `LLMGenerator`), and dataclasses or TypedDicts for structured payloads in `data_models.py`. Maintain bilingual docstrings/comments where they already exist, and route configurable values through `ProjectConfig` instead of hard-coded paths.

## Testing Guidelines
Leverage `pytest` (declared in `project.optional-dependencies.dev`); place new suites under `tests/` mirroring the package path and name files `test_<module>.py`. Mock external LLM calls by stubbing `LLMGenerator.generate` and rely on `HowToCookIngestor.load_sample_records()` or `data/processed/sample_recipes.json` for deterministic fixtures. Prefer behavior-driven assertions around graph traversal, retrieval fallbacks, and embedding queries, and aim for >80% coverage on any feature you touch.

## Commit & Pull Request Guidelines
Commits follow the Conventional Commits style already in history (`feat: add openai model…`); use `feat|fix|refactor|docs|chore` prefixes plus a concise scope. Each PR should summarize the change, list reproduction/validation commands (e.g., `uv run pytest` + the relevant pipeline invocation), link the tracking issue, and include CLI output or screenshots when the UX changes.

## Data & Configuration Tips
Never commit `.env` or raw HowToCook downloads; `.gitignore` already protects `data/raw/*` and most processed artifacts—add new large files to that list before generating them. Document any new knobs in `src/graph_rag_recipes/config.py` and mirror them in `.env.example`. Secrets such as `OPENAI_API_KEY` are loaded via `python-dotenv`; always reference them through `ProjectConfig` so agents and humans can override settings without editing code.
