import { BrandLogo } from "@/components/brand/BrandLogo";

export function LoadingScreen({ label = "Loading workspace…" }: { label?: string }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-5 px-6">
      <div className="relative">
        <div className="absolute inset-0 animate-ping rounded-2xl bg-teal-700/20" />
        <BrandLogo showWordmark={false} markClassName="relative h-12 w-12" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium">{label}</p>
        <p className="mt-1 text-xs text-muted-foreground">Preparing your receptionist dashboard</p>
      </div>
      <div className="h-1 w-40 overflow-hidden rounded-full bg-muted">
        <div className="h-full w-1/2 animate-[loading_1.2s_ease-in-out_infinite] rounded-full bg-teal-700" />
      </div>
      <style>{`@keyframes loading { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }`}</style>
    </div>
  );
}
