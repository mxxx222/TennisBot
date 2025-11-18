'use client';

import { BettingOpportunity } from '@/types';
import { format } from 'date-fns';
import Link from 'next/link';

interface OpportunityCardProps {
  opportunity: BettingOpportunity;
}

export default function OpportunityCard({ opportunity }: OpportunityCardProps) {
  const getROIColor = (roi: number) => {
    if (roi >= 15) return 'bg-green-100 text-green-800 border-green-300';
    if (roi >= 10) return 'bg-green-50 text-green-700 border-green-200';
    if (roi >= 5) return 'bg-yellow-50 text-yellow-700 border-yellow-200';
    return 'bg-gray-50 text-gray-700 border-gray-200';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.75) return 'bg-blue-100 text-blue-800';
    if (confidence >= 0.65) return 'bg-purple-100 text-purple-800';
    if (confidence >= 0.55) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSportIcon = (sport: string) => {
    const icons: Record<string, string> = {
      tennis: '🎾',
      football: '⚽',
      basketball: '🏀',
      ice_hockey: '🏒',
    };
    return icons[sport] || '🏆';
  };

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{getSportIcon(opportunity.sport)}</span>
              <span className="text-sm font-medium text-gray-600">{opportunity.league}</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{opportunity.match}</h3>
            <p className="text-sm text-gray-600">
              {opportunity.market} - {opportunity.selection}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${getUrgencyColor(
              opportunity.urgency
            )}`}
          >
            {opportunity.urgency}
          </span>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">ROI</p>
            <p className={`text-lg font-bold ${getROIColor(opportunity.roi).split(' ')[1]}`}>
              +{opportunity.roi.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Edge</p>
            <p className="text-lg font-bold text-gray-900">
              +{opportunity.edge.toFixed(2)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Confidence</p>
            <p
              className={`text-lg font-bold ${getConfidenceColor(opportunity.confidence).split(' ')[1]}`}
            >
              {(opportunity.confidence * 100).toFixed(0)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Odds</p>
            <p className="text-lg font-bold text-gray-900">{opportunity.odds.toFixed(2)}</p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-3">
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(
                opportunity.riskLevel
              )}`}
            >
              {opportunity.riskLevel.toUpperCase()} RISK
            </span>
            {opportunity.matchTime && (
              <span className="text-xs text-gray-500">
                {format(new Date(opportunity.matchTime), 'MMM dd, HH:mm')}
              </span>
            )}
          </div>
          {opportunity.betfuryLink && (
            <Link
              href={opportunity.betfuryLink}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              View on Betfury →
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

