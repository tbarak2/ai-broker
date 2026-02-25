import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useAppStore } from "../../store";
import { usePortfolio, usePositions } from "../../hooks/usePortfolio";
import LoadingSpinner from "../../components/LoadingSpinner";
import clsx from "clsx";

const PIE_COLORS = [
  "#0ea5e9", "#6366f1", "#10b981", "#f59e0b",
  "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6",
];

function fmt(n: number | string, d = 2) {
  const num = typeof n === "string" ? parseFloat(n) : n;
  return num.toLocaleString("en-US", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

export default function Portfolio() {
  const portfolioId = useAppStore((s) => s.selectedPortfolioId);
  const { data: portfolio, isLoading: loadingPortfolio } = usePortfolio(portfolioId);
  const { data: positions, isLoading: loadingPositions } = usePositions(portfolioId);

  if (!portfolioId) {
    return (
      <div className="p-8 text-center text-gray-400">
        No portfolio selected. Go to Settings to create one.
      </div>
    );
  }

  if (loadingPortfolio || loadingPositions) return <LoadingSpinner />;

  const pieData =
    positions?.map((p) => ({
      name: p.symbol,
      value: parseFloat(p.market_value),
    })) ?? [];

  // Add cash as a slice
  if (portfolio) {
    pieData.push({
      name: "CASH",
      value: parseFloat(portfolio.cash_balance),
    });
  }

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold text-white">Portfolio</h1>

      {/* Summary row */}
      {portfolio && (
        <div className="grid grid-cols-3 gap-4">
          {[
            ["Total Value", `$${fmt(portfolio.total_value)}`],
            ["Cash Balance", `$${fmt(portfolio.cash_balance)}`],
            [
              "Total P&L",
              `${parseFloat(portfolio.total_pnl) >= 0 ? "+" : ""}$${fmt(portfolio.total_pnl)}`,
            ],
          ].map(([k, v]) => (
            <div key={k} className="card text-center">
              <p className="text-gray-400 text-sm">{k}</p>
              <p className="text-white text-xl font-bold mt-1">{v}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Positions table */}
        <div className="lg:col-span-2 card overflow-hidden p-0">
          <div className="px-6 py-4 border-b border-gray-800">
            <h2 className="text-base font-semibold text-white">
              Positions ({positions?.length ?? 0})
            </h2>
          </div>
          {!positions?.length ? (
            <p className="p-6 text-gray-500 text-sm">No open positions</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase">
                  {["Symbol", "Qty", "Avg Cost", "Price", "Mkt Value", "P&L", "Weight"].map(
                    (h) => (
                      <th key={h} className="px-6 py-3 text-left font-medium">
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {positions.map((pos) => {
                  const pnl = parseFloat(pos.unrealized_pnl);
                  return (
                    <tr key={pos.id} className="hover:bg-gray-800/50 transition-colors">
                      <td className="px-6 py-3 font-semibold text-white">
                        {pos.symbol}
                        <span className="ml-2 text-gray-500 font-normal text-xs">
                          {pos.asset_type}
                        </span>
                      </td>
                      <td className="px-6 py-3">{pos.quantity}</td>
                      <td className="px-6 py-3">${fmt(pos.avg_cost_price)}</td>
                      <td className="px-6 py-3">${fmt(pos.current_price)}</td>
                      <td className="px-6 py-3">${fmt(pos.market_value)}</td>
                      <td
                        className={clsx("px-6 py-3 font-medium", {
                          "text-green-400": pnl >= 0,
                          "text-red-400": pnl < 0,
                        })}
                      >
                        {pnl >= 0 ? "+" : ""}${fmt(pnl)}
                        <span className="ml-1 text-xs opacity-70">
                          ({pos.unrealized_pnl_pct >= 0 ? "+" : ""}
                          {pos.unrealized_pnl_pct.toFixed(1)}%)
                        </span>
                      </td>
                      <td className="px-6 py-3 text-gray-400">
                        {pos.weight_pct.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Allocation pie */}
        {pieData.length > 0 && (
          <div className="card">
            <h2 className="text-base font-semibold text-white mb-4">
              Allocation
            </h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="value"
                >
                  {pieData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={PIE_COLORS[i % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v: number) => [`$${fmt(v)}`, ""]}
                  contentStyle={{
                    backgroundColor: "#111827",
                    border: "1px solid #374151",
                    borderRadius: 8,
                  }}
                />
                <Legend
                  formatter={(v) => (
                    <span style={{ color: "#9CA3AF", fontSize: 11 }}>{v}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
