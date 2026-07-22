# API Reference

Interactive docs at `/docs` (Swagger) when the backend is running.

## Conventions

- All responses are JSON.
- IDs are the database primary keys (not GitHub numbers), except `pr_number`,
  which is the GitHub PR number.
- Severities: `info | minor | major | critical`.
- Issue kinds: `logic | readability | performance | security`.

---

## Health

### `GET /`
```json
{ "status": "ok" }
```

---

## Dashboard

### `GET /api/dashboard`
Aggregate counts across all repositories.
```json
{
  "repositories": 2,
  "pull_requests": 6,
  "reviews": 9,
  "critical": 0,
  "major": 4,
  "minor": 5
}
```

---

## Repositories

### `GET /api/repos/repositories`
List all tracked repositories.
```json
[{ "id": 1, "full_name": "owner/repo", "installation_id": 12345678 }]
```

### `GET /api/repos/{repo_id}`
Summary for one repository.
```json
{ "id": 1, "name": "owner/repo", "prs": 32, "last_review": "2026-07-19T21:03:49Z", "critical": 19 }
```

### `GET /api/repos/{repo_id}/prs`
Pull requests for a repository (newest first).
```json
[{
  "id": 6, "pr_number": 10, "title": "Testing", "state": "open",
  "head_sha": "3060cf1...", "last_reviewed_at": null
}]
```

---

## Pull Requests

### `GET /api/prs/{pr_id}/issues`
All review issues for a PR (newest first).
```json
[{
  "id": 17, "file_path": "src/Stopwatch.jsx", "line": 45,
  "kind": "logic", "severity": "major",
  "message": "Invalid JSX syntax ...", "suggestion": "Remove the invalid block",
  "created_at": "2026-07-19T21:06:43Z"
}]
```

### `GET /api/prs/{pr_id}/summary`
PR metadata plus per-severity counts.
```json
{
  "id": 6, "repo": "owner/repo", "pr_number": 10, "title": "Testing",
  "state": "open", "head_sha": "3060cf1...", "last_reviewed_at": null,
  "issues": { "critical": 2, "major": 5, "minor": 10, "info": 0 }
}
```

### `GET /api/prs/{pr_id}/diff`
The PR's unified diff (fetched live from GitHub via the installation token).
```json
{ "diff": "diff --git a/... b/...\n@@ ... @@\n+ ..." }
```

### `POST /api/prs/{id}/rerun`
Re-run the review pipeline for a PR: refetch the diff, re-run all agents,
replace stored issues, and re-post the PR comment.
```json
{ "reviewed": true, "issues": 4 }
```

---

## Webhook

### `POST /api/webhook/github/webhook`
Called by GitHub. Not for manual use. Behaviour:

- Verifies `X-Hub-Signature-256` against `GITHUB_WEBHOOK_SECRET` (`401` on mismatch).
- Responds `{ "ok": true }` to `ping` events.
- Ignores non–`pull_request` events and actions other than `opened`,
  `reopened`, `synchronize` (returns `{ "ignored": true }`).
- On a relevant PR event: upserts repo + PR, fetches the diff, runs the review,
  stores issues, posts the Markdown comment, and returns
  `{ "reviewed": true, "issues": <n> }`.

---

## GitHub App setup

1. Create a GitHub App with **Pull requests: Read & write** and **Contents: Read**
   permissions, subscribed to the **Pull request** event.
2. Set the **Webhook URL** to `<backend-url>/api/webhook/github/webhook` and a
   **Webhook secret** (matches `GITHUB_WEBHOOK_SECRET`).
3. Generate a **private key** and provide it to the backend via
   `GITHUB_PRIVATE_KEY` (PEM contents) or `GITHUB_PRIVATE_KEY_PATH`.
4. Install the App on the repositories you want reviewed.
