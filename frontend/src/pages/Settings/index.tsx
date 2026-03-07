import { useState } from "react";
import { useAppStore } from "../../store";
import { usePortfolios, useCreatePortfolio } from "../../hooks/usePortfolio";
import { useStrategy } from "../../hooks/useRecommendations";
import LoadingSpinner from "../../components/LoadingSpinner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { aiApi } from "../../services/api";

function WatchlistEditor({
  watchlist,
  onChange,
}: {
  watchlist: string[];
  onChange: (symbols: string[]) => void;
}) {
  const [input, setInput] = useState("");

  const add = () => {
    const sym = input.trim().toUpperCase();
    if (sym && !watchlist.includes(sym)) {
      onChange([...watchlist, sym]);
      setInput("");
    }
  };

  const remove = (sym: string) => onChange(watchlist.filter((s) => s !== sym));

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Add symbol (e.g. AAPL)"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
        />
        <button onClick={add} className="btn-primary">
          Add
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {watchlist.map((sym) => (
          <span
            key={sym}
            className="flex items-center gap-1 bg-gray-800 text-white px-2 py-1 rounded-lg text-sm"
          >
            {sym}
            <button
              onClick={() => remove(sym)}
              className="text-gray-400 hover:text-red-400 ml-1"
            >
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Settings() {
  const qc = useQueryClient();
  const portfolioId = useAppStore((s) => s.selectedPortfolioId);
  const setSelectedPortfolioId = useAppStore((s) => s.setSelectedPortfolioId);
  const { data: portfolios } = usePortfolios();
  const { data: strategy, isLoading: loadingStrategy } = useStrategy(portfolioId);

  const createPortfolio = useCreatePortfolio();
  const [newPortfolio, setNewPortfolio] = useState({ name: "", initial_capital: "10000" });

  const [strategyForm, setStrategyForm] = useState<{
    ai_providers: string[];
    risk_tolerance: string;
    max_position_size_pct: string;
    analysis_interval_minutes: number;
    watchlist: string[];
    auto_trade: boolean;
    auto_trade_min_confidence: string;
  } | null>(null);

  // Populate form when strategy loads
  if (strategy && !strategyForm) {
    setStrategyForm({
      ai_providers: strategy.ai_providers,
      risk_tolerance: strategy.risk_tolerance,
      max_position_size_pct: strategy.max_position_size_pct,
      analysis_interval_minutes: strategy.analysis_interval_minutes,
      watchlist: strategy.watchlist,
      auto_trade: strategy.auto_trade ?? false,
      auto_trade_min_confidence: strategy.auto_trade_min_confidence ?? "0.700",
    });
  }

  const saveStrategy = useMutation({
    mutationFn: () => {
      if (!strategyForm) throw new Error("No strategy form");
      if (strategy) {
        return aiApi.updateStrategy(strategy.id, strategyForm);
      } else if (portfolioId) {
        return aiApi.createStrategy({ ...strategyForm, portfolio: portfolioId });
      }
      throw new Error("No portfolio selected");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["strategy"] }),
  });

  const toggleProvider = (p: string) => {
    if (!strategyForm) return;
    const providers = strategyForm.ai_providers.includes(p)
      ? strategyForm.ai_providers.filter((x) => x !== p)
      : [...strategyForm.ai_providers, p];
    setStrategyForm({ ...strategyForm, ai_providers: providers });
  };

  return (
    <div className="p-8 space-y-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-white">Settings</h1>

      {/* Portfolio selector */}
      <section className="card space-y-4">
        <h2 className="text-base font-semibold text-white">Portfolio</h2>
        {portfolios && portfolios.length > 0 && (
          <div className="space-y-2">
            {portfolios.map((p) => (
              <label
                key={p.id}
                className="flex items-center gap-3 cursor-pointer group"
              >
                <input
                  type="radio"
                  name="portfolio"
                  checked={portfolioId === p.id}
                  onChange={() => setSelectedPortfolioId(p.id)}
                  className="accent-brand-500"
                />
                <span className="text-white group-hover:text-brand-400 transition-colors">
                  {p.name}
                </span>
                <span className="text-gray-400 text-sm">
                  ${parseFloat(p.total_value).toLocaleString()}
                </span>
              </label>
            ))}
          </div>
        )}
        <details className="group">
          <summary className="cursor-pointer text-sm text-gray-400 hover:text-white transition-colors">
            + Create new portfolio
          </summary>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createPortfolio.mutate(newPortfolio);
            }}
            className="mt-3 space-y-3"
          >
            <input
              required
              placeholder="Portfolio name"
              value={newPortfolio.name}
              onChange={(e) => setNewPortfolio({ ...newPortfolio, name: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            />
            <input
              required
              type="number"
              placeholder="Initial capital (USD)"
              value={newPortfolio.initial_capital}
              onChange={(e) =>
                setNewPortfolio({ ...newPortfolio, initial_capital: e.target.value })
              }
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            />
            <button
              type="submit"
              disabled={createPortfolio.isPending}
              className="btn-primary"
            >
              {createPortfolio.isPending ? "Creating..." : "Create Portfolio"}
            </button>
          </form>
        </details>
      </section>

      {/* Strategy config */}
      {portfolioId && (
        <section className="card space-y-5">
          <h2 className="text-base font-semibold text-white">AI Strategy</h2>
          {loadingStrategy ? (
            <LoadingSpinner />
          ) : strategyForm ? (
            <>
              {/* AI Providers */}
              <div>
                <p className="text-sm text-gray-400 mb-2">AI Providers</p>
                <div className="flex gap-3">
                  {["claude", "openai", "gemini"].map((p) => (
                    <label key={p} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={strategyForm.ai_providers.includes(p)}
                        onChange={() => toggleProvider(p)}
                        className="accent-brand-500"
                      />
                      <span className="text-white capitalize">{p}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Risk tolerance */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Risk Tolerance</p>
                <div className="flex gap-3">
                  {["LOW", "MEDIUM", "HIGH"].map((r) => (
                    <label key={r} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="risk"
                        checked={strategyForm.risk_tolerance === r}
                        onChange={() =>
                          setStrategyForm({ ...strategyForm, risk_tolerance: r })
                        }
                        className="accent-brand-500"
                      />
                      <span className="text-white capitalize">{r.toLowerCase()}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Max position size */}
              <div>
                <label className="text-sm text-gray-400 block mb-1">
                  Max Position Size (% of portfolio)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={strategyForm.max_position_size_pct}
                  onChange={(e) =>
                    setStrategyForm({ ...strategyForm, max_position_size_pct: e.target.value })
                  }
                  className="w-32 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Analysis interval */}
              <div>
                <label className="text-sm text-gray-400 block mb-1">
                  Analysis Interval (minutes)
                </label>
                <input
                  type="number"
                  min="5"
                  max="1440"
                  value={strategyForm.analysis_interval_minutes}
                  onChange={(e) =>
                    setStrategyForm({
                      ...strategyForm,
                      analysis_interval_minutes: parseInt(e.target.value),
                    })
                  }
                  className="w-32 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
                />
              </div>

              {/* Auto-trade */}
              <div className="border border-gray-700 rounded-xl p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">Auto Management</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      AI will execute trades automatically when confidence meets the threshold.
                      Use with caution.
                    </p>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={strategyForm.auto_trade}
                    onClick={() =>
                      setStrategyForm({ ...strategyForm, auto_trade: !strategyForm.auto_trade })
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                      strategyForm.auto_trade ? "bg-brand-500" : "bg-gray-600"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        strategyForm.auto_trade ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>

                {strategyForm.auto_trade && (
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">
                      Minimum confidence to auto-execute:{" "}
                      <span className="text-white font-medium">
                        {Math.round(parseFloat(strategyForm.auto_trade_min_confidence) * 100)}%
                      </span>
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="99"
                      step="1"
                      value={Math.round(parseFloat(strategyForm.auto_trade_min_confidence) * 100)}
                      onChange={(e) =>
                        setStrategyForm({
                          ...strategyForm,
                          auto_trade_min_confidence: (parseInt(e.target.value) / 100).toFixed(3),
                        })
                      }
                      className="w-full accent-brand-500"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>50% (permissive)</span>
                      <span>99% (strict)</span>
                    </div>
                    <p className="text-xs text-yellow-400 mt-2">
                      Warning: Auto management bypasses your manual review. Only enable if you trust
                      the AI strategy.
                    </p>
                  </div>
                )}
              </div>

              {/* Watchlist */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Watchlist</p>
                <WatchlistEditor
                  watchlist={strategyForm.watchlist}
                  onChange={(wl) => setStrategyForm({ ...strategyForm, watchlist: wl })}
                />
              </div>

              <button
                onClick={() => saveStrategy.mutate()}
                disabled={saveStrategy.isPending}
                className="btn-primary"
              >
                {saveStrategy.isPending ? "Saving..." : "Save Strategy"}
              </button>
              {saveStrategy.isSuccess && (
                <p className="text-green-400 text-sm">✓ Saved!</p>
              )}
            </>
          ) : (
            <div className="space-y-3">
              <p className="text-gray-400 text-sm">No strategy configured yet.</p>
              <button
                onClick={() =>
                  setStrategyForm({
                    ai_providers: ["claude"],
                    risk_tolerance: "MEDIUM",
                    max_position_size_pct: "10",
                    analysis_interval_minutes: 30,
                    watchlist: [],
                    auto_trade: false,
                    auto_trade_min_confidence: "0.700",
                  })
                }
                className="btn-primary"
              >
                Create Strategy
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
