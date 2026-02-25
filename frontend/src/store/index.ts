import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppState {
  selectedPortfolioId: number | null;
  setSelectedPortfolioId: (id: number) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedPortfolioId: null,
      setSelectedPortfolioId: (id) => set({ selectedPortfolioId: id }),
    }),
    { name: "ai-broker-store" }
  )
);
