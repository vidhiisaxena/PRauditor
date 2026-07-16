"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLSpanElement> {
  src?: string | null;
  alt?: string;
  /** Fallback initials shown when there is no image or it fails to load. */
  fallback: string;
}

/**
 * Small avatar with an initials fallback. Hand-rolled (no Radix) to keep the
 * dependency surface small — the image simply hides itself on error.
 */
const Avatar = React.forwardRef<HTMLSpanElement, AvatarProps>(
  ({ src, alt, fallback, className, ...props }, ref) => {
    const [errored, setErrored] = React.useState(false);
    const showImage = Boolean(src) && !errored;

    return (
      <span
        ref={ref}
        className={cn(
          "relative inline-flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-muted text-xs font-medium text-muted-foreground",
          className,
        )}
        {...props}
      >
        {showImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src as string}
            alt={alt ?? fallback}
            className="h-full w-full object-cover"
            onError={() => setErrored(true)}
          />
        ) : (
          <span aria-hidden>{fallback}</span>
        )}
      </span>
    );
  },
);
Avatar.displayName = "Avatar";

export { Avatar };
