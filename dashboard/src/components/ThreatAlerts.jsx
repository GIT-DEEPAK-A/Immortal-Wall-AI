import React from "react";
import { motion } from "framer-motion";

const ThreatAlerts = ({ threats }) => {
  const recentThreats = threats.slice(-3);

  return (
    <div className="space-y-4">
      <h3 className="text-gold font-orbitron text-lg mb-4">AI Threat Prediction</h3>

      {/* Chart placeholder */}
      <div className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-4 h-32 mb-4">
        <div className="flex items-end justify-between h-full space-x-2">
          {[...Array(10)].map((_, i) => (
            <motion.div
              key={i}
              className="bg-gradient-to-t from-gold to-gold-soft rounded-sm flex-1"
              initial={{ height: 0 }}
              animate={{ height: `${20 + Math.random() * 60}%` }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
            />
          ))}
        </div>
        <p className="text-text-secondary text-xs mt-2 text-center">Threat Probability Trend</p>
      </div>

      {/* Alerts */}
      <div className="space-y-3">
        <div className="backdrop-blur-xl bg-red-400/10 border border-red-400/20 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-red-400">⚠️</span>
            <span className="text-red-400 font-semibold">Potential brute force attack detected</span>
          </div>
          <p className="text-text-secondary text-sm">Multiple failed login attempts from IP 192.168.1.100</p>
        </div>

        <div className="backdrop-blur-xl bg-orange-400/10 border border-orange-400/20 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-orange-400">👤</span>
            <span className="text-orange-400 font-semibold">Suspicious login activity</span>
          </div>
          <p className="text-text-secondary text-sm">Unusual login pattern detected</p>
        </div>
      </div>
    </div>
  );
};

export default ThreatAlerts;