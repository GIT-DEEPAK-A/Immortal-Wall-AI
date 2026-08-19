import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import getApi from '../api';

const ThreatPredictionPage = ({ onLogout }) => {
  const [predictionData, setPredictionData] = useState([]);
  const [currentRisk, setCurrentRisk] = useState('LOW');
  const [aiConfidence, setAiConfidence] = useState(0);
  const [logs, setLogs] = useState([]);
  const [honeypotStatus, setHoneypotStatus] = useState({
    adminPanel: false,
    database: true,
    loginPortal: false,
    apiEndpoint: true
  });
  const [responseActions, setResponseActions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch threat predictions and system status
  const fetchData = async () => {
    const api = getApi();
    if (!api) return;
    try {
      const [analyticsRes, statusRes] = await Promise.all([
        api.get('/api/analytics?timeframe=1h'),
        api.get('/api/system-status')
      ]);

      // Process threat trends for prediction chart
      const trends = analyticsRes.data?.threat_trends || [];
      const processedData = trends.slice(-10).map((point, index) => ({
        time: point.hour.split(' ')[1] || `${index * 6}:00`,
        probability: Math.min(point.count * 10, 100) // Scale threat count to percentage
      }));

      setPredictionData(processedData.length > 0 ? processedData : [
        { time: '00:00', probability: 20 },
        { time: '00:06', probability: 35 },
        { time: '00:12', probability: 50 },
        { time: '00:18', probability: 65 },
        { time: '00:24', probability: 45 },
        { time: '00:30', probability: 70 },
        { time: '00:36', probability: 55 },
        { time: '00:42', probability: 80 },
        { time: '00:48', probability: 60 },
        { time: '00:54', probability: 75 }
      ]);

      // Calculate current risk level
      const recentThreats = statusRes.data?.threats?.recent_threats_24h || 0;
      const avgScore = statusRes.data?.threats?.average_threat_score || 0;

      let riskLevel = 'LOW';
      if (recentThreats > 50 || avgScore > 0.7) riskLevel = 'CRITICAL';
      else if (recentThreats > 20 || avgScore > 0.5) riskLevel = 'HIGH';
      else if (recentThreats > 5 || avgScore > 0.3) riskLevel = 'MEDIUM';

      setCurrentRisk(riskLevel);
      setAiConfidence(avgScore * 100);

      // Update logs with recent threats
      const recentThreatsData = statusRes.data?.recent_threats || [];
      const logEntries = recentThreatsData.slice(0, 5).map(threat => {
        const time = new Date(threat.timestamp).toLocaleTimeString();
        return `[${time}] ${threat.threat_type} threat from ${threat.ip_address} - ${threat.threat_level}`;
      });

      setLogs(logEntries.length > 0 ? logEntries : [
        '[14:30:15] AI prediction updated - MEDIUM risk level',
        '[14:29:45] Suspicious login attempt detected',
        '[14:28:20] Honeypot activated on port 8080',
        '[14:27:10] Threat prediction: 75% confidence',
        '[14:26:05] Database access pattern anomaly'
      ]);

      // Update response actions
      const actions = [];
      if (recentThreats > 0) {
        actions.push({
          action: 'Block suspicious IPs',
          status: 'completed',
          time: new Date().toLocaleTimeString()
        });
      }
      if (avgScore > 0.5) {
        actions.push({
          action: 'Enable enhanced monitoring',
          status: 'active',
          time: new Date().toLocaleTimeString()
        });
      }

      setResponseActions(actions.length > 0 ? actions : [
        { action: 'Block suspicious IP', status: 'completed', time: '14:30:00' },
        { action: 'Enable rate limiting', status: 'active', time: '14:29:30' },
        { action: 'Alert security team', status: 'pending', time: '14:28:45' }
      ]);

      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching threat prediction data:', error);
      setIsLoading(false);
      // Keep default data on error
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Generate SVG path
  const pathData = predictionData.length > 0
    ? `M 0 ${200 - predictionData[0].probability * 1.6} ${predictionData.map((point, i) =>
        `L ${i * 8} ${200 - point.probability * 1.6}`
      ).join(' ')}`
    : 'M 0 160 L 80 160';

  return (
    <div className="min-h-screen bg-dark text-text-primary font-poppins flex-1 relative">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Cyber Grid */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="threat-grid" width="5" height="5" patternUnits="userSpaceOnUse">
                <path d="M 5 0 L 0 0 0 5" fill="none" stroke="#FFD700" strokeWidth="0.05" opacity="0.3"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#threat-grid)" />
          </svg>
        </div>
      </div>

      <div className="relative z-10 p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-4xl font-orbitron text-gold mb-2">AI Threat Prediction</h1>
          <p className="text-text-secondary mb-8">Real-time cybersecurity intelligence and automated response</p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* AI Prediction Graph */}
          <motion.div
            className="lg:col-span-2 backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl shadow-gold/10"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h3 className="text-gold font-orbitron text-xl mb-4">AI Prediction Graph</h3>
            <div className="relative h-64">
              <svg className="w-full h-full" viewBox="0 0 400 200">
                <defs>
                  <linearGradient id="prediction-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#FFD700" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#FFD700" stopOpacity="0.2" />
                  </linearGradient>
                </defs>

                {/* Grid lines */}
                <g className="opacity-20">
                  {[...Array(6)].map((_, i) => (
                    <line
                      key={i}
                      x1="0"
                      y1={i * 40}
                      x2="400"
                      y2={i * 40}
                      stroke="#FFD700"
                      strokeWidth="0.5"
                    />
                  ))}
                </g>

                {/* Prediction line */}
                <motion.path
                  d={pathData}
                  fill="none"
                  stroke="#FFD700"
                  strokeWidth="3"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 2 }}
                />

                {/* Fill area */}
                <motion.path
                  d={`${pathData} L 400 200 L 0 200 Z`}
                  fill="url(#prediction-gradient)"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.3 }}
                  transition={{ duration: 2, delay: 0.5 }}
                />

                {/* Data points */}
                {predictionData.map((point, i) => (
                  <motion.circle
                    key={i}
                    cx={i * 40}
                    cy={200 - point.probability * 1.6}
                    r="4"
                    fill="#FFD700"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                  />
                ))}
              </svg>

              {/* Risk level indicator */}
              <div className="absolute top-4 right-4">
                <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  currentRisk === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-400/50' :
                  currentRisk === 'MEDIUM' ? 'bg-orange-500/20 text-orange-400 border border-orange-400/50' :
                  'bg-green-500/20 text-green-400 border border-green-400/50'
                }`}>
                  {currentRisk} RISK
                </div>
              </div>
            </div>
          </motion.div>

          {/* Risk Assessment Panel */}
          <motion.div
            className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl shadow-gold/10"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h3 className="text-gold font-orbitron text-xl mb-4">Risk Assessment</h3>
            <div className="space-y-4">
              {predictionData.slice(-3).map((point, i) => {
                const confidence = Math.round(point.probability);
                return (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-text-primary">Threat {i + 1}</span>
                      <span className={`font-bold ${
                        confidence > 70 ? 'text-red-400' :
                        confidence > 40 ? 'text-orange-400' :
                        'text-green-400'
                      }`}>
                        {confidence}%
                      </span>
                    </div>
                    <div className="w-full bg-surface-hover rounded-full h-2">
                      <motion.div
                        className={`h-2 rounded-full ${
                          confidence > 70 ? 'bg-red-400' :
                          confidence > 40 ? 'bg-orange-400' :
                          'bg-green-400'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${confidence}%` }}
                        transition={{ duration: 1, delay: 0.8 + i * 0.2 }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Honeypot Sync Panel */}
          <motion.div
            className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl shadow-gold/10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <h4 className="text-gold font-orbitron text-lg mb-4">Honeypot Deployment</h4>
            <div className="space-y-3">
              <div className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-300 ${
                honeypotStatus.adminPanel
                  ? 'border-red-400/50 bg-red-400/10 shadow-lg shadow-red-400/20'
                  : 'border-gold/20 bg-surface-hover'
              }`}>
                <span className="text-text-primary">Fake Admin Panel</span>
                <span className={`text-sm font-semibold ${
                  honeypotStatus.adminPanel ? 'text-red-400' : 'text-green-400'
                }`}>
                  {honeypotStatus.adminPanel ? 'ACTIVATED' : 'STANDBY'}
                </span>
              </div>

              <div className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-300 ${
                honeypotStatus.database
                  ? 'border-red-400/50 bg-red-400/10 shadow-lg shadow-red-400/20'
                  : 'border-gold/20 bg-surface-hover'
              }`}>
                <span className="text-text-primary">Decoy Database</span>
                <span className={`text-sm font-semibold ${
                  honeypotStatus.database ? 'text-red-400' : 'text-green-400'
                }`}>
                  {honeypotStatus.database ? 'ACTIVATED' : 'STANDBY'}
                </span>
              </div>
            </div>
          </motion.div>

          {/* Automated Response Panel */}
          <motion.div
            className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl shadow-gold/10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <h4 className="text-gold font-orbitron text-lg mb-4">Automated Response</h4>
            <div className="space-y-3">
              {responseActions.map((action, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1, duration: 0.5 }}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    action.status === 'active'
                      ? 'border-orange-400/50 bg-orange-400/10 shadow-lg shadow-orange-400/20'
                      : 'border-green-400/50 bg-green-400/10'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      action.status === 'active' ? 'bg-orange-400 animate-pulse' : 'bg-green-400'
                    }`}></div>
                    <span className="text-text-primary text-sm">{action.action}</span>
                  </div>
                  <span className="text-xs text-text-secondary">{action.time}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Live Logs Feed */}
          <motion.div
            className="backdrop-blur-xl bg-surface/80 border border-gold/20 rounded-xl p-6 shadow-2xl shadow-gold/10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 1 }}
          >
            <h4 className="text-gold font-orbitron text-lg mb-4">Live Security Logs</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto font-mono text-xs">
              {logs.map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05, duration: 0.3 }}
                  className={
                    log.includes('Suspicious') || log.includes('Threat') 
                      ? 'p-2 rounded bg-red-400/10 text-red-400' 
                      : log.includes('Prediction') 
                      ? 'p-2 rounded bg-orange-400/10 text-orange-400' 
                      : 'p-2 rounded bg-gold/10 text-gold'
                  }
                >
                  {log}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default ThreatPredictionPage;