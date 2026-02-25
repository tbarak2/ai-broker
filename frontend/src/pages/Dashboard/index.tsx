import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useAppStore } from "../../store";
import { usePortfolio, usePnlHistory, useMetrics } from "../../hooks/usePortfolio";
import { useRecommendations } from "../../hooks/useRecommendations";
import { useTrades } from "../../hooks/useTrades";
import StatCard from "../../components/StatCard";
import LoadingSpinner from "../../components/LoadingSpinner";
import { format } from "date-fns";

function fmt(n: number | string | undefined, decimals = 2) {
  const num = typeof n === "string" ? parseFloat(n) : (n ?? 0);
  return num.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function Dashboard() {
  const portfolioId = useAppStore((s) => s.selectedPortfolioId);
  const { data: portfolio, isLoading } = usePortfolio(portfolioId);
  const { data: pnlData } = usePnlHistory(portfolioId, "30d");
  const { data: metrics } = useMetrics(portfolioId);
  const { data: pendingRecs } = useRecommendations({
    portfolio_id: portfolioId ?? undefined,
    status: "PENDING",
  });
  const { data: recentTrades } = useTrades(portfolioId ?? undefined);

  if (!portfolioId) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-400 mb-4">No portfolio selected.</p>
        <p className="text-sm text-gray-500">
          Go to <strong>Settings</strong> to create your first portfolio.
        </p>
      </div>
    );
  }

  if (isLoading) return <LoadingSpinner text="Loading portfolio..." />;
  if (!portfolio) return null;

  const pnlNum = parseFloat(portfolio.total_pnl);
  const pnlPct = portfolio.total_pnl_pct;

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">{portfolio.name}</h1>
        <p className="text-gray-400 text-sm mt-1">Paper trading dashboard</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Value"
          value={`$${fmt(portfolio.total_value)}`}
          sub="Portfolio market value"
        />
        <StatCard
          label="Cash Balance"
          value={`$${fmt(portfolio.cash_balance)}`}
          sub="Available to invest"
        />
        <StatCard
          label="Total P&L"
          value={`$${pnlNum >= 0 ? "+" : ""}${fmt(pnlNum)}`}
          sub={`${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(2)}% all time`}
          trend={pnlNum >= 0 ? "up" : "down"}
        />
        <StatCard
          label="Open Positions"
          value={String(portfolio.positions_count)}
          sub={`${pendingRecs?.length ?? 0} pending AI recs`}
        />
      </div>

      {/* P&L chart */}
      {pnlData && pnlData.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-4">
            Portfolio Value — Last 30 Days
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={pnlData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                tick={{ fill: "#9CA3AF", fontSize: 11 }}
                tickFormatter={(v) => v.slice(5)}
              />
              <YAxis
                tick={{ fill: "#9CA3AF", fontSize: 11 }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                width={56}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  color: "#fff",
                }}
                formatter={(v: number) => [`$${fmt(v)}`, "Value"]}
              />
              <Line
                type="monotone"
                dataKey="portfolio_value"
                stroke="#0ea5e9"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Metrics */}
        {metrics && (
          <div className="card">
            <h2 className="text-base font-semibold text-white mb-3">
              Performance Metrics
            </h2>
            <dl className="space-y-2 text-sm">
              {[
                ["Win Rate", `${fmt(metrics.win_rate_pct, 1)}%`],
                ["Sharpe Ratio", fmt(metrics.sharpe_ratio, 2)],
                ["Max Drawdown", `-${fmt(metrics.max_drawdown_pct, 1)}%`],
                ["Total Trades", String(metrics.total_trades ?? 0)],
                ["Best Trade", `$${fmt(metrics.best_trade_pnl)}`],
                ["Worst Trade", `$${fmt(metrics.worst_trade_pnl)}`],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <dt className="text-gray-400">{k}</dt>
                  <dd className="text-white font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* Recent trades */}
        <div className="card">
          <h2 className="text-base font-semibold text-white mb-3">
            Recent Trades
          </h2>
          {!recentTrades?.length ? (
            <p className="text-gray-500 text-sm">No trades yet</p>
          ) : (
            <div className="space-y-2">
              {recentTrades.slice(0, 6).map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={
                        t.side === "BUY" ? "badge-green" : "badge-red"
                      }
                    >
                      {t.side}
                    </span>
                    <span className="font-medium">{t.symbol}</span>
                    <span className="text-gray-400">×{t.quantity}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-white">${fmt(t.price)}</span>
                    <span className="text-gray-500 ml-2 text-xs">
                      {format(new Date(t.executed_at), "MMM d")}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
