# Contributing to PRAuditor

Thanks for your interest — contributions are welcome, and PRs get reviewed by
PRAuditor itself. 🙂

## Getting set up

Follow the [Quickstart](README.md#quickstart) to run the backend and frontend
locally. You'll need Python 3.11+, Node 18+, a PostgreSQL database, a GitHub
App, and an OpenAI-compatible LLM endpoint.

## Development workflow

1. **Fork** the repo and create a branch: `git checkout -b feat/your-thing`.
2. Make your change. Keep it focused — one concern per PR.
3. **Backend:** if you touch models, generate a migration:
   ```bash
   alembic revision --autogenerate -m "describe your change"
   # review the generated file, then:
   alembic upgrade head
   ```
4. **Frontend:** make sure it type-checks and builds:
   ```bash
   cd frontend && npx tsc --noEmit && npm run build
   ```
5. Open a pull request against `main` with a clear description of what and why.

## Conventions

- **Backend** — run from the repo root; use package-relative imports
  (`from .config import ...`). Keep endpoints in the right router under `backend/api/`.
- **Frontend** — pages stay thin; business logic lives in `lib/` and `hooks/`,
  API calls in `services/`, never `fetch` in a component. No `any`.
- Match the style of the surrounding code; keep functions small and named clearly.

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs. actual behaviour, and
relevant logs (redact secrets — never paste tokens, private keys, or database URLs).

## Roadmap

See the [roadmap](README.md#roadmap) for larger efforts that are open for
contribution — risk scoring, inline comments, a background review queue, and
multi-user support are all good places to start.

By contributing, you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
