'use client';

import { LiveMatch } from '@/types';
import { format } from 'date-fns';

interface LiveMatchesProps {
  matches: LiveMatch[];
  loading?: boolean;
}

export default function LiveMatches({ matches, loading }: LiveMatchesProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Live Matches</h2>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!matches || matches.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Live Matches</h2>
        <p className="text-gray-500 text-center py-8">No live matches at the moment</p>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'upcoming':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'finished':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
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
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Live Matches</h2>
      <div className="space-y-3">
        {matches.slice(0, 10).map((match) => (
          <div
            key={match.id}
            className="border rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{getSportIcon(match.sport)}</span>
                  <span className="text-sm font-medium text-gray-600">{match.league}</span>
                </div>
                <p className="font-semibold text-gray-900">{match.match}</p>
                {match.score && (
                  <p className="text-sm text-gray-600 mt-1">Score: {match.score}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                    match.status
                  )}`}
                >
                  {match.status.toUpperCase()}
                </span>
                {match.time && (
                  <span className="text-xs text-gray-500">
                    {format(new Date(match.time), 'HH:mm')}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

