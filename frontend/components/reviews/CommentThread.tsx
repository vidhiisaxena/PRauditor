"use client";

import { useState } from "react";
import { MessageSquare, Send } from "lucide-react";

import { formatRelativeTime } from "@/lib/format";
import { ApiError, NotImplementedError } from "@/lib/api-client";
import {
  useAddComment,
  useReviewComments,
} from "@/hooks/useReviewComments";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { ReviewComment } from "@/types";

interface CommentThreadProps {
  prId: number;
  issueId: number;
}

/** Inline discussion pinned to a single finding: existing comments + composer. */
export function CommentThread({ prId, issueId }: CommentThreadProps) {
  const { data: allComments } = useReviewComments(prId);
  const comments = (allComments ?? []).filter((c) => c.issueId === issueId);
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <MessageSquare className="h-3.5 w-3.5" />
        {comments.length > 0
          ? `${comments.length} comment${comments.length === 1 ? "" : "s"}`
          : "Add comment"}
      </button>

      {open || comments.length > 0 ? (
        <div className="mt-2 space-y-3 border-l-2 pl-3">
          {comments.map((comment) => (
            <CommentItem key={comment.id} comment={comment} />
          ))}
          <CommentComposer prId={prId} issueId={issueId} />
        </div>
      ) : null}
    </div>
  );
}

function CommentItem({ comment }: { comment: ReviewComment }) {
  return (
    <div className="flex gap-2">
      <Avatar
        src={comment.author.avatarUrl}
        alt={comment.author.login}
        fallback={comment.author.login.slice(0, 2).toUpperCase()}
        className="h-6 w-6"
      />
      <div className="min-w-0">
        <p className="text-xs">
          <span className="font-medium">{comment.author.login}</span>{" "}
          <span className="text-muted-foreground">
            {formatRelativeTime(comment.createdAt)}
          </span>
        </p>
        <p className="mt-0.5 whitespace-pre-wrap text-sm">{comment.body}</p>
      </div>
    </div>
  );
}

function CommentComposer({ prId, issueId }: CommentThreadProps) {
  const [body, setBody] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const addComment = useAddComment(prId);

  async function submit() {
    const trimmed = body.trim();
    if (!trimmed) return;
    setNote(null);
    try {
      await addComment.mutateAsync({ issueId, body: trimmed });
      setBody("");
    } catch (error) {
      setNote(
        error instanceof NotImplementedError
          ? "Commenting needs the backend endpoint (POST /api/prs/{id}/comments)."
          : error instanceof ApiError
            ? "Could not post the comment."
            : "Something went wrong.",
      );
    }
  }

  return (
    <div className="space-y-2">
      <Textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Leave a comment on this finding…"
        aria-label="Comment"
        className="min-h-[64px] text-sm"
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === "Enter") void submit();
        }}
      />
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] text-muted-foreground">⌘/Ctrl + Enter</span>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={submit}
          disabled={!body.trim() || addComment.isPending}
        >
          <Send className="h-3.5 w-3.5" />
          {addComment.isPending ? "Posting…" : "Comment"}
        </Button>
      </div>
      {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
    </div>
  );
}
