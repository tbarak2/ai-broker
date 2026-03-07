import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authApi } from "../../services/api";
import { useAppStore } from "../../store";

export default function TotpSetup() {
  const navigate = useNavigate();
  const location = useLocation();
  const setTokens = useAppStore((s) => s.setTokens);

  const partialToken: string = location.state?.partialToken ?? "";

  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchingQr, setFetchingQr] = useState(true);

  useEffect(() => {
    if (!partialToken) {
      navigate("/login");
      return;
    }
    authApi
      .totpSetup(partialToken)
      .then(({ data }) => {
        setQrCode(data.qr_code);
        setSecret(data.secret);
      })
      .catch(() => navigate("/login"))
      .finally(() => setFetchingQr(false));
  }, [partialToken, navigate]);

  const activate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authApi.totpActivate(partialToken, code);
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
          <p className="text-gray-400 text-sm">Set up two-factor authentication</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
          <div className="space-y-2">
            <p className="text-sm text-white font-medium">Step 1 — Scan QR code</p>
            <p className="text-xs text-gray-400">
              Open <strong>Google Authenticator</strong> (or any TOTP app) and scan the
              code below.
            </p>
          </div>

          {fetchingQr ? (
            <div className="h-48 flex items-center justify-center">
              <div className="text-gray-500 text-sm">Loading…</div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <img
                src={qrCode}
                alt="TOTP QR code"
                className="w-48 h-48 rounded-lg border border-gray-700"
              />
              <details className="w-full">
                <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-300">
                  Can't scan? Enter key manually
                </summary>
                <p className="mt-2 font-mono text-xs text-gray-300 bg-gray-800 rounded px-3 py-2 break-all">
                  {secret}
                </p>
              </details>
            </div>
          )}

          <form onSubmit={activate} className="space-y-4">
            <div className="space-y-1">
              <p className="text-sm text-white font-medium">Step 2 — Enter 6-digit code</p>
              <input
                required
                type="text"
                inputMode="numeric"
                maxLength={6}
                pattern="\d{6}"
                placeholder="000000"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-center text-2xl tracking-widest font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

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
              {loading ? "Verifying…" : "Activate & sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
