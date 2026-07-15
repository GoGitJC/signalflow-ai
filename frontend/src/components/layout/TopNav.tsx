import { Menu, Moon, RefreshCw, Sun } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SearchBar } from "@/components/shared/SearchBar";
import { StatusIndicator } from "@/components/shared/StatusIndicator";

export function TopNav({
  search,
  onSearch,
  onMenu,
  onRefresh,
  theme,
  onToggleTheme,
  apiStatus,
}: {
  search: string;
  onSearch: (value: string) => void;
  onMenu: () => void;
  onRefresh: () => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  apiStatus: "online" | "degraded" | "offline";
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6">
        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenu} aria-label="Open menu">
          <Menu className="h-4 w-4" />
        </Button>
        <SearchBar
          value={search}
          onChange={onSearch}
          placeholder="Search calls, appointments, knowledge…"
          className="hidden max-w-md flex-1 md:block"
        />
        <div className="ml-auto flex items-center gap-2">
          <StatusIndicator status={apiStatus} label={apiStatus === "online" ? "Systems nominal" : "API issue"} />
          <Button variant="ghost" size="icon" onClick={onRefresh} aria-label="Refresh data">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onToggleTheme} aria-label="Toggle theme">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button type="button" className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring/40">
                <Avatar name="SignalFlow Operator" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Workspace</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onRefresh}>Refresh dashboard</DropdownMenuItem>
              <DropdownMenuItem onClick={onToggleTheme}>
                {theme === "dark" ? "Light mode" : "Dark mode"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
