import { useState } from "react";
import { useAppStore } from "../../store";
import { useTrades, useOrders, useCreateOrder, useApproveOrder } from "../../hooks/useTrades";
import LoadingSpinner from "../../components/LoadingSpinner";
import clsx from "clsx";
import { format } from "date-fns";

const ORDER_STATUS_COLORS: Record<string, string> = {
  PENDING_APPROVAL: "badge-yellow",
  APPROVED: "badge-blue",
  EXECUTED: "badge-green",
  REJECTED: "badge-red",
  CANCELLED: "badge-gray",
  FAILED: "badge-red",
};

function fmt(n: number | string, d = 2) {
  const num = typeof n === "string" ? parseFloat(n) : n;
  return num.toLocaleString("en-US", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

function NewOrderForm({
  portfolioId,
  onClose,
}: {
  portfolioId: number;
  onClose: () => void;
}) {
  const [form, setForm] = useState({
    symbol: "",
    side: "BUY",
    quantity: "",
    order_type: "MARKET",
    asset_type: "STOCK",
  });
  const createOrder = useCreateOrder();
  const approveOrder = useApproveOrder();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const order = await createOrder.mutateAsync({
      portfolio_id: portfolioId,
      symbol: form.symbol.toUpperCase(),
      side: form.side,
      quantity: form.quantity,
      order_type: form.order_type,
      asset_type: form.asset_type,
    });
    // Auto-approve manual orders
    await approveOrder.mutateAsync(order.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="card w-full max-w-md space-y-4">
        <h2 className="text-lg font-semibold text-white">New Manual Order</h2>
        <form onSubmit={handleSubmit} className="space-y-3">
          {[
            { label: "Symbol", key: "symbol", placeholder: "AAPL" },
            { label: "Quantity", key: "quantity", placeholder: "10", type: "number" },
          ].map(({ label, key, placeholder, type }) => (
            <div key={key}>
              <label className="text-sm text-gray-400 block mb-1">{label}</label>
              <input
                type={type ?? "text"}
                required
                placeholder={placeholder}
                value={(form as Record<string, string>)[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>
          ))}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-400 block mb-1">Side</label>
              <select
                value={form.side}
                onChange={(e) => setForm({ ...form, side: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
              >
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Type</label>
              <select
                value={form.order_type}
                onChange={(e) => setForm({ ...form, order_type: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
              >
                <option value="MARKET">MARKET</option>
                <option value="LIMIT">LIMIT</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createOrder.isPending || approveOrder.isPending}
              className="btn-primary flex-1"
            >
              {createOrder.isPending ? "Placing..." : "Place Order"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Trades() {
  const portfolioId = useAppStore((s) => s.selectedPortfolioId);
  const [view, setView] = useState<"trades" | "orders">("trades");
  const [showForm, setShowForm] = useState(false);

  const { data: trades, isLoading: loadingTrades } = useTrades(portfolioId ?? undefined);
  const { data: orders, isLoading: loadingOrders } = useOrders(
    portfolioId ? { portfolio_id: portfolioId } : undefined
  );

  const isLoading = view === "trades" ? loadingTrades : loadingOrders;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Trades & Orders</h1>
        {portfolioId && (
          <button onClick={() => setShowForm(true)} className="btn-primary">
            + New Order
          </button>
        )}
      </div>

      {/* Tab switch */}
      <div className="flex gap-2">
        {(["trades", "orders"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setView(t)}
            className={clsx("px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors", {
              "bg-brand-600 text-white": view === t,
              "bg-gray-800 text-gray-400 hover:text-white": view !== t,
            })}
          >
            {t}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : view === "trades" ? (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase">
                {["Symbol", "Side", "Qty", "Price", "Total", "Date"].map((h) => (
                  <th key={h} className="px-6 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {!trades?.length ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No trades yet
                  </td>
                </tr>
              ) : (
                trades.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-6 py-3 font-semibold text-white">{t.symbol}</td>
                    <td className="px-6 py-3">
                      <span className={t.side === "BUY" ? "badge-green" : "badge-red"}>
                        {t.side}
                      </span>
                    </td>
                    <td className="px-6 py-3">{t.quantity}</td>
                    <td className="px-6 py-3">${fmt(t.price)}</td>
                    <td className="px-6 py-3">${fmt(t.total_value)}</td>
                    <td className="px-6 py-3 text-gray-400">
                      {format(new Date(t.executed_at), "MMM d, HH:mm")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase">
                {["#", "Symbol", "Side", "Qty", "Status", "Source", "Created"].map((h) => (
                  <th key={h} className="px-6 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {!orders?.length ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                    No orders yet
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-6 py-3 text-gray-400">#{o.id}</td>
                    <td className="px-6 py-3 font-semibold text-white">{o.symbol}</td>
                    <td className="px-6 py-3">
                      <span className={o.side === "BUY" ? "badge-green" : "badge-red"}>
                        {o.side}
                      </span>
                    </td>
                    <td className="px-6 py-3">{o.quantity}</td>
                    <td className="px-6 py-3">
                      <span className={ORDER_STATUS_COLORS[o.status] ?? "badge-gray"}>
                        {o.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-400 text-xs">{o.source}</td>
                    <td className="px-6 py-3 text-gray-400">
                      {format(new Date(o.created_at), "MMM d, HH:mm")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && portfolioId && (
        <NewOrderForm portfolioId={portfolioId} onClose={() => setShowForm(false)} />
      )}
    </div>
  );
}
