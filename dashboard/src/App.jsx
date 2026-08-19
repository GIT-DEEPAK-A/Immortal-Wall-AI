import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import SplashScreen from "./components/SplashScreen";
import LoginPage    from "./components/LoginPage";
import Dashboard    from "./components/Dashboard";

const API = "http://localhost:8000";

/* ─────────────────────────────────────────────
   App — manages the three-phase flow:
     splash  →  login  →  dashboard
───────────────────────────────────────────── */
function App() {
  // "splash" | "login" | "dashboard"
  const [phase, setPhase] = useState("splash");

  // Dashboard data
  const [status,       setStatus]       = useState({});
  const [threats,      setThreats]      = useState([]);
  const [logs,         setLogs]         = useState([]);
  const [analytics,    setAnalytics]    = useState({});
  const [realTimeData, setRealTimeData] = useState({
    activeConnections: 0,
    threatsPerMinute:  0,
    systemLoad:        "normal",
  });

  const wsRef              = useRef(null);
  const reconnectTimer     = useRef(null);
  const reconnectAttempts  = useRef(0);
  const MAX_RECONNECT      = 10;

  /* ── WebSocket ──────────────────────────────────── */
  const connectWS = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    try {
      const ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WS] connected");
        reconnectAttempts.current = 0;
      };

      ws.onmessage = ({ data }) => {
        try {
          const msg = JSON.parse(data);
          switch (msg.type) {
            case "system_status":
              setStatus((prev) => ({ ...prev, ...msg.data, lastUpdate: new Date().toISOString() }));
              setRealTimeData({
                activeConnections: msg.data.system_metrics?.active_connections ?? 0,
                threatsPerMinute:  msg.data.system_metrics?.threats_per_minute  ?? 0,
                systemLoad:        msg.data.system_metrics?.system_load          ?? "normal",
              });
              break;
            case "new_threat":
              setThreats((prev) => [msg.data, ...prev.slice(0, 49)]);
              break;
            case "new_threats":
              setThreats((prev) => [...msg.data, ...prev.slice(0, 40)]);
              break;
            default:
              break;
          }
        } catch { /* ignore malformed */ }
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (reconnectAttempts.current < MAX_RECONNECT) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30_000);
          reconnectAttempts.current += 1;
          reconnectTimer.current = setTimeout(connectWS, delay);
        }
      };

      ws.onerror = () => { /* handled by onclose */ };
    } catch (e) {
      console.error("[WS] setup error:", e);
    }
  };

  const disconnectWS = () => {
    wsRef.current?.close();
    wsRef.current = null;
    clearTimeout(reconnectTimer.current);
  };

  /* ── REST fetch on login ────────────────────────── */
  const fetchInitialData = async () => {
    try {
      const [statusRes, threatsRes, logsRes, analyticsRes] = await Promise.allSettled([
        axios.get(`${API}/api/system-status`),
        axios.get(`${API}/api/threats?limit=50`),
        axios.get(`${API}/api/logs?limit=100`),
        axios.get(`${API}/api/analytics?timeframe=24h`),
      ]);

      if (statusRes.status   === "fulfilled") setStatus(statusRes.value.data);
      if (threatsRes.status  === "fulfilled") setThreats(threatsRes.value.data.threats  ?? []);
      if (logsRes.status     === "fulfilled") setLogs(logsRes.value.data.logs           ?? []);
      if (analyticsRes.status === "fulfilled") setAnalytics(analyticsRes.value.data);

      const sm = statusRes.value?.data?.system_metrics;
      if (sm) setRealTimeData({
        activeConnections: sm.active_connections ?? 0,
        threatsPerMinute:  sm.threats_per_minute  ?? 0,
        systemLoad:        sm.system_load          ?? "normal",
      });
    } catch (e) {
      console.warn("[App] initial fetch failed:", e.message);
    }
  };

  /* ── Effect: connect WS and poll when in dashboard phase ── */
  useEffect(() => {
    if (phase !== "dashboard") { disconnectWS(); return; }

    fetchInitialData();
    connectWS();
    const poll = setInterval(fetchInitialData, 30_000);

    return () => {
      clearInterval(poll);
      disconnectWS();
    };
  }, [phase]);

  /* ── Cleanup on unmount ── */
  useEffect(() => () => disconnectWS(), []);

  /* ── Render ── */
  if (phase === "splash")    return <SplashScreen onEnter={() => setPhase("login")} />;
  if (phase === "login")     return <LoginPage    onLogin={() => setPhase("dashboard")} />;

  return (
    <Dashboard
      status={status}
      threats={threats}
      logs={logs}
      analytics={analytics}
      realTimeData={realTimeData}
      onLogout={() => setPhase("login")}
    />
  );
}

export default App;
