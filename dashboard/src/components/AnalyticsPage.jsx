import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

const AnalyticsPage = ({ analytics = {}, realTimeData = {} }) => {
  const [timeframe, setTimeframe] = useState("24h");

  // Use real data from props, fallback to defaults
  const trendData = analytics?.threat_trends || [
    { hour: "00:00", count: 45 },
    { hour: "04:00", count: 120 },
    { hour: "08:00", count: 78 },
    { hour: "12:00", count: 95 },
    { hour: "16:00", count: 210 },
    { hour: "20:00", count: 165 },
    { hour: "24:00", count: 89 },
  ];

  const threatDistribution = Object.entries(analytics?.threat_distribution || {}).map(([label, value]) => ({
    label: label.charAt(0).toUpperCase() + label.slice(1),
    value: value,
    color: label === 'malicious' ? '#FF4F40' : label === 'suspicious' ? '#FFA500' : '#FFD700'
  })) || [
    { label: "Malicious", value: 42, color: "#FF4F40" },
    { label: "Suspicious", value: 28, color: "#FFA500" },
    { label: "Normal", value: 30, color: "#FFD700" },
  ];

  const topSources = (analytics?.top_threat_sources || []).map((source, index) => ({
    ip: source.ip,
    attacks: source.count,
    percentage: Math.round((source.count / Math.max(...(analytics?.top_threat_sources || []).map(s => s.count), 1)) * 100)
  })) || [
    { ip: "192.168.1.100", attacks: 287, percentage: 23 },
    { ip: "10.0.0.50", attacks: 245, percentage: 20 },
    { ip: "172.16.0.25", attacks: 156, percentage: 13 },
    { ip: "203.0.113.1", attacks: 134, percentage: 11 },
    { ip: "Others", attacks: 378, percentage: 33 },
  ];

  const honeypotMetrics = [
    { type: "Admin Panel", captured: 156, color: "#FF4F40" },
    { type: "Database", captured: 123, color: "#FFA500" },
    { type: "Login Portal", captured: 98, color: "#FFD700" },
    { type: "API Endpoint", captured: 67, color: "#FF6B4A" },
  ];

  const responseMetrics = [
    { label: "Avg Response Time", value: "2.3s", unit: "seconds" },
    { label: "Blocked Attacks", value: analytics?.response_effectiveness?.block_ip || "1,243", unit: "total" },
    { label: "Actions Executed", value: Object.values(analytics?.response_effectiveness || {}).reduce((a, b) => a + b, 0).toLocaleString() || "4,892", unit: "automated" },
  ];

  const LineChart = ({ data }) => {
    const maxValue = Math.max(...data.map((d) => d.count || d.attacks || 0), 1);
    const chartHeight = 200;
    const chartWidth = 100;

    const points = data.map((d, idx) => {
      const x = (idx / (Math.max(data.length - 1, 1))) * chartWidth;
      const y = chartHeight - ((d.count || d.attacks || 0) / maxValue) * chartHeight;
      return { x, y, value: d.count || d.attacks || 0, time: d.hour || d.time };
    });

    const pathD = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
    const fillPath = `${pathD} L ${chartWidth} ${chartHeight} L 0 ${chartHeight} Z`;

    return (
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full">
        <defs>
          <linearGradient id="trend-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(255,215,0,0.4)" />
            <stop offset="100%" stopColor="rgba(255,215,0,0.05)" />
          </linearGradient>
          <filter id="trend-glow">
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <path d={fillPath} fill="url(#trend-gradient)" />
        <path d={pathD} stroke="#FFD700" strokeWidth="2.5" fill="none" filter="url(#trend-glow)" />

        {points.map((p, idx) => (
          <circle key={idx} cx={p.x} cy={p.y} r="2" fill="#FFD700" opacity={0.8} />
        ))}

        <g opacity="0.2">
          {[0, 1, 2, 3, 4].map((i) => (
            <line
              key={i}
              x1="0"
              y1={(chartHeight / 4) * i}
              x2={chartWidth}
              y2={(chartHeight / 4) * i}
              stroke="#FFD700"
              strokeWidth="0.5"
            />
          ))}
        </g>
      </svg>
    );
  };

  const PieChart = ({ data }) => {
    const total = data.reduce((sum, d) => sum + d.value, 0) || 1;
    let currentAngle = -Math.PI / 2;

    const slices = data.map((d) => {
      const sliceAngle = (d.value / total) * 2 * Math.PI;
      const startAngle = currentAngle;
      const endAngle = currentAngle + sliceAngle;
      const midAngle = startAngle + sliceAngle / 2;

      const x1 = 50 + 40 * Math.cos(startAngle);
      const y1 = 50 + 40 * Math.sin(startAngle);
      const x2 = 50 + 40 * Math.cos(endAngle);
      const y2 = 50 + 40 * Math.sin(endAngle);

      const largeArc = sliceAngle > Math.PI ? 1 : 0;
      const path = `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`;

      const labelX = 50 + 25 * Math.cos(midAngle);
      const labelY = 50 + 25 * Math.sin(midAngle);

      currentAngle = endAngle;

      return { path, labelX, labelY, ...d };
    });

    return (
      <svg viewBox="0 0 100 100" className="w-full h-full">
        <defs>
          <filter id="pie-glow">
            <feGaussianBlur stdDeviation="1" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {slices.map((slice, idx) => (
          <g key={idx}>
            <path d={slice.path} fill={slice.color} opacity="0.85" filter="url(#pie-glow)" />
            <path d={slice.path} fill="none" stroke={slice.color} strokeWidth="0.5" opacity="0.4" />
          </g>
        ))}

        <circle cx="50" cy="50" r="15" fill="#0A0F1C" />
      </svg>
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-dark text-text-primary min-h-screen">
      <main className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex justify-between items-center"
        >
          <h1 className="text-4xl font-orbitron text-gold font-bold">Analytics Dashboard</h1>
          <div className="flex gap-2">
            {["1h", "24h", "7d", "30d"].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-4 py-2 rounded font-medium transition-all ${
                  timeframe === tf
                    ? "bg-gold text-dark"
                    : "bg-surface text-text-secondary hover:bg-surface-hover"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Real-time Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all">
            <h3 className="text-text-secondary text-sm font-medium mb-2">Active Connections</h3>
            <div className="text-3xl font-bold text-gold">{realTimeData?.activeConnections || 0}</div>
            <p className="text-text-secondary text-xs mt-2">Live connections</p>
          </div>

          <div className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all">
            <h3 className="text-text-secondary text-sm font-medium mb-2">Threats/Min</h3>
            <div className="text-3xl font-bold text-gold">{(realTimeData?.threatsPerMinute || 0).toFixed(1)}</div>
            <p className="text-text-secondary text-xs mt-2">Current rate</p>
          </div>

          <div className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all">
            <h3 className="text-text-secondary text-sm font-medium mb-2">System Load</h3>
            <div className="text-3xl font-bold text-gold">{realTimeData?.systemLoad || "normal"}</div>
            <p className="text-text-secondary text-xs mt-2">Status</p>
          </div>
        </motion.div>

        {/* Threat Trends */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all"
        >
          <h2 className="text-lg font-orbitron text-gold font-bold mb-4">Threat Trends</h2>
          <div className="h-64">
            <LineChart data={trendData} />
          </div>
          <div className="grid grid-cols-7 gap-2 mt-4">
            {trendData.map((d, idx) => (
              <div key={idx} className="text-center text-xs">
                <div className="text-text-secondary">{d.hour}</div>
                <div className="text-gold font-bold">{d.count}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Threat Distribution & Top Sources */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Threat Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all"
          >
            <h2 className="text-lg font-orbitron text-gold font-bold mb-4">Threat Distribution</h2>
            <div className="h-64">
              <PieChart data={threatDistribution} />
            </div>
            <div className="space-y-2 mt-4">
              {threatDistribution.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-text-secondary">{item.label}</span>
                  </div>
                  <span className="text-gold font-bold">{item.value}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Top Sources */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all"
          >
            <h2 className="text-lg font-orbitron text-gold font-bold mb-4">Top Threat Sources</h2>
            <div className="space-y-4">
              {topSources.map((source, idx) => (
                <div key={idx}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-text-secondary text-sm">{source.ip}</span>
                    <span className="text-gold font-bold">{source.attacks} attacks</span>
                  </div>
                  <div className="relative bg-surface-darker rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${source.percentage}%` }}
                      transition={{ duration: 0.8, delay: idx * 0.1 }}
                      className="h-full bg-gradient-to-r from-gold to-red-500"
                    />
                  </div>
                  <div className="text-xs text-text-secondary mt-1">{source.percentage}% of top sources</div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Response Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {responseMetrics.map((metric, idx) => (
            <div
              key={idx}
              className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all"
            >
              <h3 className="text-text-secondary text-sm font-medium mb-2">{metric.label}</h3>
              <div className="text-3xl font-bold text-gold">{metric.value}</div>
              <p className="text-text-secondary text-xs mt-2">{metric.unit}</p>
            </div>
          ))}
        </motion.div>

        {/* Honeypot Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="bg-surface border border-gold/20 rounded-lg p-6 hover:border-gold/40 transition-all"
        >
          <h2 className="text-lg font-orbitron text-gold font-bold mb-4">Honeypot Activity</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {honeypotMetrics.map((metric, idx) => (
              <div
                key={idx}
                className="bg-surface-darker rounded-lg p-4 border border-gold/10"
              >
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-text-secondary text-sm font-medium">{metric.type}</h3>
                  <span className="text-gold font-bold">{metric.captured}</span>
                </div>
                <div
                  className="h-2 rounded-full"
                  style={{
                    background: `linear-gradient(to right, ${metric.color}, ${metric.color}4d)`,
                  }}
                />
              </div>
            ))}
          </div>
        </motion.div>
      </main>
    </div>
  );
};

export default AnalyticsPage;
