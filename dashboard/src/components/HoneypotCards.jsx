import React, { useState } from "react";
import { motion } from "framer-motion";

const HoneypotCards = () => {
  const [honeypots, setHoneypots] = useState([
    {
      id: 1,
      name: "Decoy Server",
      status: "breached",
      message: "Malicious payload captured",
      active: true
    },
    {
      id: 2,
      name: "Fake Database",
      status: "accessed",
      message: "Unauthorized query executed",
      active: false
    },
    {
      id: 3,
      name: "Admin Panel",
      status: "lured",
      message: "Credential attempt logged",
      active: true
    }
  ]);

  const handleReplay = (id) => {
    // Simulate replay action
    console.log(`Replaying attack on honeypot ${id}`);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-gold font-orbitron text-lg mb-4">Honeypot Activity</h3>

      {honeypots.map((pot, index) => (
        <motion.div
          key={pot.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1, duration: 0.5 }}
          className={`backdrop-blur-xl bg-surface/80 border rounded-xl p-4 transition-all duration-300 ${
            pot.active
              ? "border-red-400/50 shadow-lg shadow-red-400/20"
              : "border-gold/20"
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${pot.active ? "bg-red-400" : "bg-green-400"}`} />
              <span className="font-semibold text-text-primary">{pot.name}</span>
            </div>
            <span className={`text-sm px-2 py-1 rounded ${
              pot.active ? "bg-red-400/20 text-red-400" : "bg-green-400/20 text-green-400"
            }`}>
              {pot.status}
            </span>
          </div>

          <p className="text-text-secondary text-sm mb-3">{pot.message}</p>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleReplay(pot.id)}
            className="w-full py-2 px-4 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg font-semibold hover:from-red-600 hover:to-red-700 transition-all duration-300"
          >
            Replay Attack
          </motion.button>
        </motion.div>
      ))}
    </div>
  );
};

export default HoneypotCards;