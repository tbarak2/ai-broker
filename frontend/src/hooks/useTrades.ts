import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tradingApi } from "../services/api";

export function useOrders(params?: { portfolio_id?: number; status?: string }) {
  return useQuery({
    queryKey: ["orders", params],
    queryFn: () => tradingApi.listOrders(params).then((r) => r.data.results),
    refetchInterval: 10_000,
  });
}

export function useTrades(portfolioId?: number) {
  return useQuery({
    queryKey: ["trades", portfolioId],
    queryFn: () =>
      tradingApi.listTrades(portfolioId ? { portfolio_id: portfolioId } : {}).then(
        (r) => r.data.results
      ),
    refetchInterval: 30_000,
  });
}

export function useCreateOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof tradingApi.createOrder>[0]) =>
      tradingApi.createOrder(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useApproveOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tradingApi.approveOrder(id).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["trades"] });
      qc.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}

export function useRejectOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) =>
      tradingApi.rejectOrder(id, reason).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }),
  });
}
