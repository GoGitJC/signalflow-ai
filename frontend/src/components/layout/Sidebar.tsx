import {
  BookOpen,
  Bot,
  CalendarDays,
  CircleHelp,
  ClipboardCheck,
  LayoutDashboard,
  LineChart,
  PhoneCall,
  Settings,
  Users,
  X,
} from "lucide-react";
import type { PageId } from "@/types";
import { cn } from "@/lib/utils";
import { BrandLogo } from "@/components/brand/BrandLogo";

const items: Array<{ id: PageId; label: string; icon: typeof LayoutDashboard }> = [
  { id: "overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "calls", label: "Calls", icon: PhoneCall },
  { id: "appointments", label: "Appointments", icon: CalendarDays },
  { id: "knowledge", label: "Knowledge Base", icon: BookOpen },
  { id: "voice-agent", label: "Voice Agent", icon: Bot },
  { id: "customers", label: "Customers", icon: Users },
  { id: "analytics", label: "Analytics", icon: LineChart },
  { id: "readiness", label: "Acceptance", icon: ClipboardCheck },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "help", label: "Help", icon: CircleHelp },
];

export function Sidebar({
  page,
  onNavigate,
  open,
  onClose,
}: {
  page: PageId;
  onNavigate: (page: PageId) => void;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-40 bg-slate-950/40 transition-opacity lg:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/5 bg-sidebar text-sidebar-foreground transition-transform duration-200 lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <BrandLogo
            className="text-white"
            markClassName="h-8 w-8"
          />
          <button type="button" className="rounded-lg p-2 text-sidebar-muted lg:hidden" onClick={onClose}>
            <X className="h-4 w-4" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3 pb-6">
          {items.map(({ id, label, icon: Icon }) => {
            const active = page === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => {
                  onNavigate(id);
                  onClose();
                }}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors duration-200",
                  active
                    ? "bg-sidebar-active text-white"
                    : "text-sidebar-muted hover:bg-white/5 hover:text-white",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </button>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
