import React from "react";
import { motion } from "framer-motion";

const Sidebar = ({ activeItem, onItemClick, onLogout }) => {
  const menuItems = [
    { name: "Dashboard", icon: "📊" },
    { name: "Threat Prediction", icon: "🔮" },
    { name: "Honeypots", icon: "🪤" },
    { name: "Live Attacks", icon: "⚡" },
    { name: "Analytics", icon: "📈" },
    { name: "Settings", icon: "⚙️" },
  ];

  return (
    <motion.div
      initial={{ x: -240 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-60 bg-surface border-r border-gold/20 flex flex-col"
    >
      <div className="p-6 border-b border-gold/20">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-gold to-gold-soft rounded-lg flex items-center justify-center">
            <span className="text-black text-lg">🛡️</span>
          </div>
          <div>
            <h1 className="text-gold font-orbitron font-bold text-lg">IMMORTAL WALL</h1>
            <p className="text-text-secondary text-xs">AI Security</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
            onClick={() => onItemClick(item.name)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-300 ${
              activeItem === item.name
                ? "bg-gold/10 border-l-4 border-gold text-gold shadow-lg shadow-gold/20"
                : "text-text-secondary hover:bg-surface-hover hover:text-text-primary"
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="font-medium">{item.name}</span>
          </motion.button>
        ))}
      </nav>

      <div className="p-4 border-t border-gold/20">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-text-secondary hover:bg-red-400/10 hover:text-red-400 transition-all duration-300"
        >
          <span className="text-lg">🚪</span>
          <span className="font-medium">Logout</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default Sidebar;