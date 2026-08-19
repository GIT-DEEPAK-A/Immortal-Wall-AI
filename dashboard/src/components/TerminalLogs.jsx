import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";

const TerminalLogs = ({ logs }) => {
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const recentLogs = logs.slice(-20);

  return (
    <div className="space-y-4">
      <h3 className="text-gold font-orbitron text-lg mb-4">Live Terminal Logs</h3>

      <div
        ref={logRef}
        className="backdrop-blur-xl bg-black/80 border border-gold/20 rounded-xl p-4 h-64 overflow-y-auto font-mono text-sm"
      >
        {recentLogs.length === 0 ? (
          <div className="text-text-secondary">
            <span className="text-green-400">$</span> Initializing security systems...<br/>
            <span className="text-green-400">$</span> AI threat detection online<br/>
            <span className="text-green-400">$</span> Honeypot deployment active<br/>
            <span className="text-yellow-400">$</span> Monitoring network traffic...<br/>
            <span className="text-green-400">$</span> System ready
          </div>
        ) : (
          recentLogs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className={`mb-1 ${
                log.event_type === "login" && log.status === "failed" ? "text-red-400" :
                log.threat_flags?.failed_login ? "text-orange-400" :
                "text-green-400"
              }`}
            >
              <span className="text-gold">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>{" "}
              <span className="text-blue-400">{log.ip}</span>{" "}
              <span className="text-purple-400">{log.username}</span>{" "}
              <span className="text-yellow-400">{log.event_type}</span>{" "}
              <span className={
                log.status === "success" ? "text-green-400" :
                log.status === "failed" ? "text-red-400" :
                "text-text-secondary"
              }>
                {log.status}
              </span>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
};

export default TerminalLogs;