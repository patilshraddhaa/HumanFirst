import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { AuthUser } from "../client/types.gen";

type AuthContextValue = { isBootstrapping: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void; register: (name: string, email: string, password: string) => Promise<void>; user: AuthUser | null; };
const AuthContext = createContext<AuthContextValue | null>(null);
const KEY = "humanfirst-author";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient(); const [user, setUser] = useState<AuthUser | null>(null); const [isBootstrapping, setIsBootstrapping] = useState(true);
  useEffect(() => { const saved = localStorage.getItem(KEY); if (saved) setUser(JSON.parse(saved)); setIsBootstrapping(false); }, []);
  const save = (name: string, email: string) => { const author: AuthUser = { id: "local-author", name: name || "Writer", display_name: name || "Writer", email, mcp_token: "local-demo", created_at: new Date().toISOString() }; localStorage.setItem(KEY, JSON.stringify(author)); setUser(author); };
  const value = useMemo<AuthContextValue>(() => ({ isBootstrapping, async login(email) { save(email.split("@")[0], email); }, async register(name, email) { save(name, email); }, logout() { localStorage.removeItem(KEY); setUser(null); void queryClient.cancelQueries(); queryClient.removeQueries(); }, user }), [isBootstrapping, queryClient, user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() { const context = useContext(AuthContext); if (!context) throw new Error("useAuth must be used inside AuthProvider"); return context; }
