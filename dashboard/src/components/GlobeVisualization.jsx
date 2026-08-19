import React from "react";
import { motion } from "framer-motion";

const GlobeVisualization = () => {
  return (
    <div className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-8 h-96 flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0">
        {/* Animated rings */}
        {[...Array(3)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute inset-0 border border-gold/20 rounded-full"
            animate={{ rotate: 360 }}
            transition={{
              duration: 20 + i * 5,
              repeat: Infinity,
              ease: "linear"
            }}
            style={{
              width: `${60 + i * 20}%`,
              height: `${60 + i * 20}%`,
              left: `${20 - i * 10}%`,
              top: `${20 - i * 10}%`,
            }}
          />
        ))}

        {/* Attack lines */}
        {[...Array(5)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-px h-16 bg-gradient-to-b from-transparent via-red-400 to-transparent"
            animate={{
              opacity: [0, 1, 0],
              scaleY: [0, 1, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.5
            }}
            style={{
              left: `${20 + i * 15}%`,
              top: `${30 + (i % 2) * 20}%`,
              transformOrigin: "bottom"
            }}
          />
        ))}
      </div>

      {/* Central globe */}
      <motion.div
        className="relative z-10"
        animate={{ rotateY: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      >
        <div className="w-32 h-32 bg-gradient-to-br from-gold via-gold-soft to-gold rounded-full flex items-center justify-center shadow-2xl shadow-gold/50">
          <div className="w-24 h-24 bg-dark rounded-full flex items-center justify-center">
            <span className="text-gold text-3xl">🛡️</span>
          </div>
        </div>
      </motion.div>

      <div className="absolute bottom-4 left-4 right-4 text-center">
        <h3 className="text-gold font-orbitron text-lg mb-2">Global Threat Monitoring</h3>
        <p className="text-text-secondary text-sm">Real-time attack visualization and defense coordination</p>
      </div>
    </div>
  );
};

export default GlobeVisualization;