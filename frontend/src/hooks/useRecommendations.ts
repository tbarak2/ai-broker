import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { aiApi } from "../services/api";

export function useRecommendations(params?: {
  portfolio_id?: number;
  status?: string;
  provider?: string;
}) {
  return useQuery({
    queryKey: ["recommendations", params],
    queryFn: () => aiApi.listRecommendations(params).then((r) => r.data.results),
    refetchInterval: 30_000,
  });
}

export function useApproveRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => aiApi.approve(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recommendations"] });
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
}

export function useRejectRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => aiApi.reject(id).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations"] }),
  });
}

export function useRunAnalysis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (portfolioId: number) => aiApi.runAnalysis(portfolioId),
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ["recommendations"] });
      }, 3000);
    },
  });
}

export function useStrategy(portfolioId: number | null) {
  return useQuery({
    queryKey: ["strategy", portfolioId],
    queryFn: () =>
      aiApi.getStrategy(portfolioId!).then((r) => r.data.results[0] ?? null),
    enabled: portfolioId != null,
  });
}
