import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";

const API_BASE = "http://localhost:8000/api/auth";

/* ── Numpad layout ───────────────────────────────────────────── */
const PAD_KEYS = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["CLR", "0", "⌫"],
];

/* ── Single digit display box ────────────────────────────────── */
const DigitBox = ({ filled, active, success }) => (
  <motion.div
    animate={
      success
        ? { scale: [1, 1.15, 1], borderColor: ["#D4AF37", "#4ade80", "#4ade80"] }
        : active
        ? { scale: [1, 1.06, 1] }
        : { scale: 1 }
    }
    transition={{
      duration: success ? 0.4 : 0.5,
      repeat: active && !success ? Infinity : 0,
      repeatDelay: 0.8,
    }}
    className={`
      w-11 h-13 rounded-xl flex items-center justify-center
      border-2 transition-colors duration-200 select-none
      ${success
        ? "border-green-400 bg-green-400/10 shadow-lg shadow-green-400/30"
        : filled
        ? "border-gold bg-gold/10 shadow-md shadow-gold/20"
        : active
        ? "border-gold/60 bg-white/[0.04]"
        : "border-white/10 bg-white/[0.02]"}
    `}
    style={{ height: "3.25rem" }}
  >
    {filled ? (
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className={`w-2.5 h-2.5 rounded-full ${success ? "bg-green-400" : "bg-gold"}`}
      />
    ) : null}
  </motion.div>
);

/* ── Individual numpad button ─────────────────────────────────── */
const PadButton = ({ label, onClick, disabled, isAction }) => {
  const [pressed, setPressed] = useState(false);

  const handlePress = () => {
    if (disabled) return;
    setPressed(true);
    setTimeout(() => setPressed(false), 150);
    onClick(label);
  };

  if (label === "CLR") {
    return (
      <motion.button
        onClick={handlePress}
        disabled={disabled}
        whileTap={{ scale: 0.9 }}
        className={`
          h-14 rounded-2xl flex items-center justify-center text-xs font-bold tracking-widest uppercase
          transition-all duration-150 select-none
          ${pressed ? "bg-red-500/30 border-red-400/60" : "bg-red-500/10 border-red-400/20"}
          border text-red-400 hover:bg-red-500/20 hover:border-red-400/40
          disabled:opacity-30 disabled:cursor-not-allowed
        `}
      >
        CLR
      </motion.button>
    );
  }

  if (label === "⌫") {
    return (
      <motion.button
        onClick={handlePress}
        disabled={disabled}
        whileTap={{ scale: 0.9 }}
        className={`
          h-14 rounded-2xl flex items-center justify-center text-lg
          transition-all duration-150 select-none
          ${pressed ? "bg-white/15 border-white/30" : "bg-white/[0.04] border-white/10"}
          border text-text-secondary hover:bg-white/10 hover:text-text-primary
          disabled:opacity-30 disabled:cursor-not-allowed
        `}
      >
        ⌫
      </motion.button>
    );
  }

  return (
    <motion.button
      onClick={handlePress}
      disabled={disabled}
      whileTap={{ scale: 0.88 }}
      className={`
        h-14 rounded-2xl flex flex-col items-center justify-center gap-0.5
        transition-all duration-150 select-none font-orbitron font-bold text-xl
        ${pressed
          ? "bg-gold/25 border-gold/70 text-gold shadow-lg shadow-gold/30"
          : "bg-white/[0.04] border-white/10 text-text-primary hover:bg-gold/10 hover:border-gold/30 hover:text-gold"}
        border disabled:opacity-30 disabled:cursor-not-allowed
      `}
    >
      {label}
    </motion.button>
  );
};

/* ── Main LoginPage ───────────────────────────────────────────── */
const LoginPage = ({ onLogin }) => {
  const [passkey, setPasskey] = useState("");
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [shake,   setShake]   = useState(false);

  /* Physical keyboard support */
  const handleKeyDown = useCallback((e) => {
    if (loading || success) return;
    if (/^[0-9]$/.test(e.key)) {
      setPasskey((p) => (p.length < 6 ? p + e.key : p));
    } else if (e.key === "Backspace") {
      setPasskey((p) => p.slice(0, -1));
    } else if (e.key === "Escape") {
      setPasskey("");
      setError("");
    }
  }, [loading, success]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  /* Auto-submit at 6 digits */
  useEffect(() => {
    if (passkey.length === 6 && !loading && !success) {
      handleSubmit(passkey);
    }
  }, [passkey]);

  const handlePadPress = (key) => {
    if (loading || success) return;
    if (key === "CLR") {
      setPasskey("");
      setError("");
      return;
    }
    if (key === "⌫") {
      setPasskey((p) => p.slice(0, -1));
      return;
    }
    setPasskey((p) => (p.length < 6 ? p + key : p));
  };

  const handleSubmit = async (currentPasskey) => {
    const pk = currentPasskey ?? passkey;
    if (pk.length !== 6 || loading) return;
    setError("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/login`, { passkey: pk });
      if (res.data.success) {
        setSuccess(true);
        setTimeout(onLogin, 900);
      } else {
        triggerError("Invalid passkey. Try again.");
      }
    } catch {
      triggerError("Backend unreachable. Start the server first.");
    } finally {
      setLoading(false);
    }
  };

  const triggerError = (msg) => {
    setError(msg);
    setPasskey("");
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const disabled = loading || success;

  return (
    <div className="min-h-screen bg-[#050810] flex items-center justify-center relative overflow-hidden">

      {/* ── Hex-grid background ── */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.05] pointer-events-none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="lhex" width="56" height="100" patternUnits="userSpaceOnUse">
            <polygon points="28,2 54,16 54,44 28,58 2,44 2,16"   fill="none" stroke="#FFD700" strokeWidth="0.6"/>
            <polygon points="28,52 54,66 54,94 28,108 2,94 2,66"  fill="none" stroke="#FFD700" strokeWidth="0.6"/>
            <polygon points="56,26 82,40 82,68 56,82 30,68 30,40" fill="none" stroke="#FFD700" strokeWidth="0.6"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#lhex)"/>
      </svg>

      {/* Central glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                      w-[700px] h-[700px] rounded-full bg-gold/[0.04] blur-[140px] pointer-events-none" />

      {/* ── Card ── */}
      <motion.div
        initial={{ opacity: 0, y: 28, scale: 0.95 }}
        animate={{ opacity: 1, y: 0,  scale: 1 }}
        transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
        style={shake ? { animation: "shake 0.45s cubic-bezier(.36,.07,.19,.97)" } : {}}
        className="relative z-10 w-full max-w-sm mx-4"
      >
        {/* ── Logo ── */}
        <motion.div
          className="flex flex-col items-center mb-7"
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="relative mb-3">
            {/* Pulse rings */}
            {[1, 2].map((n) => (
              <motion.div
                key={n}
                className="absolute rounded-2xl border border-gold/20"
                style={{ inset: -n * 6 }}
                animate={{ scale: [1, 1.12 + n * 0.05], opacity: [0.4, 0] }}
                transition={{ duration: 2.5, repeat: Infinity, delay: n * 0.4 }}
              />
            ))}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold via-yellow-400 to-amber-500
                            flex items-center justify-center shadow-2xl shadow-gold/40 relative z-10">
              <svg viewBox="0 0 120 140" className="w-9 h-9">
                <path d="M60 4 L108 24 L108 68 C108 98 84 122 60 132 C36 122 12 98 12 68 L12 24 Z"
                      fill="rgba(0,0,0,0.6)"/>
                <g stroke="rgba(255,215,0,0.95)" strokeWidth="5" fill="none">
                  <line x1="60" y1="28" x2="60" y2="98"/>
                  <line x1="34" y1="54" x2="86" y2="54"/>
                  <circle cx="60" cy="54" r="11"/>
                </g>
              </svg>
            </div>
          </div>

          <h1 className="text-xl font-orbitron font-black tracking-widest text-transparent
                         bg-clip-text bg-gradient-to-r from-gold to-yellow-300">
            IMMORTAL WALL AI
          </h1>
          <p className="text-[10px] text-white/30 tracking-[0.45em] uppercase mt-1">
            Secure Access Portal
          </p>
        </motion.div>

        {/* ── Panel ── */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6
                     backdrop-blur-xl shadow-2xl shadow-black/70"
        >
          {/* Heading */}
          <div className="text-center mb-5">
            <p className="text-text-primary font-semibold text-sm tracking-wide mb-0.5">
              Enter System Passkey
            </p>
            <p className="text-white/25 text-[11px] font-mono tracking-widest">
              DEFAULT · · · 1 2 3 4 5 6
            </p>
          </div>

          {/* ── Digit display ── */}
          <div className="flex gap-2.5 justify-center mb-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <DigitBox
                key={i}
                filled={i < passkey.length}
                active={i === passkey.length && !disabled}
                success={success}
              />
            ))}
          </div>

          {/* ── Error ── */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.p
                key="err"
                initial={{ opacity: 0, y: -4, height: 0 }}
                animate={{ opacity: 1, y: 0,  height: "auto" }}
                exit={{   opacity: 0, y: -4, height: 0 }}
                className="text-red-400 text-[11px] text-center mb-3 px-3 py-2 rounded-lg
                           bg-red-500/10 border border-red-500/20"
              >
                {error}
              </motion.p>
            )}
            {success && (
              <motion.p
                key="ok"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-green-400 text-[11px] text-center mb-3 px-3 py-2 rounded-lg
                           bg-green-500/10 border border-green-500/20"
              >
                Access granted — entering system…
              </motion.p>
            )}
          </AnimatePresence>

          {/* ── Numpad ── */}
          <div className="grid grid-cols-3 gap-2.5 mb-5">
            {PAD_KEYS.flat().map((key) => (
              <PadButton
                key={key}
                label={key}
                onClick={handlePadPress}
                disabled={disabled || (key !== "CLR" && key !== "⌫" && passkey.length === 6)}
              />
            ))}
          </div>

          {/* ── Submit ── */}
          <motion.button
            whileHover={!disabled ? { scale: 1.02 } : {}}
            whileTap={!disabled ? { scale: 0.97 } : {}}
            onClick={() => handleSubmit(passkey)}
            disabled={passkey.length !== 6 || disabled}
            className="w-full py-3.5 rounded-xl font-orbitron font-bold text-sm tracking-widest uppercase
                       bg-gradient-to-r from-gold to-yellow-400 text-black
                       disabled:opacity-35 disabled:cursor-not-allowed
                       hover:shadow-lg hover:shadow-gold/30 transition-all duration-300"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <motion.span
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.75, repeat: Infinity, ease: "linear" }}
                  className="inline-block w-4 h-4 border-2 border-black/30 border-t-black rounded-full"
                />
                Verifying…
              </span>
            ) : success ? (
              "✓ Access Granted"
            ) : (
              "Access System →"
            )}
          </motion.button>

          <p className="text-center text-[9px] text-white/10 mt-4 font-mono tracking-[0.35em] uppercase">
            Authorised Personnel Only
          </p>
        </motion.div>

        {/* ── Bottom status bar ── */}
        <div className="flex justify-center gap-6 mt-5">
          {["FIREWALL", "AI ENGINE", "HONEYPOT"].map((lbl) => (
            <div key={lbl} className="flex items-center gap-1.5 text-[10px] text-white/20 font-mono">
              <span className="w-1 h-1 rounded-full bg-green-400/50 animate-pulse" />
              {lbl}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Shake keyframe */}
      <style>{`
        @keyframes shake {
          0%,100%{transform:translateX(0)}
          18%{transform:translateX(-10px)}
          36%{transform:translateX(10px)}
          54%{transform:translateX(-7px)}
          72%{transform:translateX(7px)}
          90%{transform:translateX(-3px)}
        }
      `}</style>
    </div>
  );
};

export default LoginPage;
