import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authApi } from "../../services/api";
import { useAppStore } from "../../store";

export default function TotpVerify() {
  const navigate = useNavigate();
  const location = useLocation();
  const setTokens = useAppStore((s) => s.setTokens);

  const partialToken: string = location.state?.partialToken ?? "";

  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!partialToken) {
    navigate("/login");
    return null;
  }

  const verify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.totpVerify(partialToken, code);
      setTokens(data.access, data.refresh, data.user);
      navigate("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Invalid code. Try again.";
      setError(msg);
      setCode("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="text-4xl font-bold text-white mb-1">AI Broker</div>
          <p className="text-gray-400 text-sm">Two-factor authentication</p>
        </div>

        <form
          onSubmit={verify}
          className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-5"
        >
          <div className="space-y-2">
            <p className="text-sm text-white font-medium">Enter your authenticator code</p>
            <p className="text-xs text-gray-400">
              Open Google Authenticator and enter the 6-digit code for AI Broker.
            </p>
          </div>

          <input
            required
            autoFocus
            type="text"
            inputMode="numeric"
            maxLength={6}
            pattern="\d{6}"
            placeholder="000000"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest font-mono focus:outline-none focus:border-brand-500"
          />

          {error && (
            <p className="text-red-400 text-sm bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || code.length !== 6}
            className="w-full btn-primary py-3 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Verifying…" : "Verify"}
          </button>

          <button
            type="button"
            onClick={() => navigate("/login")}
            className="w-full text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Back to login
          </button>
        </form>
      </div>
    </div>
  );
}
