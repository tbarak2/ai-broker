import { useState } from "react";
import { useAppStore } from "../../store";
import {
  useRecommendations,
  useApproveRecommendation,
  useRejectRecommendation,
  useRunAnalysis,
} from "../../hooks/useRecommendations";
import type { AIRecommendation } from "../../services/api";
import LoadingSpinner from "../../components/LoadingSpinner";
import clsx from "clsx";
import { formatDistanceToNow } from "date-fns";

const ACTION_COLORS = {
  BUY: "badge-green",
  SELL: "badge-red",
  HOLD: "badge-yellow",
  REBALANCE: "badge-blue",
};

const STATUS_COLORS: Record<string, string> = {
  PENDING: "badge-yellow",
  APPROVED: "badge-blue",
  EXECUTED: "badge-green",
  REJECTED: "badge-red",
  EXPIRED: "badge-gray",
};

const PROVIDER_ICONS: Record<string, string> = {
  CLAUDE: "🟣",
  OPENAI: "🟢",
  GEMINI: "🔵",
};

function RecommendationCard({
  rec,
  onApprove,
  onReject,
  approving,
  rejecting,
}: {
  rec: AIRecommendation;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  approving: boolean;
  rejecting: boolean;
}) {
  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span>{PROVIDER_ICONS[rec.provider] ?? "🤖"}</span>
          <span className="font-semibold text-white">{rec.provider}</span>
          <span className={ACTION_COLORS[rec.action]}>{rec.action}</span>
          <span className="text-lg font-bold text-white">{rec.symbol}</span>
        </div>
        <span className={STATUS_COLORS[rec.status] ?? "badge-gray"}>
          {rec.status}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div>
          <p className="text-gray-400 text-xs">Confidence</p>
          <p className="text-white font-medium">{rec.confidence_pct}%</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Qty Suggested</p>
          <p className="text-white font-medium">{rec.quantity_suggested}</p>
        </div>
        {rec.price_target && (
          <div>
            <p className="text-gray-400 text-xs">Target</p>
            <p className="text-green-400 font-medium">${rec.price_target}</p>
          </div>
        )}
        {rec.stop_loss && (
          <div>
            <p className="text-gray-400 text-xs">Stop-loss</p>
            <p className="text-red-400 font-medium">${rec.stop_loss}</p>
          </div>
        )}
      </div>

      <p className="text-gray-300 text-sm leading-relaxed">{rec.reasoning}</p>

      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-gray-500">
          {formatDistanceToNow(new Date(rec.created_at), { addSuffix: true })}
        </span>
        {rec.status === "PENDING" && (
          <div className="flex gap-2">
            <button
              onClick={() => onReject(rec.id)}
              disabled={rejecting}
              className="btn-danger text-xs px-3 py-1.5"
            >
              Reject
            </button>
            <button
              onClick={() => onApprove(rec.id)}
              disabled={approving}
              className="btn-primary text-xs px-3 py-1.5"
            >
              {approving ? "Approving..." : "Approve"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AIAdvisor() {
  const portfolioId = useAppStore((s) => s.selectedPortfolioId);
  const [statusFilter, setStatusFilter] = useState<string>("PENDING");
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [rejectingId, setRejectingId] = useState<number | null>(null);

  const { data: recs, isLoading } = useRecommendations({
    portfolio_id: portfolioId ?? undefined,
    status: statusFilter || undefined,
  });

  const approve = useApproveRecommendation();
  const reject = useRejectRecommendation();
  const runAnalysis = useRunAnalysis();

  const handleApprove = async (id: number) => {
    setApprovingId(id);
    try {
      await approve.mutateAsync(id);
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (id: number) => {
    setRejectingId(id);
    try {
      await reject.mutateAsync(id);
    } finally {
      setRejectingId(null);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Advisor</h1>
          <p className="text-gray-400 text-sm mt-1">
            Multi-model AI recommendations — you approve before execution
          </p>
        </div>
        <button
          onClick={() => portfolioId && runAnalysis.mutate(portfolioId)}
          disabled={!portfolioId || runAnalysis.isPending}
          className="btn-primary"
        >
          {runAnalysis.isPending ? "Running..." : "▶ Run Analysis"}
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {["PENDING", "APPROVED", "EXECUTED", "REJECTED", "EXPIRED", ""].map((s) => (
          <button
            key={s || "ALL"}
            onClick={() => setStatusFilter(s)}
            className={clsx("px-3 py-1.5 rounded-lg text-sm font-medium transition-colors", {
              "bg-brand-600 text-white": statusFilter === s,
              "bg-gray-800 text-gray-400 hover:text-white": statusFilter !== s,
            })}
          >
            {s || "All"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : !recs?.length ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-4xl mb-3">🤖</p>
          <p>No recommendations found.</p>
          {portfolioId && (
            <button
              onClick={() => runAnalysis.mutate(portfolioId)}
              className="btn-primary mt-4"
            >
              Run AI Analysis
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {recs.map((rec) => (
            <RecommendationCard
              key={rec.id}
              rec={rec}
              onApprove={handleApprove}
              onReject={handleReject}
              approving={approvingId === rec.id}
              rejecting={rejectingId === rec.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
