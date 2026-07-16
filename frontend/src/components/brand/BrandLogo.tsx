import { cn } from "@/lib/utils";

export function BrandLogo({
  className,
  markClassName,
  showWordmark = true,
}: {
  className?: string;
  markClassName?: string;
  showWordmark?: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <svg
        className={cn("h-8 w-8 shrink-0", markClassName)}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <rect width="64" height="64" rx="14" fill="#0F766E" />
        <path
          d="M14 34c6-14 10-14 16 0s10 14 16 0"
          stroke="#ECFDF5"
          strokeWidth="4"
          strokeLinecap="round"
        />
        <circle cx="46" cy="22" r="4" fill="#99F6E4" />
      </svg>
      {showWordmark ? (
        <div className="leading-tight">
          <div className="text-sm font-semibold tracking-tight">SignalFlow AI</div>
          <div className="text-[11px] opacity-70">Receptionist OS</div>
        </div>
      ) : null}
    </div>
  );
}
