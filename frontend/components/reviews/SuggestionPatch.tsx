"use client";

import { useState } from "react";
import { Check, Copy, GitCommitHorizontal } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SuggestionPatchProps {
  suggestion: string;
}

type PatchLine = { type: "add" | "del" | "context"; text: string };

/**
 * Detect whether the suggestion is already a diff (lines starting with +/-).
 * If so we render it as a coloured patch; otherwise we treat the whole thing as
 * proposed code (a GitHub-style "suggested change" block).
 */
function parsePatch(suggestion: string): PatchLine[] {
  const lines = suggestion.replace(/\r\n/g, "\n").split("\n");
  const looksLikeDiff = lines.some(
    (l) => /^[+-]/.test(l) && !l.startsWith("+++") && !l.startsWith("---"),
  );

  if (!looksLikeDiff) {
    return lines.map((text) => ({ type: "add", text }));
  }

  return lines.map((line) => {
    if (line.startsWith("+")) return { type: "add", text: line.slice(1) };
    if (line.startsWith("-")) return { type: "del", text: line.slice(1) };
    return { type: "context", text: line.replace(/^ /, "") };
  });
}

const LINE_STYLES: Record<PatchLine["type"], string> = {
  add: "bg-primary/10 text-foreground before:content-['+'] before:text-primary",
  del: "bg-destructive/10 text-foreground before:content-['-'] before:text-destructive",
  context: "text-muted-foreground before:content-['']",
};

/** Renders a suggested fix as a copyable, commit-ready patch block. */
export function SuggestionPatch({ suggestion }: SuggestionPatchProps) {
  const [copied, setCopied] = useState(false);
  const patch = parsePatch(suggestion);

  // Copy the proposed (added) lines, or the raw suggestion if it's plain code.
  const copyText = patch
    .filter((l) => l.type !== "del")
    .map((l) => l.text)
    .join("\n");

  async function copy() {
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard may be unavailable */
    }
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <div className="flex items-center justify-between border-b bg-muted/50 px-3 py-1.5">
        <span className="text-xs font-medium text-muted-foreground">
          Suggested fix
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2 text-xs"
            onClick={copy}
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" /> Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" /> Copy
              </>
            )}
          </Button>
          {/* TODO(backend): POST /api/prs/{prId}/issues/{issueId}/apply */}
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 px-2 text-xs"
            disabled
            title="Commit suggestion — waiting on backend endpoint"
          >
            <GitCommitHorizontal className="h-3.5 w-3.5" /> Commit
          </Button>
        </div>
      </div>
      <pre className="overflow-x-auto bg-card px-3 py-2 font-mono text-xs leading-relaxed">
        {patch.map((line, i) => (
          <div
            key={i}
            className={cn(
              "whitespace-pre before:mr-2 before:inline-block before:w-2 before:text-center",
              LINE_STYLES[line.type],
            )}
          >
            {line.text || " "}
          </div>
        ))}
      </pre>
    </div>
  );
}
