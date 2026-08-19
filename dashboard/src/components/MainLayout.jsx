// MainLayout.jsx
// This layout is used when rendering the dashboard as a standalone shell.
// The primary app entry point (App.jsx + Dashboard.jsx) is used in production.

import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Dashboard from "./Dashboard";
import AnalyticsPage from "./AnalyticsPage";
import LiveAttacksPage from "./LiveAttacksPage";
import HoneypotsPage from "./HoneypotsPage";
import ThreatPredictionPage from "./ThreatPredictionPage";
import SettingsPage from "./SettingsPage";

function MainLayout({ status = {}, threats = [], logs = [], analytics = {}, realTimeData = {}, onLogout = () => {} }) {
  const [activePage, setActivePage] = useState("Dashboard");

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return (
          <Dashboard
            status={status}
            threats={threats}
            logs={logs}
            analytics={analytics}
            realTimeData={realTimeData}
            onLogout={onLogout}
          />
        );
      case "Live Attacks":
        return <LiveAttacksPage />;
      case "Honeypots":
        return <HoneypotsPage />;
      case "Threat Prediction":
        return <ThreatPredictionPage />;
      case "Analytics":
        return <AnalyticsPage analytics={analytics} realTimeData={realTimeData} />;
      case "Settings":
        return <SettingsPage />;
      default:
        return (
          <Dashboard
            status={status}
            threats={threats}
            logs={logs}
            analytics={analytics}
            realTimeData={realTimeData}
            onLogout={onLogout}
          />
        );
    }
  };

  return (
    <div className="flex font-inter min-h-screen bg-dark">
      <Sidebar activeItem={activePage} onItemClick={setActivePage} onLogout={onLogout} />
      <div className="flex-1">{renderPage()}</div>
    </div>
  );
}

export default MainLayout;
