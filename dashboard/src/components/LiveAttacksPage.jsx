import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

const attacks = [
  {
    id: "atk-001",
    ip: "195.154.92.47",
    country: "Russia",
    attackType: "DDoS",
    threatLevel: "Critical",
    status: "Blocked",
    confidence: 98.5,
    timestamp: "12:01:15",
    payload: "SYN flood attack",
    vector: "UDP amplification",
  },
  {
    id: "atk-002",
    ip: "203.101.24.18",
    country: "China",
    attackType: "Brute Force",
    threatLevel: "High",
    status: "Redirected to Honeypot",
    confidence: 96.4,
    timestamp: "12:02:30",
    payload: "SSH credential stuffing",
    vector: "Dictionary attack",
  },
  {
    id: "atk-003",
    ip: "185.220.100.255",
    country: "Brazil",
    attackType: "SQL Injection",
    threatLevel: "High",
    status: "Active",
    confidence: 94.2,
    timestamp: "12:03:45",
    payload: "Database query manipulation",
    vector: "Input validation bypass",
  },
  {
    id: "atk-004",
    ip: "91.199.119.66",
    country: "Ukraine",
    attackType: "Credential Harvesting",
    threatLevel: "Medium",
    status: "Blocked",
    confidence: 89.7,
    timestamp: "12:04:10",
    payload: "Phishing infrastructure",
    vector: "Social engineering",
  },
];

const attackLogs = [
  "[12:01:15] Incoming connection from Russia - DDoS detected",
  "[12:01:18] Attack pattern analysis: SYN flood - Threat score 98.5%",
  "[12:01:20] Response triggered: IP blocked by firewall",
  "[12:02:30] Connection attempt from China - Brute force detected",
  "[12:02:35] Honeypot engagement: Attacker redirected to decoy server",
  "[12:03:45] SQL injection attempt intercepted",
  "[12:03:48] Payload captured and stored for analysis",
  "[12:04:10] Credential harvesting attempt from Ukraine",
];

const stats = [
  { label: "Total Attacks Today", value: "1,247", color: "text-red-400" },
  { label: "Active Threats", value: "4", color: "text-orange-400" },
  { label: "Blocked Attacks", value: "1,243", color: "text-green-400" },
];

const GlobeVisualization = ({ selectedAttack }) => {
  return (
    <div className="relative w-full h-96 flex items-center justify-center">
      <svg className="w-full h-full" viewBox="0 0 500 500" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="globe-gradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255,215,0,0.15)" />
            <stop offset="100%" stopColor="rgba(255,215,0,0.05)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="attack-glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <circle cx="250" cy="250" r="150" fill="url(#globe-gradient)" stroke="rgba(255,215,0,0.3)" strokeWidth="1" />

        <g opacity="0.2">
          <line x1="150" y1="250" x2="350" y2="250" stroke="#FFD700" strokeWidth="0.5" />
          <line x1="250" y1="150" x2="250" y2="350" stroke="#FFD700" strokeWidth="0.5" />
          <circle cx="250" cy="250" r="100" fill="none" stroke="#FFD700" strokeWidth="0.5" />
          <circle cx="250" cy="250" r="75" fill="none" stroke="#FFD700" strokeWidth="0.5" />
        </g>

        <circle cx="250" cy="250" r="20" fill="#FFD700" filter="url(#glow)" />
        <circle cx="250" cy="250" r="20" fill="none" stroke="#FFD700" strokeWidth="2" opacity="0.6">
          <animate attributeName="r" from="20" to="40" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite" />
        </circle>

        {attacks.map((attack, idx) => {
          const angle = (idx * 90) * (Math.PI / 180);
          const distance = 120;
          const x = 250 + distance * Math.cos(angle);
          const y = 250 + distance * Math.sin(angle);

          return (
            <g key={attack.id}>
              <line
                x1="250"
                y1="250"
                x2={x}
                y2={y}
                stroke="#FF4F40"
                strokeWidth="2"
                opacity={selectedAttack?.id === attack.id ? 1 : 0.3}
                filter="url(#attack-glow)"
              >
                <animate
                  attributeName="strokeDasharray"
                  from="0,1000"
                  to="1000,0"
                  dur="3s"
                  repeatCount="indefinite"
                />
              </line>

              <circle cx={x} cy={y} r="8" fill="#FF4F40" filter="url(#attack-glow)">
                <animate attributeName="r" from="8" to="16" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" from="1" to="0.3" dur="2s" repeatCount="indefinite" />
              </circle>

              <circle cx={x} cy={y} r="6" fill="#FF6B4A" opacity={selectedAttack?.id === attack.id ? 1 : 0.6} />
            </g>
          );
        })}
      </svg>

      <div className="absolute bottom-6 left-6 text-xs text-text-secondary uppercase tracking-[0.3em]">
        <p>Global Threat Map</p>
        <p className="text-gold mt-1">{attacks.length} Active Attacks</p>
      </div>
    </div>
  );
};

const LiveAttacksPage = () => {
  const [selectedAttack, setSelectedAttack] = useState(attacks[0]);
  const [aiText, setAiText] = useState("");
  const [typingIndex, setTypingIndex] = useState(0);

  const insight = "This attack pattern matches known botnet behavior. Estimated command & control server located in Eastern Europe.";

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (typingIndex < insight.length) {
        setAiText((prev) => prev + insight[typingIndex]);
        setTypingIndex(typingIndex + 1);
      }
    }, 25);

    return () => clearTimeout(timeout);
  }, [typingIndex, insight]);

  const handleSelectAttack = (attack) => {
    setSelectedAttack(attack);
    setAiText("");
    setTypingIndex(0);
  };

  return (
    <div className="min-h-screen bg-dark text-text-primary font-poppins flex-1 relative overflow-hidden">
      <div className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_center,_rgba(255,215,0,0.12),_transparent_50%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(10,15,28,0.8),rgba(10,15,28,0.95))] pointer-events-none" />

      <div className="relative z-10 p-6 lg:p-8 space-y-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3 max-w-3xl">
            <p className="text-sm uppercase tracking-[0.3em] text-gold/80">Real-Time Global Threat Visualization</p>
            <h1 className="text-4xl lg:text-5xl font-orbitron text-gold">Live Cyber Attack Monitoring</h1>
            <p className="text-text-secondary max-w-2xl text-sm lg:text-base">
              Immersive 3D holographic attack visualization. Monitor incoming threats in real-time, visualize attack vectors on a global map, and trigger automated responses through integrated AI defense systems.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1.2fr_0.85fr] gap-8">
          <section className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="rounded-[38px] border border-gold/20 bg-surface/85 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
            >
              <p className="text-sm uppercase tracking-[0.3em] text-gold/70 mb-4">3D Attack Visualization</p>
              <GlobeVisualization selectedAttack={selectedAttack} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="grid grid-cols-3 gap-4"
            >
              {stats.map((stat, idx) => (
                <div
                  key={idx}
                  className="rounded-[28px] border border-gold/15 bg-surface/80 backdrop-blur-xl p-5 shadow-xl shadow-gold/5 text-center"
                >
                  <p className="text-xs uppercase tracking-[0.35em] text-text-secondary">{stat.label}</p>
                  <p className={`text-2xl font-orbitron ${stat.color} mt-3`}>{stat.value}</p>
                </div>
              ))}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="rounded-[38px] border border-gold/20 bg-surface/85 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
            >
              <p className="text-sm uppercase tracking-[0.3em] text-gold/70 mb-4">Attack Feeds</p>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="rounded-3xl border border-gold/10 bg-[#070B14]/90 p-5">
                  <p className="text-xs uppercase tracking-[0.25em] text-gold/60 mb-3">Live Activity Log</p>
                  <div className="space-y-2 font-mono text-xs text-text-secondary max-h-44 overflow-y-auto pr-2">
                    {attackLogs.slice(0, 8).map((log, idx) => (
                      <div key={idx} className="rounded-2xl bg-black/40 px-3 py-2 border border-gold/5 text-white/80 hover:bg-black/60 transition-colors">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-3xl border border-gold/10 bg-[#070B14]/90 p-5">
                  <p className="text-xs uppercase tracking-[0.25em] text-gold/60 mb-3">Auto Response Actions</p>
                  <div className="space-y-3 text-sm text-text-secondary">
                    <div className="rounded-2xl border border-gold/10 bg-[#0D1220]/80 p-3">
                      <div className="flex items-center justify-between">
                        <span>🔥 Firewall Updated</span>
                        <span className="text-xs bg-green-400/15 text-green-300 px-2 py-1 rounded-full">Active</span>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-gold/10 bg-[#0D1220]/80 p-3">
                      <div className="flex items-center justify-between">
                        <span>⛔ IP Blocked</span>
                        <span className="text-xs bg-green-400/15 text-green-300 px-2 py-1 rounded-full">Completed</span>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-gold/10 bg-[#0D1220]/80 p-3">
                      <div className="flex items-center justify-between">
                        <span>🚨 Alert Triggered</span>
                        <span className="text-xs bg-orange-400/15 text-orange-300 px-2 py-1 rounded-full">Pending</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </section>

          <aside className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="rounded-[38px] border border-gold/20 bg-surface/85 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-gold/70">Attack Details</p>
                  <h2 className="text-2xl font-orbitron text-white">Selected Threat</h2>
                </div>
                <div className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                  selectedAttack.threatLevel === "Critical"
                    ? "border-red-400/30 bg-red-500/15 text-red-300"
                    : selectedAttack.threatLevel === "High"
                    ? "border-orange-400/30 bg-orange-500/15 text-orange-300"
                    : "border-gold/30 bg-gold/15 text-gold"
                }`}>
                  {selectedAttack.threatLevel}
                </div>
              </div>

              <div className="space-y-3 text-sm text-text-secondary">
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Attacker IP</p>
                  <p className="mt-2 text-white font-mono font-semibold text-lg">{selectedAttack.ip}</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Location</p>
                  <p className="mt-2 text-white font-semibold">{selectedAttack.country}</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Attack Type</p>
                  <p className="mt-2 text-white font-semibold">{selectedAttack.attackType}</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Attack Vector</p>
                  <p className="mt-2 text-white font-semibold">{selectedAttack.vector}</p>
                </div>
                <div className="rounded-3xl border border-gold/10 bg-[#0C1120]/90 p-4">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">Status</p>
                  <div className="mt-2">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                      selectedAttack.status === "Blocked"
                        ? "bg-green-400/15 text-green-300"
                        : selectedAttack.status === "Active"
                        ? "bg-red-400/15 text-red-300"
                        : "bg-blue-400/15 text-blue-300"
                    }`}>
                      {selectedAttack.status}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 rounded-3xl border border-gold/10 bg-[#070B14]/90 p-5 text-sm text-text-secondary">
                <div className="flex items-center justify-between mb-3">
                  <p className="uppercase tracking-[0.3em] text-gold/70 text-[10px]">AI-Generated Insight</p>
                  <div className="rounded-full border border-gold/20 px-2 py-1 text-[10px] font-semibold text-gold">{selectedAttack.confidence}%</div>
                </div>
                <p className="text-white leading-7">{aiText || "Typing analysis..."}</p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="rounded-[38px] border border-gold/20 bg-surface/80 backdrop-blur-2xl p-6 shadow-2xl shadow-gold/10"
            >
              <p className="text-sm uppercase tracking-[0.3em] text-gold/70 mb-4">Active Attacks</p>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {attacks.map((attack) => (
                  <motion.button
                    key={attack.id}
                    onClick={() => handleSelectAttack(attack)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`w-full text-left rounded-3xl border p-4 transition-all duration-300 ${
                      selectedAttack.id === attack.id
                        ? "border-gold bg-gold/15 shadow-lg shadow-gold/15"
                        : "border-gold/10 bg-[#0D1220]/80 hover:border-gold/20"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <p className="text-xs uppercase tracking-[0.3em] text-gold/70">{attack.country}</p>
                        <p className="text-sm font-mono text-white mt-1">{attack.ip}</p>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full whitespace-nowrap ${
                        attack.threatLevel === "Critical"
                          ? "bg-red-500/15 text-red-300"
                          : attack.threatLevel === "High"
                          ? "bg-orange-500/15 text-orange-300"
                          : "bg-gold/15 text-gold"
                      }`}>
                        {attack.threatLevel}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary">{attack.attackType} • {attack.timestamp}</p>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default LiveAttacksPage;
