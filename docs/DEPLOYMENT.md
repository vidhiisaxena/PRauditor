# Deployment

PRAuditor deploys as three services: **database → Neon**, **backend → Render**,
**frontend → Vercel**, wired together by a **GitHub App**.

## 1. Database — Neon

1. Create a project at [neon.tech] and copy the connection string
   (`postgresql://...neon.tech/...?sslmode=require`).
2. Run the migrations against it from your machine (repo root, venv active):
   ```bash
   DATABASE_URL="<neon-url>" alembic upgrade head    # macOS/Linux
   # PowerShell: $env:DATABASE_URL="<neon-url>"; alembic upgrade head
   ```
   You should see the migrations applied and the three tables created.

## 2. Backend — Render

1. Create a **Web Service** from this GitHub repo (a `render.yaml` is included).
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Environment variables** (see [`.env.example`](../.env.example)):
   `DATABASE_URL` (the Neon URL), `GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`
   (paste the PEM contents — the file is gitignored), `GITHUB_INSTALLATION_ID`,
   `GITHUB_WEBHOOK_SECRET`, `GPT_API_URL`, `GPT_API_KEY`, `GPT_MODEL`, and
   `CORS_ORIGINS` (your Vercel URL).
5. Deploy, then confirm `https://<render-app>.onrender.com/` returns `{"status":"ok"}`.

## 3. Frontend — Vercel

1. Import the repo and set **Root Directory = `frontend`**.
2. Add env var `NEXT_PUBLIC_BACKEND_URL = https://<render-app>.onrender.com`.
   > `NEXT_PUBLIC_*` vars are baked in **at build time** — set it *before*
   > building, and **redeploy** after any change to it.
3. Deploy. Vercel builds `next build` automatically.

## 4. Wire up the GitHub App

1. Set the App's **Webhook URL** to
   `https://<render-app>.onrender.com/api/webhook/github/webhook`.
2. Ensure the **Webhook secret** matches `GITHUB_WEBHOOK_SECRET` on Render.
3. Confirm the App has **Pull requests: Read & write** + **Contents: Read** and
   is subscribed to the **Pull request** event.
4. Add your Vercel origin to `CORS_ORIGINS` on Render (exact, no trailing slash).

## 5. Verify end to end

Open a pull request on an installed repo and check:
- Render logs show the webhook received and the review running.
- The PR gets a Markdown review comment.
- The Vercel dashboard shows the repo, PR, and issues.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Frontend "failed to load" | `NEXT_PUBLIC_BACKEND_URL` unset/stale (rebuild), or the origin missing from `CORS_ORIGINS`. |
| `No 'Access-Control-Allow-Origin'` in console | The exact Vercel origin isn't in `CORS_ORIGINS` (check for trailing slash / typo), or Render is on old code. |
| `column ... does not exist` (500) | Migrations not applied to the deployed DB — run `alembic upgrade head` against it. |
| No new PRs appear | GitHub can't reach the backend — verify the webhook URL and that the service is live. |
| Webhook `401` | `GITHUB_WEBHOOK_SECRET` mismatch between GitHub and the backend. |
