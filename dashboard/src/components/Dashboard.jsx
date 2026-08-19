import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Sidebar from "./Sidebar";
import StatusCards from "./StatusCards";
import GlobeVisualization from "./GlobeVisualization";
import ThreatAlerts from "./ThreatAlerts";
import HoneypotCards from "./HoneypotCards";
import TerminalLogs from "./TerminalLogs";
import ThreatPredictionPage from "./ThreatPredictionPage";
import HoneypotsPage from "./HoneypotsPage";
import LiveAttacksPage from "./LiveAttacksPage";
import AnalyticsPage from "./AnalyticsPage";
import SettingsPage from "./SettingsPage";

const Dashboard = ({ status, threats, logs, analytics, realTimeData, onLogout }) => {
  const [activePage, setActivePage] = useState("Dashboard");

  const handlePageChange = (pageName) => {
    setActivePage(pageName);
  };

  const renderContent = () => {
    switch (activePage) {
      case "Dashboard":
        return (
          <div className="flex-1 flex flex-col">
            <main className="flex-1 p-6 space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <StatusCards status={status} threats={threats} logs={logs} />
              </motion.div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  className="lg:col-span-2"
                >
                  <GlobeVisualization />
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  <ThreatAlerts threats={threats} />
                </motion.div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.6 }}
                >
                  <HoneypotCards />
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.8 }}
                >
                  <TerminalLogs logs={logs} />
                </motion.div>
              </div>
            </main>
          </div>
        );

      case "Threat Prediction":
        return <ThreatPredictionPage onLogout={onLogout} />;

      case "Honeypots":
        return <HoneypotsPage />;

      case "Live Attacks":
        return <LiveAttacksPage />;

      case "Analytics":
        return <AnalyticsPage analytics={analytics} realTimeData={realTimeData} />;

      case "Settings":
        return <SettingsPage />;

      default:
        return (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl text-gold font-orbitron mb-4">{activePage}</h2>
              <p className="text-text-secondary">This feature is coming soon...</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-dark text-text-primary font-poppins flex">
      <Sidebar activeItem={activePage} onItemClick={handlePageChange} onLogout={onLogout} />

      <AnimatePresence mode="wait">
        <motion.div
          key={activePage}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="flex-1"
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;