'use client';

import { PerformanceMetrics as MetricsType } from '@/types';

interface PerformanceMetricsProps {
  metrics: MetricsType | null;
  loading?: boolean;
}

export default function PerformanceMetrics({ metrics, loading }: PerformanceMetricsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        No metrics available
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getROIColor = (roi: number) => {
    if (roi >= 15) return 'text-green-600';
    if (roi >= 10) return 'text-green-500';
    if (roi >= 5) return 'text-yellow-500';
    if (roi >= 0) return 'text-gray-600';
    return 'text-red-600';
  };

  const cards = [
    {
      title: 'Total ROI',
      value: formatPercentage(metrics.roi),
      color: getROIColor(metrics.roi),
      icon: '📈',
    },
    {
      title: 'Win Rate',
      value: formatPercentage(metrics.winRate),
      color: metrics.winRate >= 50 ? 'text-green-600' : 'text-red-600',
      icon: '🎯',
    },
    {
      title: 'Total Profit',
      value: formatCurrency(metrics.totalProfit),
      color: metrics.totalProfit >= 0 ? 'text-green-600' : 'text-red-600',
      icon: '💰',
    },
    {
      title: 'Total Bets',
      value: metrics.totalBets.toString(),
      color: 'text-gray-700',
      icon: '📊',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{card.icon}</span>
            <span className="text-xs text-gray-500">{metrics.period}</span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">{card.title}</h3>
          <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
          {index === 2 && (
            <p className="text-xs text-gray-500 mt-2">
              Staked: {formatCurrency(metrics.totalStaked)}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

