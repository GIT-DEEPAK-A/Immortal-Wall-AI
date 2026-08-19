import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

/**
 * MLStatusPanel — compact ML model status card.
 *
 * Fetches GET /api/ml/status on mount and every 60 s.
 * Displays: model version, trained-at, F1, drift badge,
 * recent threat rate, and top-5 feature importances as bars.
 *
 * Props:
 *   apiClient  {AxiosInstance|null}  authenticated axios instance from App
 */
const MLStatusPanel = ({ apiClient }) => {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const fetchStatus = async () => {
    if (!apiClient) return;
    try {
      const res = await apiClient.get("/api/ml/status");
      setData(res.data);
      setError(null);
    } catch (err) {
      setError("Unable to fetch ML status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60_000);
    return () => clearInterval(interval);
  }, [apiClient]);

  /* ── Helpers ──────────────────────────────────────────────────── */
  const fmtDate = (iso) => {
    if (!iso || iso === "unknown") return "—";
    try { return new Date(iso).toLocaleString(); }
    catch { return iso; }
  };

  const top5 = data?.feature_importances
    ? Object.entries(data.feature_importances)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
    : [];

  const maxImp = top5.length > 0 ? top5[0][1] : 1;

  /* ── Render ─────────────────────────────────────────────────────── */
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-dark-surface border border-white/[0.08] rounded-2xl p-5 w-full"
      style={{ background: "rgba(255,255,255,0.03)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gold font-orbitron font-bold text-sm tracking-wider uppercase">
          ML Engine Status
        </h3>
        {data && (
          <span className="text-[10px] font-mono text-white/30">
            v{data.model_version ?? "—"}
          </span>
        )}
      </div>

      {/* Drift banner */}
      {data?.drift_detected && (
        <motion.div
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.2, repeat: Infinity }}
          className="flex items-center gap-2 bg-red-500/15 border border-red-500/40
                     rounded-xl px-4 py-2 mb-4"
        >
          <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0 animate-pulse" />
          <span className="text-red-400 font-bold text-xs tracking-widest uppercase">
            Model Drift Detected
          </span>
        </motion.div>
      )}

      {loading && (
        <p className="text-white/30 text-xs text-center py-6">Loading ML status…</p>
      )}

      {error && !loading && (
        <p className="text-red-400/70 text-xs text-center py-4">{error}</p>
      )}

      {data && !loading && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
          {/* Trained At */}
          <div>
            <p className="text-[10px] text-white/30 uppercase tracking-widest mb-1">Trained At</p>
            <p className="text-xs text-text-primary font-mono">{fmtDate(data.trained_at)}</p>
          </div>

          {/* F1 Score */}
          <div>
            <p className="text-[10px] text-white/30 uppercase tracking-widest mb-1">CV F1 Macro</p>
            <p className={`text-lg font-bold font-orbitron ${
              data.f1_macro >= 0.9 ? "text-green-400"
              : data.f1_macro >= 0.85 ? "text-gold"
              : "text-red-400"
            }`}>
              {data.f1_macro !== undefined ? (data.f1_macro * 100).toFixed(1) + "%" : "—"}
            </p>
          </div>

          {/* Drift badge */}
          <div>
            <p className="text-[10px] text-white/30 uppercase tracking-widest mb-1">Drift</p>
            <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
              data.drift_detected
                ? "bg-red-500/15 text-red-400 border border-red-500/30"
                : "bg-green-500/15 text-green-400 border border-green-500/30"
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                data.drift_detected ? "bg-red-400 animate-pulse" : "bg-green-400"
              }`} />
              {data.drift_detected ? "Detected" : "Stable"}
            </span>
          </div>

          {/* Recent threat rate */}
          <div>
            <p className="text-[10px] text-white/30 uppercase tracking-widest mb-1">Threat Rate</p>
            <p className={`text-lg font-bold font-orbitron ${
              data.recent_threat_rate > 0.5 ? "text-red-400"
              : data.recent_threat_rate > 0.2 ? "text-amber-400"
              : "text-green-400"
            }`}>
              {data.recent_threat_rate !== undefined
                ? (data.recent_threat_rate * 100).toFixed(1) + "%"
                : "—"}
            </p>
          </div>
        </div>
      )}

      {/* Top 5 feature importances */}
      {top5.length > 0 && (
        <div>
          <p className="text-[10px] text-white/30 uppercase tracking-widest mb-3">
            Top Feature Importances
          </p>
          <div className="space-y-2">
            {top5.map(([feat, imp]) => (
              <div key={feat}>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-white/60 font-mono">{feat}</span>
                  <span className="text-gold/80">{(imp * 100).toFixed(1)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(imp / maxImp) * 100}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="h-full rounded-full bg-gradient-to-r from-gold/70 to-gold"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default MLStatusPanel;
