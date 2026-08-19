import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ─────────────────────────────────────────────
   Animated hex-grid background
───────────────────────────────────────────── */
const HexGrid = () => (
  <svg
    className="absolute inset-0 w-full h-full opacity-10 pointer-events-none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <pattern id="hex" width="56" height="100" patternUnits="userSpaceOnUse">
        <polygon
          points="28,2 54,16 54,44 28,58 2,44 2,16"
          fill="none"
          stroke="#FFD700"
          strokeWidth="0.6"
        />
        <polygon
          points="28,52 54,66 54,94 28,108 2,94 2,66"
          fill="none"
          stroke="#FFD700"
          strokeWidth="0.6"
        />
        <polygon
          points="56,26 82,40 82,68 56,82 30,68 30,40"
          fill="none"
          stroke="#FFD700"
          strokeWidth="0.6"
        />
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#hex)" />
  </svg>
);

/* ─────────────────────────────────────────────
   Orbiting defence ring
───────────────────────────────────────────── */
const OrbitRing = ({ radius, duration, dotCount, color }) => {
  const dots = Array.from({ length: dotCount });
  return (
    <motion.div
      className="absolute inset-0 flex items-center justify-center pointer-events-none"
      animate={{ rotate: 360 }}
      transition={{ duration, repeat: Infinity, ease: "linear" }}
    >
      {dots.map((_, i) => {
        const angle = (360 / dotCount) * i;
        const rad   = (angle * Math.PI) / 180;
        const x     = Math.cos(rad) * radius;
        const y     = Math.sin(rad) * radius;
        return (
          <div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full"
            style={{
              background: color,
              transform: `translate(${x}px, ${y}px)`,
              boxShadow: `0 0 6px ${color}`,
            }}
          />
        );
      })}
    </motion.div>
  );
};

/* ─────────────────────────────────────────────
   Main splash component
   Props:
     onEnter — called when user proceeds to login
───────────────────────────────────────────── */
const SplashScreen = ({ onEnter }) => {
  const [phase, setPhase] = useState("intro"); // intro | ready | exit
  const [scanLine, setScanLine] = useState(0);
  const [glitchActive, setGlitchActive] = useState(false);

  /* Auto-advance intro → ready after 3.5 s */
  useEffect(() => {
    const t = setTimeout(() => setPhase("ready"), 3500);
    return () => clearTimeout(t);
  }, []);

  /* Animate scan line 0→100 during intro */
  useEffect(() => {
    if (phase !== "intro") return;
    const interval = setInterval(() => {
      setScanLine((v) => {
        if (v >= 100) { clearInterval(interval); return 100; }
        return v + 2;
      });
    }, 60);
    return () => clearInterval(interval);
  }, [phase]);

  /* Random glitch flashes */
  useEffect(() => {
    const interval = setInterval(() => {
      setGlitchActive(true);
      setTimeout(() => setGlitchActive(false), 120);
    }, 3000 + Math.random() * 2000);
    return () => clearInterval(interval);
  }, []);

  const handleEnter = () => {
    setPhase("exit");
    setTimeout(onEnter, 600);
  };

  return (
    <AnimatePresence>
      {phase !== "exit" && (
        <motion.div
          key="splash"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.04 }}
          transition={{ duration: 0.6 }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#050810] overflow-hidden select-none"
        >
          {/* ── Background layers ── */}
          <HexGrid />

          {/* Radial glow */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_50%,rgba(255,215,0,0.07),transparent)]" />

          {/* Scan line (intro only) */}
          {phase === "intro" && (
            <motion.div
              className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold to-transparent opacity-60"
              style={{ top: `${scanLine}%` }}
            />
          )}

          {/* ── Orbiting rings ── */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <OrbitRing radius={160} duration={20} dotCount={12} color="rgba(255,215,0,0.7)" />
            <OrbitRing radius={200} duration={35} dotCount={8}  color="rgba(255,215,0,0.35)" />
            <OrbitRing radius={250} duration={55} dotCount={6}  color="rgba(255,215,0,0.2)" />
          </div>

          {/* ── Centre shield ── */}
          <motion.div
            className="relative z-10 flex flex-col items-center"
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1,   opacity: 1 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Shield icon */}
            <motion.div
              className="relative mb-8"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              {/* Pulse rings */}
              {[1, 2, 3].map((n) => (
                <motion.div
                  key={n}
                  className="absolute inset-0 rounded-full border border-gold/30"
                  animate={{ scale: [1, 1.8 + n * 0.3], opacity: [0.6, 0] }}
                  transition={{
                    duration: 2.4,
                    repeat: Infinity,
                    delay: n * 0.6,
                    ease: "easeOut",
                  }}
                  style={{ width: 100, height: 100, top: 10, left: 10 }}
                />
              ))}

              {/* Shield SVG */}
              <div className="w-28 h-28 relative">
                <svg viewBox="0 0 120 140" className="w-full h-full drop-shadow-[0_0_30px_rgba(255,215,0,0.6)]">
                  <defs>
                    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%"   stopColor="#FFD700" />
                      <stop offset="50%"  stopColor="#FFA500" />
                      <stop offset="100%" stopColor="#FFD700" />
                    </linearGradient>
                    <filter id="shieldGlow">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                  </defs>
                  <path
                    d="M60 4 L108 24 L108 68 C108 98 84 122 60 132 C36 122 12 98 12 68 L12 24 Z"
                    fill="url(#shieldGrad)"
                    filter="url(#shieldGlow)"
                    opacity="0.95"
                  />
                  <path
                    d="M60 4 L108 24 L108 68 C108 98 84 122 60 132 C36 122 12 98 12 68 L12 24 Z"
                    fill="none"
                    stroke="rgba(255,255,255,0.3)"
                    strokeWidth="1.5"
                  />
                  {/* AI circuit lines inside shield */}
                  <g stroke="rgba(0,0,0,0.55)" strokeWidth="2" fill="none">
                    <line x1="60" y1="30" x2="60" y2="100" />
                    <line x1="35" y1="55" x2="85" y2="55" />
                    <circle cx="60" cy="55" r="10" />
                    <circle cx="60" cy="55" r="4" fill="rgba(0,0,0,0.7)" />
                    <line x1="60" y1="30" x2="45" y2="43" />
                    <line x1="60" y1="30" x2="75" y2="43" />
                    <line x1="35" y1="55" x2="35" y2="75" />
                    <line x1="85" y1="55" x2="85" y2="75" />
                  </g>
                </svg>
              </div>
            </motion.div>

            {/* Title */}
            <motion.div
              className={`text-center mb-3 ${glitchActive ? "translate-x-0.5" : ""}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8 }}
            >
              <h1 className="text-5xl md:text-6xl font-orbitron font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-gold via-yellow-300 to-gold drop-shadow-[0_0_20px_rgba(255,215,0,0.5)]">
                IMMORTAL WALL
              </h1>
              <div className="flex items-center justify-center gap-3 mt-2">
                <div className="h-px w-16 bg-gradient-to-r from-transparent to-gold/60" />
                <span className="text-gold/80 text-sm font-orbitron tracking-[0.5em] uppercase">AI</span>
                <div className="h-px w-16 bg-gradient-to-l from-transparent to-gold/60" />
              </div>
            </motion.div>

            {/* Tagline */}
            <motion.p
              className="text-text-secondary text-sm tracking-[0.3em] uppercase mb-10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.8 }}
            >
              Defend Before They Attack
            </motion.p>

            {/* Status ticker (intro phase) */}
            <AnimatePresence mode="wait">
              {phase === "intro" && (
                <motion.div
                  key="ticker"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center gap-3 mb-8"
                >
                  {/* Progress bar */}
                  <div className="w-64 h-0.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-gold/80 to-gold rounded-full"
                      style={{ width: `${scanLine}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>
                  <span className="text-gold/50 font-mono text-xs tracking-widest">
                    INITIALISING SYSTEMS · {scanLine}%
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Enter button (ready phase) */}
            <AnimatePresence>
              {phase === "ready" && (
                <motion.button
                  key="enter-btn"
                  initial={{ opacity: 0, scale: 0.85, y: 10 }}
                  animate={{ opacity: 1, scale: 1,    y: 0  }}
                  exit={{   opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  onClick={handleEnter}
                  className="group relative px-12 py-4 rounded-xl font-orbitron font-bold tracking-widest text-sm uppercase overflow-hidden"
                >
                  {/* Animated border */}
                  <span className="absolute inset-0 rounded-xl border border-gold/50 group-hover:border-gold transition-colors duration-300" />
                  {/* Glow fill on hover */}
                  <span className="absolute inset-0 rounded-xl bg-gold/0 group-hover:bg-gold/10 transition-all duration-300" />
                  {/* Corner accents */}
                  <span className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-gold rounded-tl" />
                  <span className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-gold rounded-tr" />
                  <span className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-gold rounded-bl" />
                  <span className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-gold rounded-br" />

                  <motion.span
                    className="relative z-10 text-gold group-hover:text-yellow-200 transition-colors duration-200 flex items-center gap-3"
                    animate={{ x: [0, 3, 0] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  >
                    Enter Secure System
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </motion.span>
                </motion.button>
              )}
            </AnimatePresence>
          </motion.div>

          {/* ── Bottom status bar ── */}
          <motion.div
            className="absolute bottom-6 left-0 right-0 flex items-center justify-center gap-8 text-xs font-mono"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2 }}
          >
            {[
              { label: "AI ENGINE",   color: "text-green-400" },
              { label: "HONEYPOT",    color: "text-green-400" },
              { label: "RULE ENGINE", color: "text-green-400" },
              { label: "ML MODEL",    color: "text-green-400" },
            ].map(({ label, color }) => (
              <div key={label} className="flex items-center gap-2 text-text-secondary/50">
                <span className={`w-1.5 h-1.5 rounded-full ${color} animate-pulse`} />
                {label}
              </div>
            ))}
          </motion.div>

          {/* ── Version stamp ── */}
          <div className="absolute bottom-2 right-4 text-[10px] text-white/10 font-mono tracking-widest">
            v2.0.0
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SplashScreen;
