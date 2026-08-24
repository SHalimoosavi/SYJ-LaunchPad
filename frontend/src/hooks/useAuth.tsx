"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api";
import { clearStoredToken, getStoredToken, setStoredToken } from "@/lib/token-storage";

export interface AuthUser {
  id: string;
  walletAddress: string;
  role: string;
}

export type AuthStatus = "loading" | "unauthenticated" | "authenticated";

interface MeResponse {
  id: string;
  wallet_address: string;
  role: string;
}

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  // On mount, try to resume a session from a previously stored token by
  // asking the backend who it belongs to — this is what makes a page
  // refresh not force a brand-new wallet signature.
  useEffect(() => {
    let cancelled = false;

    async function restoreSession(): Promise<void> {
      const token = getStoredToken();
      if (!token) {
        if (!cancelled) setStatus("unauthenticated");
        return;
      }

      try {
        const me = await apiFetch<MeResponse>("/api/v1/auth/me");
        if (!cancelled) {
          setUser({ id: me.id, walletAddress: me.wallet_address, role: me.role });
          setStatus("authenticated");
        }
      } catch {
        // Token expired, was revoked, or is otherwise invalid — fall back
        // to a clean unauthenticated state rather than looping forever.
        clearStoredToken();
        if (!cancelled) setStatus("unauthenticated");
      }
    }

    void restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback((token: string, nextUser: AuthUser) => {
    setStoredToken(token);
    setUser(nextUser);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
