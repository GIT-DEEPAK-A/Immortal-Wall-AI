import React from "react";
import { motion } from "framer-motion";

const StatusCards = ({ status, threats, logs, realTimeData }) => {
  const totalThreats = status?.threats?.total_threats || 0;
  const activeThreats = status?.threats?.recent_threats_24h || 0;
  const blockedThreats = status?.threats?.blocked_threats || 0;
  const avgThreatScore = status?.threats?.average_threat_score || 0;
  const activeConnections = realTimeData?.activeConnections || 0;
  const threatsPerMinute = realTimeData?.threatsPerMinute || 0;

  const cards = [
    {
      title: "System Status",
      value: status?.agent_status ? "Online" : "Degraded",
      icon: "🟢",
      color: "green-400",
      glow: "shadow-green-400/50",
      subtitle: `${activeConnections} connections`
    },
    {
      title: "Threat Level",
      value: activeThreats > 10 ? "CRITICAL" : activeThreats > 5 ? "HIGH" : activeThreats > 0 ? "MEDIUM" : "LOW",
      icon: activeThreats > 10 ? "🔴" : activeThreats > 5 ? "🟠" : activeThreats > 0 ? "🟡" : "🟢",
      color: activeThreats > 10 ? "red-400" : activeThreats > 5 ? "orange-400" : activeThreats > 0 ? "yellow-400" : "green-400",
      glow: activeThreats > 10 ? "shadow-red-400/50" : activeThreats > 5 ? "shadow-orange-400/50" : activeThreats > 0 ? "shadow-yellow-400/50" : "shadow-green-400/50",
      subtitle: `${activeThreats} in last 24h`
    },
    {
      title: "Active Threats",
      value: totalThreats,
      icon: "⚡",
      color: "orange-400",
      glow: "shadow-orange-400/50",
      subtitle: `${threatsPerMinute.toFixed(1)}/min`
    },
    {
      title: "AI Confidence",
      value: `${(avgThreatScore * 100).toFixed(1)}%`,
      icon: "🤖",
      color: "gold",
      glow: "shadow-gold/50",
      subtitle: `${blockedThreats} blocked`
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.5 }}
          className={`backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl ${card.glow} hover:scale-105 transition-all duration-300`}
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center bg-${card.color}/20`}>
              <span className="text-2xl">{card.icon}</span>
            </div>
            {card.isProgress && (
              <div className="w-16 h-2 bg-surface-hover rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "98.6%" }}
                  transition={{ delay: 1, duration: 1 }}
                  className="h-full bg-gold rounded-full"
                />
              </div>
            )}
          </div>
          <div className="space-y-1">
            <p className="text-text-secondary text-sm">{card.title}</p>
            <p className={`text-2xl font-bold text-${card.color}`}>{card.value}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default StatusCards;