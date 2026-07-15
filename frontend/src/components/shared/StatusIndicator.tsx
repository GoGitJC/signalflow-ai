import { cn } from "@/lib/utils";

export function StatusIndicator({
  status,
  label,
}: {
  status: "online" | "degraded" | "offline" | "idle";
  label?: string;
}) {
  const color =
    status === "online"
      ? "bg-success"
      : status === "degraded"
        ? "bg-warning"
        : status === "offline"
          ? "bg-danger"
          : "bg-muted-foreground";

  return (
    <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
      <span className={cn("h-2 w-2 rounded-full", color)} />
      {label ?? status}
    </span>
  );
}
