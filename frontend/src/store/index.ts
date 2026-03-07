import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthUser {
  id: number;
  username: string;
  email: string;
}

interface AppState {
  // Portfolio selection
  selectedPortfolioId: number | null;
  setSelectedPortfolioId: (id: number) => void;

  // Auth
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  setTokens: (access: string, refresh: string, user: AuthUser) => void;
  clearAuth: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedPortfolioId: null,
      setSelectedPortfolioId: (id) => set({ selectedPortfolioId: id }),

      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (access, refresh, user) =>
        set({ accessToken: access, refreshToken: refresh, user }),
      clearAuth: () =>
        set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: "ai-broker-store" }
  )
);
