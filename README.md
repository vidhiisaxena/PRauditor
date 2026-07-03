# PRauditor

PRauditor is an automated Pull Request Review Agent that analyzes code changes inside a GitHub PR and generates clear, structured, actionable review comments.

## Running the server

Recommended: run the bundled runner which ensures the project root is on `PYTHONPATH`:

```bash
python run_uvicorn.py
```

Alternative: run uvicorn directly from the repository root:

```bash
uvicorn backend.main:app --reload --app-dir .
```
