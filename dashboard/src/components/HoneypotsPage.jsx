import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

const honeypotCards = [
  {
    id: "admin",
    name: "Fake Admin Panel",
    attackType: "Brute Force",
    status: "Under Attack",
    glow: "border-red-400/40 bg-red-500/10",
    message: "Malicious payload captured",
    indicator: "danger",
    recent: ["[12:00] Login attempt blocked", "[12:01] Payload decoded", "[12:02] Attack signature stored"],
  },
  {
    id: "database",
    name: "Decoy Database Server",
    attackType: "SQL Injection",
    status: "Triggered",
    glow: "border-red-400/40 bg-red-500/10",
    message: "Query injection trapped",
    indicator: "danger",
    recent: ["[11:58] Suspicious query captured", "[12:00] Payload fingerprinted", "[12:02] Response sandboxed"],
  },
  {
    id: "login",
    name: "Dummy Login Portal",
    attackType: "Credential Stuffing",
    status: "Idle",
    glow: "border-gold/20 bg-gold/10",
    message: "No active threat",
    indicator: "idle",
    recent: ["[11:46] Honeypot armed", "[11:53] Probe detected", "[11:58] Awaiting attacker"],
  },
  {
    id: "api",
    name: "Shadow API Endpoint",
    attackType: "Malware Upload",
    status: "Idle",
    glow: "border-gold/20 bg-gold/10",
    message: "Ready to trap evasive payloads",
    indicator: "idle",
    recent: ["[11:40] Endpoint live", "[11:50] Probe scan complete", "[11:55] Attack vector mapped"],
  },
];

const liveLogs = [
  "[12:01] Honeypot triggered",
  "[12:02] Payload captured",
  "[12:03] AI analysis complete",
  "[12:04] IP blocked by firewall",
  "[12:05] Threat prediction sync validated",
];

const responseActions = [
  { label: "IP Blocked", status: "completed" },
  { label: "Firewall Updated", status: "completed" },
  { label: "Alert Sent", status: "active" },
];

const HoneypotsPage = () => {
  const [selectedHoneypot, setSelectedHoneypot] = useState(honeypotCards[0]);
  const [aiText, setAiText] = useState("");
  const [typingIndex, setTypingIndex] = useState(0);
  const insight = "Attacker is attempting credential stuffing using automated scripts.";

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (typingIndex < insight.length) {
        setAiText((prev) => prev + insight[typingIndex]);
        setTypingIndex(typingIndex + 1);
      }
    }, 35);

    return () => clearTimeout(timeout);
  }, [typingIndex, insight]);

  const handleSelectCard = (card) => {
    setSelectedHoneypot(card);
    setAiText("");
    setTypingIndex(0);
  };

  return (
    <div className="min-h-screen bg-dark text-text-primary font-poppins flex-1 relative overflow-hidden">
      <div className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_top,_rgba(255,215,0,0.08),_transparent_38%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(10,15,28,0.8),rgba(10,15,28,0.95))] pointer-events-none" />
      <div className="absolute inset-0 overflow-hidden">
        <svg className="w-full h-full" viewBox="0 0 1440 900" preserveAspectRatio="none">
          <path d="M0 100C200 40 400 140 600 90C800 40 1000 120 1200 70C1400 20 1440 70 1440 70V900H0Z" fill="rgba(255,215,0,0.04)" />
          <path d="M0 820C240 760 480 860 720 810C960 760 1200 840 1440 790V900H0Z" fill="rgba(255,215,0,0.02)" />
        </svg>
      </div>

      <div className="relative z-10 p-6 lg:p-8 space-y-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3 max-w-3xl">
            <p className="text-sm uppercase tracking-[0.3em] text-gold/80">AI-Powered Honeypot Defense System</p>
            <h1 className="text-4xl lg:text-5xl font-orbitron text-gold">Trap, Analyze, and Neutralize Attackers</h1>
            <p className="text-text-secondary max-w-2xl text-sm lg:text-base">
              Ultra-premium holographic deception control. Manage live decoy systems, replay attacks with cinematic flow visualizations, and monitor AI threat intelligence in a single high-end security command center.
            </p>
          </div>

          <div className="rounded-3xl border border-gold/20 bg-surface/70 backdrop-blur-2xl px-5 py-4 shadow-2xl shadow-gold/10 max-w-sm">
            <div className="flex items-center justify-between text-sm text-text-secondary mb-3">
              <span>Threat Prediction Sync</span>
              <span className="text-gold">2 min ago</span>
            </div>
            <p className="text-text-primary text-sm leading-6">
              This attack was predicted 2 minutes earlier by the AI timeline engine.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.9fr] gap-6">
          <section className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {honeypotCards.map((card) => (
                <motion.button
                  key={card.id}
                  onClick={() => handleSelectCard(card)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.99 }}
                  className={`group relative overflow-hidden rounded-[28px] border p-5 text-left transition-all duration-300 shadow-2xl ${
                    selectedHoneypot.id === card.id
                      ? "border-gold bg-gold/10 shadow-gold/20"
                      : "border-gold/20 bg-surface/80"
                  }`}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-gold/10 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gold">{card.name}</h3>
                      <p className="text-xs uppercase tracking-[0.25em] text-text-secondary mt-2">{card.attackType}</p>
                    </div>
                    <div className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      card.indicator === "danger"
                        ? "bg-red-500/15 text-red-300 border border-red-400/30"
                        : "bg-gold/15 text-gold border border-gold/40"
                    }`}>
                      {card.status}
                    </div>
                  </div>

                  <div className="mt-6 space-y-3">
                    <p className="text-sm text-text-secondary">{card.message}</p>
                    <div className="space-y-2">
                      {card.recent.slice(0, 2).map((entry, idx) => (
                        <div key={idx} className="rounded-2xl bg-black/40 px-3 py-2 text-xs text-text-secondary border border-gold/10">
                          {entry}
                        </div>
                      ))}
                    </div>
                  </div>

                  {card.indicator === "danger" && (
                    <div className="absolute right-5 top-5 text-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-red-400">
                      ⚠️
                    </div>
                  )}
                </motion.button>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="rounded-[38px] border border-gold/20 bg-surface/90 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
            >
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between mb-6">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-gold/70">Attack Replay</p>
                  <h2 className="text-2xl font-orbitron text-white mt-2">{selectedHoneypot.name} Flow</h2>
                </div>
                <button className="inline-flex items-center gap-2 rounded-3xl bg-gradient-to-r from-red-500 to-orange-400 px-5 py-3 text-sm font-semibold text-white shadow-xl shadow-red-500/20 hover:brightness-110 transition-all duration-300">
                  <span>Replay Attack</span>
                  <span>▶</span>
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-[0.95fr_0.5fr] gap-6">
                <div className="rounded-3xl border border-gold/15 bg-black/30 p-4">
                  <div className="relative overflow-hidden rounded-3xl border border-gold/10 bg-[#070B14]/80 p-5">
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,215,0,0.12),transparent_35%)]" />
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,_rgba(255,79,64,0.12),transparent_30%)]" />
                    <div className="relative z-10 space-y-4">
                      <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-text-secondary">
                        <span>Attacker</span>
                        <span>Analysis</span>
                      </div>
                      <div className="space-y-3">
                        <div className="rounded-3xl border border-gold/10 bg-[#0D1322]/80 p-4">
                          <p className="text-xs text-text-secondary uppercase tracking-[0.3em]">Attacker</p>
                          <p className="text-lg font-semibold text-white mt-3">Unknown Entity</p>
                        </div>
                        <div className="rounded-3xl border border-red-400/10 bg-[#200707]/90 p-4">
                          <p className="text-xs text-red-300 uppercase tracking-[0.3em]">Vector</p>
                          <p className="text-lg font-semibold text-red-300 mt-3">Payload Capture</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="rounded-3xl border border-gold/15 bg-[#080D1A]/80 p-4 text-xs text-text-secondary">
                  <div className="space-y-4">
                    <div className="rounded-3xl border border-gold/10 bg-[#111726]/90 p-3">
                      <p className="uppercase tracking-[0.25em] text-gold/70 text-[10px]">Attacker → Honeypot</p>
                      <p className="mt-3 text-white font-semibold">Connection Established</p>
                    </div>
                    <div className="rounded-3xl border border-gold/10 bg-[#111726]/90 p-3">
                      <p className="uppercase tracking-[0.25em] text-gold/70 text-[10px]">Honeypot → Capture</p>
                      <p className="mt-3 text-white font-semibold">Payload stored</p>
                    </div>
                    <div className="rounded-3xl border border-gold/10 bg-[#111726]/90 p-3">
                      <p className="uppercase tracking-[0.25em] text-gold/70 text-[10px]">Capture → Analysis</p>
                      <p className="mt-3 text-white font-semibold">Threat vector decoded</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </section>

          <aside className="space-y-6">
            <motion.div
              className="rounded-[38px] border border-gold/20 bg-surface/85 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-gold/70">AI Analysis</p>
                  <h2 className="text-2xl font-orbitron text-white">Threat Insights</h2>
                </div>
                <div className="rounded-full border border-gold/20 px-3 py-1 text-xs font-semibold text-gold/90">97.8%</div>
              </div>

              <div className="space-y-4 text-sm text-text-secondary">
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Attacker IP</p>
                  <p className="mt-2 text-white font-semibold">192.168.1.99</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Location</p>
                  <p className="mt-2 text-white font-semibold">Seoul, South Korea</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Threat Level</p>
                  <p className="mt-2 text-white font-semibold">Critical</p>
                </div>
              </div>

              <div className="mt-6 rounded-3xl border border-gold/10 bg-[#070B14]/90 p-5 text-sm text-text-secondary">
                <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px] mb-3">AI-generated insight</p>
                <p className="text-white leading-7">{aiText || "Typing analysis..."}</p>
              </div>
            </motion.div>

            <motion.div
              className="rounded-[38px] border border-gold/20 bg-surface/80 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              <h3 className="text-gold font-orbitron text-xl mb-4">Connected Systems</h3>
              <div className="space-y-4 text-sm text-text-secondary">
                <div className="rounded-3xl border border-gold/10 bg-[#0D1220]/90 p-4">
                  <p className="text-gold text-xs uppercase tracking-[0.3em] mb-3">Threat Prediction Sync</p>
                  <p>This attack was predicted 2 minutes earlier.</p>
                </div>

                <div className="rounded-3xl border border-gold/10 bg-[#0D1220]/90 p-4">
                  <p className="text-gold text-xs uppercase tracking-[0.3em] mb-3">Automated Response</p>
                  <ul className="space-y-2">
                    {responseActions.map((item) => (
                      <li key={item.label} className="flex items-center justify-between text-sm">
                        <span>{item.label}</span>
                        <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${
                          item.status === "active" ? "bg-orange-400/15 text-orange-300" : "bg-green-400/15 text-green-300"
                        }`}>
                          {item.status}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-3xl border border-gold/10 bg-[#0D1220]/90 p-4">
                  <p className="text-gold text-xs uppercase tracking-[0.3em] mb-3">Live Logs Feed</p>
                  <div className="space-y-2 font-mono text-xs text-text-secondary max-h-44 overflow-y-auto pr-1">
                    {liveLogs.map((log, index) => (
                      <div key={index} className="rounded-2xl bg-black/30 px-3 py-2 border border-gold/10 text-white/90">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default HoneypotsPage;
