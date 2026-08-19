/**
 * api.js — Axios instance factory.
 *
 * Creates one axios instance per session with the JWT pre-attached as the
 * default Authorization header.  A response interceptor automatically routes
 * 401 responses back to the login screen by calling onLogout().
 *
 * Usage in components:
 *   import api from "../api";   // get the singleton set at login
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

// Module-level singleton — replaced on every login, cleared on logout.
let _apiInstance = null;

/**
 * Create (or recreate) the axios instance and attach the bearer token.
 * Called once by App.jsx immediately after a successful login.
 *
 * @param {string}   token     JWT returned by /api/auth/login
 * @param {Function} onLogout  Callback invoked on any 401 response
 * @returns {import("axios").AxiosInstance}
 */
export function createApiClient(token, onLogout) {
  const instance = axios.create({
    baseURL: BASE_URL,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  // On every 401, clear auth state and route back to login
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        console.warn("[API] 401 received — logging out");
        onLogout();
      }
      return Promise.reject(error);
    }
  );

  _apiInstance = instance;
  return instance;
}

/**
 * Update the token on the existing instance (e.g. after token refresh).
 * @param {string} token
 */
export function setAuthToken(token) {
  if (_apiInstance) {
    _apiInstance.defaults.headers["Authorization"] = `Bearer ${token}`;
  }
}

/**
 * Return the current API instance.
 * Components should receive it as a prop from App.jsx rather than calling
 * this directly, so they always have the latest instance.
 */
export default function getApi() {
  return _apiInstance;
}
