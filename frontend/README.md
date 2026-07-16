# PRAuditor Frontend

Next.js 14 dashboard for **PRAuditor**, an AI multi-agent GitHub Pull Request
review platform. This app visualises repositories, pull requests, and the review
issues produced by the FastAPI backend.

## Tech Stack

- **Next.js 14** (App Router) + **TypeScript** (strict, no `any`)
- **TailwindCSS** with CSS-variable theming (light + dark)
- **shadcn/ui**-style primitives (Radix under the hood) + **Lucide** icons
- **TanStack Query** for server-state (caching, loading/error states)

## Getting Started

```bash
npm install
cp .env.example .env.local   # then edit if your backend is elsewhere
npm run dev                  # http://localhost:3000
```

### Environment

| Variable                  | Default                 | Purpose                        |
| ------------------------- | ----------------------- | ------------------------------ |
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

> The backend must send **CORS** headers for `http://localhost:3000` (or your
> deployed origin) or browser requests will be blocked.

### Scripts

- `npm run dev` — dev server
- `npm run build` — production build (also type-checks + lints)
- `npm run lint` — Next.js lint

## Architecture

The guiding rule: **pages are thin, business logic is not in `page.tsx`.**
Data flows in one direction:

```
page.tsx  →  feature view (components/<feature>)  →  hook (hooks/)  →  service (services/)  →  api-client (lib/)
```

- **Pages** only parse route params and render a feature view.
- **Feature views** own data-fetching (via hooks) and layout/state.
- **Hooks** wrap TanStack Query with centralised query keys.
- **Services** are the *only* place that maps to backend endpoints.
- **`lib/api-client.ts`** is the *only* place that calls `fetch`.
- **`lib/review.ts`** holds pure domain logic (severity normalisation,
  summarisation, grouping by file) so it stays testable and reusable.

### Folder layout

```
app/
├── layout.tsx              # Root layout: Providers + AppShell + theme init
├── providers.tsx           # TanStack Query client
├── page.tsx                # Dashboard route
├── repos/page.tsx          # Repository list route
├── repos/[repoId]/page.tsx # Repository detail route
└── prs/[prId]/page.tsx     # Review detail route (main screen)

components/
├── ui/            # shadcn-style primitives: button, card, badge, dialog, …
├── common/        # PageHeader, SearchInput, EmptyState, ErrorCard,
│                  # LoadingSkeleton, ConfirmDialog, SeverityBadge,
│                  # StatusBadge, RiskScore
├── layout/        # AppShell, Sidebar, Topbar, ThemeToggle
├── dashboard/     # DashboardView, StatsCard, RecentReviews
├── repositories/  # RepositoriesView, RepositoryCard, RepositoryDetailView
├── pullrequests/  # PullRequestList, PRCard
└── reviews/       # ReviewDetailView, ReviewSummarySidebar,
                   # FileIssueSection (collapsible), IssueCard, ReviewActions

hooks/       # useRepositories, usePullRequests, useReviewIssues,
             # useDashboardStats, queryKeys
services/    # repositories, pullRequests, reviews, dashboard
lib/         # api-client, config, utils (cn), format, review
types/       # domain types + derived view-models
```

## Routes

| Route             | Screen            | Data source                          |
| ----------------- | ----------------- | ------------------------------------ |
| `/`               | Dashboard         | aggregated stats + recent reviews    |
| `/repos`          | Repository list   | `GET /api/repos`                     |
| `/repos/[repoId]` | Repository detail | `GET /api/repos/{repoId}/prs`        |
| `/prs/[prId]`     | Review detail     | `GET /api/prs/{prId}/issues`         |

## Backend integration

Existing `GET` endpoints are wired up. Everything else is a **typed stub** that
throws `NotImplementedError`, ready to be filled in. Search the codebase for
`TODO(backend)` to find each integration point.

| Capability            | Status | Endpoint (expected)               | Where                       |
| --------------------- | ------ | --------------------------------- | --------------------------- |
| List repositories     | ✅ live | `GET /api/repos`                  | `services/repositories.ts`  |
| List pull requests    | ✅ live | `GET /api/repos/{repoId}/prs`     | `services/pullRequests.ts`  |
| List review issues    | ✅ live | `GET /api/prs/{prId}/issues`      | `services/reviews.ts`       |
| Dashboard stats       | ⏳ stub | `GET /api/dashboard`              | `services/dashboard.ts` (aggregates client-side for now) |
| Single repository     | ⏳ stub | `GET /api/repos/{repoId}`         | resolved from cached list   |
| Single pull request   | ⏳ stub | `GET /api/prs/{prId}`             | `services/pullRequests.ts`  |
| Re-run review         | ⏳ stub | `POST /api/prs/{prId}/rerun`      | `services/pullRequests.ts`  |
| Merge PR              | ⏳ stub | `POST /api/prs/{prId}/merge`      | `services/pullRequests.ts`  |
| Post comment          | ⏳ stub | `POST /api/prs/{prId}/comment`    | `services/reviews.ts`       |

### Wiring up a future action (example: re-run review)

1. Implement the call in the service (uncomment the `apiClient.post(...)` line).
2. Add a mutation hook, e.g. `useRerunReview(prId)`, that on success
   invalidates `queryKeys.reviewIssues(prId)` (and `queryKeys.dashboard`).
3. Enable the button in `components/reviews/ReviewActions.tsx`; wrap destructive
   actions (Merge) in `<ConfirmDialog/>`.

## Design & conventions

- Minimal, developer-focused UI (GitHub / Vercel / Linear), neutral palette,
  generous whitespace, subtle borders. No gradients, glassmorphism, or heavy
  animation.
- **Risk scores** are placeholders (`RiskScore`, derived risk level) until the
  backend Risk Scoring agent exists — marked `TODO(backend)`.
- Every list supports **loading**, **error + retry**, and **empty** states.
- Dark mode works today (theme toggle in the top bar); structured to fold into a
  future settings panel.

## Extensibility

Structured so upcoming features drop in without refactors: GitHub auth / org
switcher (sidebar slot), notifications (topbar slot), analytics (new
`components/analytics/` + service), review history, and inline GitHub comments.
