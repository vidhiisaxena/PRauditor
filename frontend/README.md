# PRAuditor Frontend

Next.js 14 frontend for the PRAuditor GitHub App - an automated Pull Request Review Agent Dashboard.

## Features

- **Home Page** (`/`) - Shows backend status and navigation
- **Repositories** (`/repos`) - Lists all repositories
- **Repository Detail** (`/repos/[repoId]`) - Shows all PRs for a repository
- **PR Review** (`/prs/[prId]`) - Shows detailed review issues for a PR

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- React 18

## Project Structure

```
frontend/
├── app/                    # Next.js app router pages
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   ├── repos/              # Repository pages
│   └── prs/                # PR review pages
├── components/             # Reusable React components
├── lib/                    # Utility functions (API helpers)
├── types/                  # TypeScript type definitions
└── public/                 # Static assets
```
