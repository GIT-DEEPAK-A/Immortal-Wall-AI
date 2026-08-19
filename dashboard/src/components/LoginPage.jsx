import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";

const API_BASE = "http://localhost:8000/api/auth";

/* ── Input field ─────────────────────────────────────────────── */
const Field = ({ label, id, type = "text", value, onChange, disabled, autoFocus, placeholder }) => (
  <div className="flex flex-col gap-1.5">
    <label htmlFor={id} className="text-[11px] font-mono tracking-widest uppercase text-white/40">
      {label}
    </label>
    <input
      id={id}
      type={type}
      value={value}
      onChange={onChange}
      disabled={disabled}
      autoFocus={autoFocus}
      autoComplete={type === "password" ? "current-password" : "email"}
      placeholder={placeholder}
      className="
        w-full px-4 py-3 rounded-xl
        bg-white/[0.04] border border-white/[0.10]
        text-text-primary text-sm placeholder:text-white/20
        focus:outline-none focus:border-gold/50 focus:bg-white/[0.07]
        disabled:opacity-40 disabled:cursor-not-allowed
        transition-colors duration-200
      "
    />
  </div>
);

/* ── Main LoginPage ───────────────────────────────────────────── */
const LoginPage = ({ onLogin }) => {
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [success,  setSuccess]  = useState(false);
  const [shake,    setShake]    = useState(false);
  const formRef = useRef(null);

  /* Submit on Enter anywhere in the form */
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Enter" && !loading && !success) handleSubmit();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [email, password, loading, success]);

  const handleSubmit = async () => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password || loading || success) return;

    setError("");
    setLoading(true);

    try {
      const res = await axios.post(
        `${API_BASE}/login`,
        { email: trimmedEmail, password },
        { validateStatus: () => true },   // handle all status codes ourselves
      );

      if (res.status === 200 && res.data?.access_token) {
        setSuccess(true);
        setTimeout(() => onLogin(res.data.access_token), 900);
      } else if (res.status === 401) {
        triggerError("Invalid email or password.");
      } else if (res.status === 422) {
        // Pydantic validation error — extract first message
        const detail = res.data?.detail;
        const msg = Array.isArray(detail)
          ? detail[0]?.msg ?? "Invalid input."
          : String(detail ?? "Invalid input.");
        triggerError(msg);
      } else {
        triggerError("Unexpected error. Please try again.");
      }
    } catch {
      triggerError("Backend unreachable. Start the server first.");
    } finally {
      setLoading(false);
    }
  };

  const triggerError = (msg) => {
    setError(msg);
    setShake(true);
    setTimeout(() => setShake(false), 500);
  };

  const disabled = loading || success;

  return (
    <div className="min-h-screen bg-[#050810] flex items-center justify-center relative overflow-hidden">

      {/* ── Hex-grid background ── */}
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.05] pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
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
        ref={formRef}
        role="main"
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
            {[1, 2].map((n) => (
              <motion.div
                key={n}
                className="absolute rounded-2xl border border-gold/20"
                style={{ inset: -n * 6 }}
                animate={{ scale: [1, 1.12 + n * 0.05], opacity: [0.4, 0] }}
                transition={{ duration: 2.5, repeat: Infinity, delay: n * 0.4 }}
                aria-hidden="true"
              />
            ))}
            <div
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold via-yellow-400 to-amber-500
                          flex items-center justify-center shadow-2xl shadow-gold/40 relative z-10"
              aria-label="Immortal Wall AI logo"
            >
              <svg viewBox="0 0 120 140" className="w-9 h-9" aria-hidden="true">
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
          <h2 className="text-center text-text-primary font-semibold text-sm tracking-wide mb-5">
            Sign In
          </h2>

          {/* ── Form fields ── */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
            noValidate
            className="flex flex-col gap-4 mb-5"
            aria-label="Login form"
          >
            <Field
              label="Email"
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={disabled}
              autoFocus
              placeholder="analyst@immortalwall.ai"
            />
            <Field
              label="Password"
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={disabled}
              placeholder="••••••••"
            />
          </form>

          {/* ── Error / success feedback ── */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.p
                key="err"
                role="alert"
                initial={{ opacity: 0, y: -4, height: 0 }}
                animate={{ opacity: 1, y: 0,  height: "auto" }}
                exit={{   opacity: 0, y: -4,  height: 0 }}
                className="text-red-400 text-[11px] text-center mb-4 px-3 py-2 rounded-lg
                           bg-red-500/10 border border-red-500/20"
              >
                {error}
              </motion.p>
            )}
            {success && (
              <motion.p
                key="ok"
                role="status"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-green-400 text-[11px] text-center mb-4 px-3 py-2 rounded-lg
                           bg-green-500/10 border border-green-500/20"
              >
                Access granted — entering system…
              </motion.p>
            )}
          </AnimatePresence>

          {/* ── Submit button ── */}
          <motion.button
            type="submit"
            whileHover={!disabled ? { scale: 1.02 } : {}}
            whileTap={!disabled  ? { scale: 0.97 } : {}}
            onClick={handleSubmit}
            disabled={!email.trim() || !password || disabled}
            aria-busy={loading}
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
                  aria-hidden="true"
                />
                Verifying…
              </span>
            ) : success ? (
              "✓ Access Granted"
            ) : (
              "Sign In →"
            )}
          </motion.button>

          <p className="text-center text-[9px] text-white/10 mt-4 font-mono tracking-[0.35em] uppercase">
            Authorised Personnel Only
          </p>
        </motion.div>

        {/* ── Bottom status bar ── */}
        <div className="flex justify-center gap-6 mt-5" aria-hidden="true">
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
