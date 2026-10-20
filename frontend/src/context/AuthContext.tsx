import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  clearStoredToken,
  fetchCurrentAuthor,
  getStoredToken,
  loginAuthor,
  persistToken,
  registerAuthor,
} from "../api/auth";
import type { AuthUser } from "../client/types.gen";

type AuthContextValue = {
  isBootstrapping: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (name: string, email: string, password: string) => Promise<void>;
  user: AuthUser | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setIsBootstrapping(false);
      return;
    }

    void fetchCurrentAuthor()
      .then(setUser)
      .catch(() => {
        clearStoredToken();
        setUser(null);
      })
      .finally(() => {
        setIsBootstrapping(false);
      });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isBootstrapping,
      async login(email, password) {
        const session = await loginAuthor({ email, password });
        persistToken(session.access_token);
        setUser(session.user);
      },
      logout() {
        clearStoredToken();
        setUser(null);
        void queryClient.cancelQueries();
        queryClient.removeQueries();
      },
      async register(name, email, password) {
        const session = await registerAuthor({ name, email, password });
        persistToken(session.access_token);
        setUser(session.user);
      },
      user,
    }),
    [isBootstrapping, queryClient, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
