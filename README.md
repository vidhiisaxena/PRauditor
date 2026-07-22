<div align="center">

# PRAuditor

**AI pull request review that thinks like an experienced engineer.**

PRAuditor is an open-source GitHub App that reviews every pull request with a
multi-agent AI pipeline — checking security, performance, logic, and
readability — and posts clear, structured feedback back to the PR.

[Features](#features) · [Architecture](#architecture) · [Quickstart](#quickstart) · [Deployment](#deployment) · [API](docs/API.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Features

- **Multi-agent review** — four specialised passes over the diff: **Logic**, **Security**, **Performance**, and **Readability**.
- **Structured Markdown reviews** — findings grouped by file, severity, and category, posted straight to the pull request.
- **GitHub App integration** — installs on your repos and reviews PRs automatically via webhooks.
- **Review history & dashboard** — every review is stored and browsable in a Next.js dashboard.
- **Manual rerun** — re-run a review on demand from the API/UI.
- **Bring your own model** — any OpenAI-compatible chat endpoint (set a URL, key, and model name).
- **Open source & self-hostable** — MIT licensed; own your data and your model.

## Tech Stack

| Layer     | Stack |
|-----------|-------|
| Frontend  | Next.js 14 (App Router), TypeScript, TailwindCSS, shadcn/ui, TanStack Query, Framer Motion, Lucide |
| Backend   | FastAPI, SQLAlchemy, Alembic, PyJWT, httpx |
| Database  | PostgreSQL (Neon in production) |
| AI        | Any OpenAI-compatible chat completions endpoint |
| Hosting   | Vercel (frontend) · Render (backend) · Neon (database) |

## Architecture

```
GitHub PR ──webhook──▶ FastAPI ──▶ Review Engine ──▶ LLM
                          │             │
                          │             └─▶ merge/dedupe ─▶ PostgreSQL
                          │                                    ▲
                          └─▶ Markdown comment on PR           │
                                                               │
Next.js frontend ────────────── JSON API ─────────────────────┘
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for the full diagram and a step-by-step walkthrough of a review.

## Repository layout

```
.
├── backend/            FastAPI app
│   ├── main.py         app entry, CORS, router registration
│   ├── api/            routers: dashboard, repo, pull_request, webhook
│   ├── review_pipeline.py   orchestrates the review
│   ├── agents.py       logic / security / performance / readability agents
│   ├── llm_client.py   OpenAI-compatible chat client
│   ├── github_client.py / github_app_auth.py   GitHub App auth + API
│   ├── models.py       SQLAlchemy models
│   └── config.py       env-driven configuration
├── alembic/            database migrations
├── frontend/           Next.js app (landing page + dashboard)
├── requirements.txt    backend dependencies
├── render.yaml         Render deployment config
└── README.md
```

## Quickstart

### Prerequisites
- Python 3.11+, Node 18+, a PostgreSQL database
- A [GitHub App](docs/API.md#github-app-setup) (App ID, private key, webhook secret)
- An OpenAI-compatible LLM endpoint + key

### 1. Backend

```bash
# from the repository root
python -m venv venv_new
venv_new\Scripts\activate            # Windows
# source venv_new/bin/activate       # macOS/Linux

pip install -r requirements.txt
cp .env.example .env                  # then fill in the values

alembic upgrade head                  # create tables
uvicorn backend.main:app --reload --port 8000
```

> ⚠️ Always run the backend from the **repository root** (`uvicorn backend.main:app`),
> not from inside `backend/` — the code uses package-relative imports.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local            # set NEXT_PUBLIC_BACKEND_URL
npm run dev                           # http://localhost:3000
```

### 3. Expose the webhook (local)

GitHub can't reach `localhost`. During local development, tunnel your backend
(e.g. `ngrok http 8000`) and point the GitHub App's webhook at
`https://<tunnel>/api/webhook/github/webhook`.

## Configuration

Backend environment variables (see [`.env.example`](.env.example)):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_PRIVATE_KEY` | App private key (PEM contents) — or `GITHUB_PRIVATE_KEY_PATH` |
| `GITHUB_INSTALLATION_ID` | Fallback installation id |
| `GITHUB_WEBHOOK_SECRET` | Secret used to verify webhook signatures |
| `GPT_API_URL` | OpenAI-compatible chat completions URL |
| `GPT_API_KEY` | API key for the LLM |
| `GPT_MODEL` | Model name (default `gpt-4o-mini`) |
| `CORS_ORIGINS` | Comma-separated allowed browser origins |

Frontend: `NEXT_PUBLIC_BACKEND_URL` (the backend base URL).

## Deployment

PRAuditor is designed for **Neon + Render + Vercel**:

1. **Database (Neon):** create a project, then `DATABASE_URL=<neon-url> alembic upgrade head`.
2. **Backend (Render):** deploy from this repo (`render.yaml`), start command
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, and set all backend env vars.
3. **Frontend (Vercel):** import the repo with **Root Directory = `frontend`** and set
   `NEXT_PUBLIC_BACKEND_URL` to the Render URL, then redeploy.
4. **GitHub App:** set the webhook URL to `https://<render-app>/api/webhook/github/webhook`
   and add your Vercel domain to `CORS_ORIGINS`.

Full steps in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## API

See **[docs/API.md](docs/API.md)** for the full endpoint reference.

## Roadmap

- [ ] Risk scoring per PR (severity × complexity × file count)
- [ ] Inline line comments + one-click suggested fixes
- [ ] PR summary agent
- [ ] Multi-user / organizations
- [ ] Analytics (PRs reviewed, issues prevented)

## License

[MIT](LICENSE) © PRAuditor contributors.
