import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

function EmptyIllustration() {
  return (
    <svg viewBox="0 0 160 96" className="mb-4 h-24 w-40 text-teal-800/80 dark:text-teal-300/80" aria-hidden>
      <rect x="8" y="20" width="144" height="60" rx="12" fill="currentColor" opacity="0.08" />
      <path
        d="M28 58c12-22 20-22 32 0s20 22 32 0 20-22 32 0"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.55"
      />
      <circle cx="120" cy="36" r="6" fill="currentColor" opacity="0.35" />
    </svg>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  helpHref,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  helpHref?: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center px-6 py-16 text-center">
        <EmptyIllustration />
        <div className="mb-3 rounded-2xl bg-muted p-3 text-muted-foreground">
          <Icon className="h-5 w-5" />
        </div>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">{description}</p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {actionLabel && onAction ? <Button onClick={onAction}>{actionLabel}</Button> : null}
          {helpHref ? (
            <Button asChild variant="outline">
              <a href={helpHref}>Help</a>
            </Button>
          ) : (
            <Button asChild variant="ghost">
              <a href="/help">Open Help</a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: {
  title?: string;
  description: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-danger/20">
      <CardContent className="flex flex-col items-start gap-3 p-6">
        <h3 className="text-base font-semibold text-danger">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex flex-wrap gap-2">
          {onRetry ? (
            <Button variant="outline" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
          <Button asChild variant="ghost">
            <a href="/help">Help</a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
