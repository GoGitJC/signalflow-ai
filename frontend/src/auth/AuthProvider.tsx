import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, setBusinessId, type SessionResponse, type SessionUser } from "@/api/client";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  user: SessionUser | null;
  businessId: string;
  isAuthenticated: boolean;
  hasRole: (...roles: string[]) => boolean;
  can: (permission: string) => boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (payload: {
    business_name: string;
    name: string;
    email: string;
    password: string;
    remember_me?: boolean;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
  reloadUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const ROLE_PERMISSIONS: Record<string, string[]> = {
  owner: ["*"],
  admin: [
    "users:read",
    "users:invite",
    "settings:write",
    "integrations:write",
    "audit:read",
    "kb:write",
    "calls:read",
    "appointments:read",
    "customers:write",
  ],
  member: ["calls:read", "appointments:read", "customers:read", "kb:read"],
};

function toUser(session: SessionResponse): SessionUser {
  return {
    id: session.user_id,
    business_id: session.business_id,
    name: session.name,
    email: session.email,
    role: session.role,
    email_verified: session.email_verified,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<SessionUser | null>(null);

  const applySession = useCallback((session: SessionResponse) => {
    const next = toUser(session);
    setUser(next);
    setBusinessId(next.business_id);
    setStatus("authenticated");
  }, []);

  const refreshSession = useCallback(async () => {
    try {
      const session = await api.refresh();
      applySession(session);
      return true;
    } catch {
      setUser(null);
      setStatus("anonymous");
      return false;
    }
  }, [applySession]);

  const reloadUser = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
      setBusinessId(me.business_id);
      setStatus("authenticated");
    } catch {
      const refreshed = await refreshSession();
      if (!refreshed) {
        setUser(null);
        setStatus("anonymous");
      }
    }
  }, [refreshSession]);

  useEffect(() => {
    void reloadUser();
  }, [reloadUser]);

  useEffect(() => {
    if (status !== "authenticated") return;
    const timer = window.setInterval(() => {
      void refreshSession();
    }, 12 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [status, refreshSession]);

  const login = useCallback(
    async (email: string, password: string, rememberMe = false) => {
      const session = await api.login({ email, password, remember_me: rememberMe });
      applySession(session);
    },
    [applySession],
  );

  const register = useCallback(
    async (payload: {
      business_name: string;
      name: string;
      email: string;
      password: string;
      remember_me?: boolean;
    }) => {
      const session = await api.register(payload);
      applySession(session);
    },
    [applySession],
  );

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  const hasRole = useCallback(
    (...roles: string[]) => Boolean(user && roles.includes(user.role)),
    [user],
  );

  const can = useCallback(
    (permission: string) => {
      if (!user) return false;
      const grants = ROLE_PERMISSIONS[user.role] ?? [];
      return grants.includes("*") || grants.includes(permission);
    },
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      user,
      businessId: user?.business_id ?? "",
      isAuthenticated: status === "authenticated",
      hasRole,
      can,
      login,
      register,
      logout,
      refreshSession,
      reloadUser,
    }),
    [status, user, hasRole, can, login, register, logout, refreshSession, reloadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
