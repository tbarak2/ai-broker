import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { portfolioApi } from "../services/api";
import { useAppStore } from "../store";

export function usePortfolios() {
  return useQuery({
    queryKey: ["portfolios"],
    queryFn: () => portfolioApi.list().then((r) => r.data.results),
  });
}

export function usePortfolio(id: number | null) {
  return useQuery({
    queryKey: ["portfolio", id],
    queryFn: () => portfolioApi.get(id!).then((r) => r.data),
    enabled: id != null,
  });
}

export function usePositions(portfolioId: number | null) {
  return useQuery({
    queryKey: ["positions", portfolioId],
    queryFn: () => portfolioApi.positions(portfolioId!).then((r) => r.data),
    enabled: portfolioId != null,
    refetchInterval: 60_000,
  });
}

export function usePnlHistory(portfolioId: number | null, period = "30d") {
  return useQuery({
    queryKey: ["pnl", portfolioId, period],
    queryFn: () => portfolioApi.pnl(portfolioId!, period).then((r) => r.data.data),
    enabled: portfolioId != null,
  });
}

export function useMetrics(portfolioId: number | null) {
  return useQuery({
    queryKey: ["metrics", portfolioId],
    queryFn: () => portfolioApi.metrics(portfolioId!).then((r) => r.data),
    enabled: portfolioId != null,
    refetchInterval: 120_000,
  });
}

export function useCreatePortfolio() {
  const qc = useQueryClient();
  const setSelectedPortfolioId = useAppStore((s) => s.setSelectedPortfolioId);
  return useMutation({
    mutationFn: (data: { name: string; initial_capital: string }) =>
      portfolioApi.create(data).then((r) => r.data),
    onSuccess: (portfolio) => {
      qc.invalidateQueries({ queryKey: ["portfolios"] });
      setSelectedPortfolioId(portfolio.id);
    },
  });
}
