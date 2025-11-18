'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import PerformanceMetrics from '@/components/PerformanceMetrics';
import { PerformanceMetrics as MetricsType, AnalyticsData } from '@/types';
import { format } from 'date-fns';

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<MetricsType | null>(null);
  const [roiData, setRoiData] = useState<AnalyticsData[]>([]);
  const [sportData, setSportData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Fetch metrics
      const metricsRes = await fetch(`/api/analytics?period=${period}`);
      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      // Fetch ROI trend data
      const roiRes = await fetch(`/api/analytics/trend?period=${period}`);
      if (roiRes.ok) {
        const roiData = await roiRes.json();
        setRoiData(roiData.data || []);
      }

      // Fetch sport performance
      const sportRes = await fetch(`/api/analytics/sports?period=${period}`);
      if (sportRes.ok) {
        const sportData = await sportRes.json();
        setSportData(sportData.data || []);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = roiData.map((item) => ({
    date: format(new Date(item.date), 'MMM dd'),
    roi: item.roi,
    winRate: item.winRate * 100,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Performance metrics and trends</p>
        </div>
        <div className="mt-4 sm:mt-0 flex gap-2">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                period === p
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Performance Metrics */}
      <PerformanceMetrics metrics={metrics} loading={loading} />

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ROI Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">ROI Trend</h3>
          {loading ? (
            <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
          ) : chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="roi"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="ROI %"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Win Rate Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Win Rate Trend</h3>
          {loading ? (
            <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
          ) : chartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="winRate"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Win Rate %"
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Performance by Sport */}
        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Performance by Sport</h3>
          {loading ? (
            <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
          ) : sportData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sportData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="sport" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="roi" fill="#3b82f6" name="ROI %" />
                <Bar dataKey="winRate" fill="#10b981" name="Win Rate %" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Average ROI</h3>
            <p className="text-2xl font-bold text-gray-900">
              {metrics.roi >= 0 ? '+' : ''}{metrics.roi.toFixed(2)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Average Win Rate</h3>
            <p className="text-2xl font-bold text-gray-900">
              {metrics.winRate.toFixed(2)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-2">Average Edge</h3>
            <p className="text-2xl font-bold text-gray-900">
              {metrics.averageEdge >= 0 ? '+' : ''}{metrics.averageEdge.toFixed(2)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

