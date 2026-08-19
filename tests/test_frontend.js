import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import App from '../src/App';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
  readyState: 1, // OPEN
}));

describe('Immortal Wall AI Dashboard', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock API responses
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/api/system-status')) {
        return Promise.resolve({
          data: {
            threats: {
              total_threats: 150,
              recent_threats_24h: 23,
              blocked_threats: 45,
              average_threat_score: 0.67
            },
            recent_threats: [
              {
                id: 1,
                timestamp: '2024-01-01T10:00:00Z',
                ip_address: '192.168.1.100',
                threat_level: 'malicious',
                threat_score: 0.95,
                description: 'Brute force attack detected'
              }
            ],
            system_metrics: {
              active_connections: 5,
              threats_per_minute: 2.3,
              system_load: 'normal'
            }
          }
        });
      } else if (url.includes('/api/threats')) {
        return Promise.resolve({
          data: {
            threats: [
              {
                id: 1,
                timestamp: '2024-01-01T10:00:00Z',
                ip_address: '192.168.1.100',
                threat_level: 'malicious',
                threat_score: 0.95,
                blocked: true
              }
            ],
            total: 1
          }
        });
      } else if (url.includes('/api/analytics')) {
        return Promise.resolve({
          data: {
            threat_trends: [
              { hour: '2024-01-01 10:00:00', count: 15 },
              { hour: '2024-01-01 11:00:00', count: 23 },
              { hour: '2024-01-01 12:00:00', count: 18 }
            ],
            top_threat_sources: [
              { ip: '192.168.1.100', count: 45 },
              { ip: '10.0.0.50', count: 32 }
            ],
            threat_distribution: {
              malicious: 45,
              suspicious: 32,
              normal: 73
            }
          }
        });
      }
      return Promise.resolve({ data: [] });
    });
  });

  test('renders login page initially', () => {
    render(<App />);
    expect(screen.getByText(/Immortal Wall AI/i)).toBeInTheDocument();
  });

  test('loads dashboard after login', async () => {
    render(<App />);

    // Simulate login
    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Security Status/i)).toBeInTheDocument();
    });

    // Check if status cards are rendered with real data
    expect(screen.getByText('150')).toBeInTheDocument(); // Total threats
    expect(screen.getByText('23')).toBeInTheDocument(); // Recent threats
  });

  test('displays real-time threat data', async () => {
    render(<App />);

    // Simulate login
    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    await waitFor(() => {
      expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
    });

    expect(screen.getByText('Brute force attack detected')).toBeInTheDocument();
  });

  test('shows analytics data', async () => {
    render(<App />);

    // Simulate login
    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    await waitFor(() => {
      // Navigate to analytics (this would need to be implemented)
      // For now, just check that the component can handle the data
      expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/analytics?timeframe=24h');
    });
  });

  test('handles API errors gracefully', async () => {
    // Mock API failure
    mockedAxios.get.mockRejectedValue(new Error('API Error'));

    render(<App />);

    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    // Should still render dashboard with fallback data
    await waitFor(() => {
      expect(screen.getByText(/Security Status/i)).toBeInTheDocument();
    });
  });

  test('WebSocket connection is established', async () => {
    render(<App />);

    const loginButton = screen.getByRole('button', { name: /login/i });
    loginButton.click();

    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws');
    });
  });
});