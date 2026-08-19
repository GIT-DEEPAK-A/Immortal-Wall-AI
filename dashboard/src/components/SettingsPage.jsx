import React, { useState } from "react";
import { motion } from "framer-motion";

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    adminName: "System Administrator",
    email: "admin@immortalwall.ai",
    twoFactor: true,
    role: "Admin",
    autoBlockIPs: true,
    enableThreatPrediction: true,
    enableHoneypots: true,
    threatLevel: "medium",
    aiMode: "automatic",
    modelConfidence: 85,
    continuousLearning: true,
    decoySystemsEnabled: true,
    honeypotType: "all",
    emailAlerts: true,
    smsAlerts: false,
    dashboardAlerts: true,
    alertSeverity: "high",
  });

  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [expandedSection, setExpandedSection] = useState(null);
  const [allowedIPs, setAllowedIPs] = useState(["192.168.1.0/24", "10.0.0.0/8"]);
  const [blockedIPs, setBlockedIPs] = useState(["192.168.100.50", "203.0.113.0/24"]);
  const [newIP, setNewIP] = useState("");

  const handleToggle = (key) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleInputChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSliderChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    setFeedbackMessage("✓ Configuration saved successfully");
    setTimeout(() => setFeedbackMessage(""), 3000);
  };

  const handleReset = () => {
    setFeedbackMessage("⟳ Settings reset to default values");
    setTimeout(() => setFeedbackMessage(""), 3000);
  };

  const addIP = (type) => {
    if (newIP.trim()) {
      if (type === "allowed") {
        setAllowedIPs((prev) => [...prev, newIP]);
      } else {
        setBlockedIPs((prev) => [...prev, newIP]);
      }
      setNewIP("");
    }
  };

  const removeIP = (type, index) => {
    if (type === "allowed") {
      setAllowedIPs((prev) => prev.filter((_, i) => i !== index));
    } else {
      setBlockedIPs((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const ToggleSwitch = ({ enabled, onChange }) => (
    <motion.button
      onClick={onChange}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-300 ${
        enabled ? "bg-gold/80 shadow-lg shadow-gold/40" : "bg-dark-secondary border border-gold/20"
      }`}
    >
      <motion.div
        animate={{ x: enabled ? 28 : 2 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className={`h-6 w-6 rounded-full ${enabled ? "bg-white" : "bg-text-secondary"}`}
      />
    </motion.button>
  );

  const SettingCard = ({ title, icon, children, isExpanded }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-[28px] border border-gold/15 bg-surface/80 backdrop-blur-xl overflow-hidden"
    >
      <button
        onClick={() => setExpandedSection(isExpanded ? null : title)}
        className="w-full p-5 flex items-center justify-between hover:bg-gold/5 transition-all"
      >
        <div className="flex items-center gap-4">
          <span className="text-2xl">{icon}</span>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        <svg
          className={`w-5 h-5 text-gold transition-transform duration-300 ${isExpanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </button>

      <motion.div
        initial={false}
        animate={{ height: isExpanded ? "auto" : 0 }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden border-t border-gold/10"
      >
        <div className="p-5 space-y-4">{children}</div>
      </motion.div>
    </motion.div>
  );

  const SettingRow = ({ label, children, helpText }) => (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div className="flex-1">
        <p className="text-sm font-semibold text-white">{label}</p>
        {helpText && <p className="text-xs text-text-secondary mt-1">{helpText}</p>}
      </div>
      {children}
    </div>
  );

  return (
    <div className="min-h-screen bg-dark text-text-primary font-poppins flex-1 relative overflow-hidden">
      <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_rgba(255,215,0,0.1),_transparent_60%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(10,15,28,0.85),rgba(10,15,28,0.95))] pointer-events-none" />

      <div className="relative z-10 p-6 lg:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-8 mb-8">
            <div className="space-y-3 flex-1">
              <p className="text-sm uppercase tracking-[0.3em] text-gold/80">System Configuration</p>
              <h1 className="text-4xl lg:text-5xl font-orbitron text-gold">System Settings & Configuration</h1>
              <p className="text-text-secondary max-w-2xl text-sm lg:text-base">
                Manage and customize your cyber defense system. Configure threat detection, security protocols, and AI behavior for optimal protection.
              </p>
            </div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="rounded-[28px] border border-gold/15 bg-surface/80 backdrop-blur-xl p-6 w-full lg:w-80 h-fit"
            >
              <p className="text-sm uppercase tracking-[0.3em] text-gold/70 mb-4">System Status</p>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-text-secondary">Security Level</p>
                  <p className="text-2xl font-orbitron text-green-400">High</p>
                </div>
                <div>
                  <p className="text-xs text-text-secondary">Active Protections</p>
                  <p className="text-2xl font-orbitron text-gold">5/5</p>
                </div>
                <div>
                  <p className="text-xs text-text-secondary">Last Updated</p>
                  <p className="text-xs text-text-secondary font-mono">2 min ago</p>
                </div>
              </div>
            </motion.div>
          </div>

          <div className="grid gap-4 mb-8">
            <SettingCard
              title="🔐 Account & Access Control"
              icon="🔐"
              isExpanded={expandedSection === "🔐 Account & Access Control"}
            >
              <SettingRow label="Admin Name">
                <input
                  type="text"
                  value={settings.adminName}
                  onChange={(e) => handleInputChange("adminName", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                />
              </SettingRow>

              <SettingRow label="Email Address">
                <input
                  type="email"
                  value={settings.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                />
              </SettingRow>

              <SettingRow label="Two-Factor Authentication">
                <ToggleSwitch enabled={settings.twoFactor} onChange={() => handleToggle("twoFactor")} />
              </SettingRow>

              <SettingRow label="User Role">
                <select
                  value={settings.role}
                  onChange={(e) => handleInputChange("role", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                >
                  <option>Admin</option>
                  <option>Analyst</option>
                  <option>Viewer</option>
                </select>
              </SettingRow>

              <button className="w-full mt-3 px-4 py-2 rounded-lg border border-gold/40 text-gold hover:bg-gold/10 transition-all text-sm font-semibold">
                Change Password
              </button>
            </SettingCard>

            <SettingCard
              title="🛡️ Security Settings"
              icon="🛡️"
              isExpanded={expandedSection === "🛡️ Security Settings"}
            >
              <SettingRow label="Auto Block Suspicious IPs">
                <ToggleSwitch enabled={settings.autoBlockIPs} onChange={() => handleToggle("autoBlockIPs")} />
              </SettingRow>

              <SettingRow label="Enable AI Threat Prediction">
                <ToggleSwitch
                  enabled={settings.enableThreatPrediction}
                  onChange={() => handleToggle("enableThreatPrediction")}
                />
              </SettingRow>

              <SettingRow label="Enable Honeypot Deployment">
                <ToggleSwitch enabled={settings.enableHoneypots} onChange={() => handleToggle("enableHoneypots")} />
              </SettingRow>

              <SettingRow
                label="Threat Detection Sensitivity"
                helpText="Lower = fewer alerts, Higher = more sensitive"
              >
                <div className="flex items-center gap-3">
                  <select
                    value={settings.threatLevel}
                    onChange={(e) => handleInputChange("threatLevel", e.target.value)}
                    className="px-3 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black text-sm focus:border-gold focus:outline-none"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </SettingRow>
            </SettingCard>

            <SettingCard
              title="🌐 Network & Firewall Config"
              icon="🌐"
              isExpanded={expandedSection === "🌐 Network & Firewall Config"}
            >
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <p className="text-sm font-semibold text-white">Firewall Status: Active</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold text-white mb-3">Allowed IP List</p>
                  <div className="space-y-2 mb-3">
                    {allowedIPs.map((ip, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/30"
                      >
                        <span className="text-xs text-green-300 font-mono">{ip}</span>
                        <button
                          onClick={() => removeIP("allowed", idx)}
                          className="text-xs text-green-300 hover:text-red-400 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="e.g., 192.168.1.0/24"
                      value={newIP}
                      onChange={(e) => setNewIP(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") addIP("allowed");
                      }}
                      className="flex-1 px-3 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-white text-sm focus:border-gold focus:outline-none"
                    />
                    <button
                      onClick={() => addIP("allowed")}
                      className="px-3 py-2 rounded-lg bg-green-500/20 border border-green-500/40 text-green-300 text-sm font-semibold hover:bg-green-500/30 transition-all"
                    >
                      Add
                    </button>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-semibold text-white mb-3">Blocked IP List</p>
                  <div className="space-y-2 mb-3">
                    {blockedIPs.map((ip, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30"
                      >
                        <span className="text-xs text-red-300 font-mono">{ip}</span>
                        <button
                          onClick={() => removeIP("blocked", idx)}
                          className="text-xs text-red-300 hover:text-green-400 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="e.g., 203.0.113.0/24"
                      value={newIP}
                      onChange={(e) => setNewIP(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") addIP("blocked");
                      }}
                      className="flex-1 px-3 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-white text-sm focus:border-gold focus:outline-none"
                    />
                    <button
                      onClick={() => addIP("blocked")}
                      className="px-3 py-2 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300 text-sm font-semibold hover:bg-red-500/30 transition-all"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>
            </SettingCard>

            <SettingCard
              title="🤖 AI Configuration Panel"
              icon="🤖"
              isExpanded={expandedSection === "🤖 AI Configuration Panel"}
            >
              <SettingRow label="AI Mode">
                <select
                  value={settings.aiMode}
                  onChange={(e) => handleInputChange("aiMode", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                >
                  <option value="automatic">Automatic</option>
                  <option value="manual">Manual</option>
                </select>
              </SettingRow>

              <SettingRow
                label="Model Confidence Threshold"
                helpText={`Current: ${settings.modelConfidence}%`}
              >
                <div className="flex items-center gap-3 flex-1 max-w-xs">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.modelConfidence}
                    onChange={(e) => handleSliderChange("modelConfidence", parseInt(e.target.value))}
                    className="flex-1 h-2 bg-dark-secondary rounded-lg appearance-none cursor-pointer accent-gold"
                  />
                  <span className="text-sm font-semibold text-gold w-12 text-right">{settings.modelConfidence}%</span>
                </div>
              </SettingRow>

              <SettingRow label="Enable Continuous Learning">
                <ToggleSwitch
                  enabled={settings.continuousLearning}
                  onChange={() => handleToggle("continuousLearning")}
                />
              </SettingRow>
            </SettingCard>

            <SettingCard
              title="🪤 Honeypot Settings"
              icon="🪤"
              isExpanded={expandedSection === "🪤 Honeypot Settings"}
            >
              <SettingRow label="Enable Decoy Systems">
                <ToggleSwitch
                  enabled={settings.decoySystemsEnabled}
                  onChange={() => handleToggle("decoySystemsEnabled")}
                />
              </SettingRow>

              <SettingRow label="Honeypot Type">
                <select
                  value={settings.honeypotType}
                  onChange={(e) => handleInputChange("honeypotType", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                >
                  <option value="all">All Types</option>
                  <option value="admin">Admin Panel</option>
                  <option value="database">Database</option>
                  <option value="api">API Endpoint</option>
                </select>
              </SettingRow>

              <SettingRow label="Auto-Deploy Based on Threat" helpText="Automatically deploy honeypots when high-level threats detected">
                <ToggleSwitch enabled={true} onChange={() => {}} />
              </SettingRow>
            </SettingCard>

            <SettingCard
              title="🔔 Notifications & Alerts"
              icon="🔔"
              isExpanded={expandedSection === "🔔 Notifications & Alerts"}
            >
              <SettingRow label="Email Alerts">
                <ToggleSwitch enabled={settings.emailAlerts} onChange={() => handleToggle("emailAlerts")} />
              </SettingRow>

              <SettingRow label="SMS Alerts">
                <ToggleSwitch enabled={settings.smsAlerts} onChange={() => handleToggle("smsAlerts")} />
              </SettingRow>

              <SettingRow label="Real-Time Dashboard Alerts">
                <ToggleSwitch enabled={settings.dashboardAlerts} onChange={() => handleToggle("dashboardAlerts")} />
              </SettingRow>

              <SettingRow label="Alert Severity Filter">
                <select
                  value={settings.alertSeverity}
                  onChange={(e) => handleInputChange("alertSeverity", e.target.value)}
                  className="px-4 py-2 rounded-lg bg-dark-secondary border border-gold/20 text-black focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold/30 transition-all"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical Only</option>
                </select>
              </SettingRow>
            </SettingCard>
          </div>

          {feedbackMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="fixed bottom-8 right-8 px-6 py-3 rounded-lg bg-gold/80 text-dark font-semibold text-sm shadow-lg shadow-gold/40 flex items-center gap-2"
            >
          {feedbackMessage.includes("✓") ? (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )}
              {feedbackMessage}
            </motion.div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 mt-10">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSave}
              className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-gold to-yellow-500 text-dark font-semibold text-sm uppercase tracking-[0.3em] hover:shadow-lg hover:shadow-gold/40 transition-all flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.3A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z" />
              </svg>
              Save Configuration
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleReset}
              className="px-6 py-3 rounded-lg border-2 border-red-500/50 text-red-400 font-semibold text-sm uppercase tracking-[0.3em] hover:bg-red-500/10 transition-all flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Reset to Default
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
