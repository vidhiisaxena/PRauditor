export interface Repository {
  id: number;
  full_name: string;
}

export interface PullRequest {
  id: number;
  pr_number: number;
  title: string | null;
  state: string | null;
  head_sha: string | null;
  last_reviewed_at: string | null;
}

export interface ReviewIssue {
  id: number;
  file_path: string;
  line: number | null;
  kind: string;
  severity: string;
  message: string;
  suggestion: string | null;
  created_at: string;
}
