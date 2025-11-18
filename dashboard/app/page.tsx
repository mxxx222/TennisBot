'use client';

import { useEffect, useState } from 'react';
import PerformanceMetrics from '@/components/PerformanceMetrics';
import LiveMatches from '@/components/LiveMatches';
import { PerformanceMetrics as MetricsType, SystemStatus, LiveMatch } from '@/types';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricsType | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch metrics
      const metricsRes = await fetch('/api/analytics?period=today');
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      // Fetch system status
      const statusRes = await fetch('/api/system/status');
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setSystemStatus(statusData);
      }

      // Fetch live matches
      const matchesRes = await fetch('/api/matches/live');
      if (matchesRes.ok) {
        const matchesData = await matchesRes.json();
        setLiveMatches(matchesData.matches || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSystemStatusColor = (health?: string) => {
    switch (health) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time betting intelligence overview</p>
        </div>
        {systemStatus && (
          <div className="mt-4 sm:mt-0">
            <div
              className={`inline-flex items-center px-4 py-2 rounded-lg border ${getSystemStatusColor(
                systemStatus.systemHealth
              )}`}
            >
              <span
                className={`w-2 h-2 rounded-full mr-2 ${
                  systemStatus.active ? 'bg-green-500' : 'bg-gray-400'
                }`}
              />
              <span className="text-sm font-medium">
                {systemStatus.active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      <PerformanceMetrics metrics={metrics} loading={loading} />

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Today's Opportunities</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {systemStatus?.opportunitiesToday || 0}
              </p>
            </div>
            <span className="text-3xl">💰</span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Matches</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {liveMatches.filter((m) => m.status === 'live').length}
              </p>
            </div>
            <span className="text-3xl">⚡</span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Last Scan</p>
              <p className="text-sm font-semibold text-gray-900 mt-1">
                {systemStatus?.lastScan
                  ? new Date(systemStatus.lastScan).toLocaleTimeString()
                  : 'Never'}
              </p>
            </div>
            <span className="text-3xl">🔄</span>
          </div>
        </div>
      </div>

      {/* Live Matches */}
      <LiveMatches matches={liveMatches} loading={loading} />
    </div>
  );
}

