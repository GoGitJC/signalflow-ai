import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";
import { ErrorState } from "@/components/shared/EmptyState";
import { ToastSystem } from "@/hooks/useToast";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useTheme } from "@/hooks/useTheme";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { AppointmentsPage } from "@/pages/AppointmentsPage";
import { CallsPage } from "@/pages/CallsPage";
import { CustomersPage } from "@/pages/CustomersPage";
import { HelpPage } from "@/pages/HelpPage";
import { KnowledgePage } from "@/pages/KnowledgePage";
import { OverviewPage } from "@/pages/OverviewPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { VoiceAgentPage } from "@/pages/VoiceAgentPage";
import type { Call, PageId } from "@/types";

export default function App() {
  return (
    <ToastSystem>
      <AppShell />
    </ToastSystem>
  );
}

function AppShell() {
  const data = useDashboardData();
  const { theme, toggleTheme } = useTheme();
  const [page, setPage] = useState<PageId>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "/" && !(event.target instanceof HTMLInputElement) && !(event.target instanceof HTMLTextAreaElement)) {
        event.preventDefault();
        const input = document.querySelector<HTMLInputElement>('input[aria-label="Search calls, appointments, knowledge…"]');
        input?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const loading = data.status === "loading" || data.status === "idle";

  const openCall = (call: Call) => {
    setSelectedCall(call);
    setPage("calls");
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar
        page={page}
        onNavigate={(next) => {
          setSelectedCall(null);
          setPage(next);
        }}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNav
          search={search}
          onSearch={setSearch}
          onMenu={() => setSidebarOpen(true)}
          onRefresh={() => void data.reload()}
          theme={theme}
          onToggleTheme={toggleTheme}
          apiStatus={data.apiOnline ? "online" : "offline"}
        />
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
          {data.status === "error" && page !== "settings" && page !== "help" && page !== "voice-agent" ? (
            <ErrorState description={data.error} onRetry={() => void data.reload()} />
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={`${page}-${selectedCall?.id ?? "list"}`}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
              >
                {page === "overview" ? (
                  <OverviewPage
                    calls={filterBySearch(data.calls, search)}
                    appointments={data.appointments}
                    loading={loading}
                    apiOnline={data.apiOnline}
                    onOpenCall={openCall}
                  />
                ) : null}
                {page === "calls" ? (
                  <CallsPage
                    calls={filterBySearch(data.calls, search)}
                    loading={loading}
                    selected={selectedCall}
                    onSelect={setSelectedCall}
                    onBack={() => setSelectedCall(null)}
                  />
                ) : null}
                {page === "appointments" ? (
                  <AppointmentsPage appointments={data.appointments} loading={loading} />
                ) : null}
                {page === "knowledge" ? (
                  <KnowledgePage
                    businessId={data.businessId}
                    entries={data.knowledge}
                    loading={loading}
                    onReload={data.reload}
                  />
                ) : null}
                {page === "voice-agent" ? <VoiceAgentPage /> : null}
                {page === "customers" ? <CustomersPage calls={data.calls} loading={loading} /> : null}
                {page === "analytics" ? (
                  <AnalyticsPage calls={data.calls} appointments={data.appointments} loading={loading} />
                ) : null}
                {page === "settings" ? <SettingsPage /> : null}
                {page === "help" ? <HelpPage /> : null}
              </motion.div>
            </AnimatePresence>
          )}
        </main>
      </div>
    </div>
  );
}

function filterBySearch(calls: Call[], search: string) {
  const q = search.trim().toLowerCase();
  if (!q) return calls;
  return calls.filter((call) =>
    [call.intent, call.outcome, call.summary, call.transcript, call.retell_call_id]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q)),
  );
}
