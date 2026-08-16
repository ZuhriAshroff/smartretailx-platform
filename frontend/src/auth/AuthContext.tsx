import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { jwtDecode } from "jwt-decode";
import * as authApi from "../api/auth";
import { TOKEN_STORAGE_KEY } from "../api/client";
import type { JwtPayload, Role } from "../types";

interface AuthUser {
  id: number;
  email: string;
  role: Role;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function decodeUser(token: string): AuthUser | null {
  try {
    const payload = jwtDecode<JwtPayload>(token);
    if (payload.exp * 1000 < Date.now()) return null;
    return { id: Number(payload.sub), email: payload.email, role: payload.role };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
    return stored ? decodeUser(stored) : null;
  });

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login({ email, password });
    localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
    setToken(result.access_token);
    setUser(decodeUser(result.access_token));
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    await authApi.register({ email, password, full_name: fullName });
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, token, login, register, logout }), [user, token, login, register, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
