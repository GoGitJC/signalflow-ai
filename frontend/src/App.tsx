import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";
import { ErrorState } from "@/components/shared/EmptyState";
import { ToastSystem } from "@/hooks/useToast";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useTheme } from "@/hooks/useTheme";
import { useAuth } from "@/auth/AuthProvider";
import { GuestRoute, ProtectedRoute } from "@/auth/guards";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { AppointmentsPage } from "@/pages/AppointmentsPage";
import { CallsPage } from "@/pages/CallsPage";
import { CustomersPage } from "@/pages/CustomersPage";
import { HelpPage } from "@/pages/HelpPage";
import { KnowledgePage } from "@/pages/KnowledgePage";
import { OverviewPage } from "@/pages/OverviewPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { VoiceAgentPage } from "@/pages/VoiceAgentPage";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { ForgotPasswordPage } from "@/pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/auth/ResetPasswordPage";
import { AcceptInvitePage } from "@/pages/auth/AcceptInvitePage";
import {
  EmailVerificationPage,
  SessionExpiredPage,
  UnauthorizedPage,
} from "@/pages/auth/StatusPages";
import type { Call, PageId } from "@/types";

const pathToPage: Record<string, PageId> = {
  "/": "overview",
  "/calls": "calls",
  "/appointments": "appointments",
  "/knowledge": "knowledge",
  "/voice-agent": "voice-agent",
  "/customers": "customers",
  "/analytics": "analytics",
  "/settings": "settings",
  "/help": "help",
};

export default function App() {
  return (
    <ToastSystem>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/accept-invite" element={<AcceptInvitePage />} />
        </Route>
        <Route path="/session-expired" element={<SessionExpiredPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/verify-email" element={<EmailVerificationPage />} />
          <Route path="/*" element={<AppShell />} />
        </Route>
      </Routes>
    </ToastSystem>
  );
}

function AppShell() {
  const data = useDashboardData();
  const { theme, toggleTheme } = useTheme();
  const { logout, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState("");
  const page = pathToPage[location.pathname] ?? (location.pathname.startsWith("/calls/") ? "calls" : "overview");

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === "/" &&
        !(event.target instanceof HTMLInputElement) &&
        !(event.target instanceof HTMLTextAreaElement)
      ) {
        event.preventDefault();
        const input = document.querySelector<HTMLInputElement>(
          'input[aria-label="Search calls, appointments, knowledge…"]',
        );
        input?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const loading = data.status === "loading" || data.status === "idle";

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar
        page={page}
        onNavigate={(next) => {
          const href =
            next === "overview"
              ? "/"
              : next === "voice-agent"
                ? "/voice-agent"
                : `/${next}`;
          navigate(href);
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
          userLabel={user?.name}
          onLogout={() => void logout().then(() => navigate("/login"))}
        />
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8">
          {data.status === "error" && page !== "settings" && page !== "help" && page !== "voice-agent" ? (
            <ErrorState description={data.error} onRetry={() => void data.reload()} />
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
              >
                <Routes>
                  <Route
                    path="/"
                    element={
                      <OverviewPage
                        calls={filterBySearch(data.calls, search)}
                        appointments={data.appointments}
                        loading={loading}
                        apiOnline={data.apiOnline}
                        onOpenCall={(call) => navigate(`/calls/${call.id}`)}
                      />
                    }
                  />
                  <Route
                    path="/calls"
                    element={
                      <CallsPage
                        calls={filterBySearch(data.calls, search)}
                        callers={data.callers}
                        loading={loading}
                        selected={null}
                        onSelect={(call) => call && navigate(`/calls/${call.id}`)}
                        onBack={() => navigate("/calls")}
                      />
                    }
                  />
                  <Route path="/calls/:callId" element={<CallDetailRoute calls={data.calls} callers={data.callers} loading={loading} />} />
                  <Route
                    path="/appointments"
                    element={
                      <AppointmentsPage
                        appointments={data.appointments}
                        callers={data.callers}
                        loading={loading}
                      />
                    }
                  />
                  <Route
                    path="/knowledge"
                    element={
                      <KnowledgePage
                        businessId={data.businessId}
                        entries={data.knowledge}
                        loading={loading}
                        onReload={data.reload}
                      />
                    }
                  />
                  <Route path="/voice-agent" element={<VoiceAgentPage businessId={data.businessId} />} />
                  <Route
                    path="/customers"
                    element={
                      <CustomersPage
                        businessId={data.businessId}
                        callers={data.callers}
                        calls={data.calls}
                        appointments={data.appointments}
                        loading={loading}
                      />
                    }
                  />
                  <Route
                    path="/analytics"
                    element={
                      <AnalyticsPage
                        businessId={data.businessId}
                        calls={data.calls}
                        appointments={data.appointments}
                        loading={loading}
                      />
                    }
                  />
                  <Route path="/settings" element={<SettingsPage businessId={data.businessId} />} />
                  <Route path="/help" element={<HelpPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          )}
        </main>
      </div>
    </div>
  );
}

function CallDetailRoute({
  calls,
  callers,
  loading,
}: {
  calls: Call[];
  callers: import("@/types").Caller[];
  loading: boolean;
}) {
  const { callId } = useParams();
  const navigate = useNavigate();
  const selected = calls.find((call) => call.id === callId) ?? null;
  return (
    <CallsPage
      calls={calls}
      callers={callers}
      loading={loading}
      selected={selected}
      onSelect={(call) => (call ? navigate(`/calls/${call.id}`) : navigate("/calls"))}
      onBack={() => navigate("/calls")}
    />
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
