// Auth context: loads persisted tokens, exposes login/logout and the current
// user. Keeps the API client token in sync via setToken/saveAuth/clearAuth.

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { api, setToken, type Me, type TokenResponse } from '../lib/api';
import { clearAuth, loadAuth, saveAuth } from '../lib/storage';

interface AuthState {
  loading: boolean;
  user: Me | null;
  accessToken: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, displayName?: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<Me | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { access } = await loadAuth();
        if (access) {
          setToken(access);
          setAccessToken(access);
          try {
            const me = await api.me();
            setUser(me);
          } catch {
            // Token stale/expired — leave user null; login screen will handle.
          }
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const applyTokens = useCallback(async (tokens: TokenResponse) => {
    setToken(tokens.access_token);
    setAccessToken(tokens.access_token);
    await saveAuth(tokens.access_token, tokens.refresh_token);
    const me = await api.me();
    setUser(me);
  }, []);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const tokens = await api.login(email, password);
      await applyTokens(tokens);
    },
    [applyTokens],
  );

  const signUp = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const tokens = await api.register(email, password, displayName);
      await applyTokens(tokens);
    },
    [applyTokens],
  );

  const signOut = useCallback(async () => {
    try {
      const { refresh } = await loadAuth();
      if (refresh) await api.logout(refresh);
    } catch {
      // best-effort revocation
    }
    setToken(null);
    setAccessToken(null);
    setUser(null);
    await clearAuth();
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await api.me();
    setUser(me);
  }, []);

  const value = useMemo(
    () => ({ loading, user, accessToken, signIn, signUp, signOut, refreshUser }),
    [loading, user, accessToken, signIn, signUp, signOut, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}