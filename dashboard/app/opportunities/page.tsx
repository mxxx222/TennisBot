'use client';

import { useEffect, useState } from 'react';
import OpportunityCard from '@/components/OpportunityCard';
import { BettingOpportunity } from '@/types';

type SortOption = 'roi' | 'confidence' | 'edge' | 'time';
type FilterSport = 'all' | 'tennis' | 'football' | 'basketball' | 'ice_hockey';

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<BettingOpportunity[]>([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState<BettingOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>('roi');
  const [sportFilter, setSportFilter] = useState<FilterSport>('all');
  const [minROI, setMinROI] = useState(5);
  const [minConfidence, setMinConfidence] = useState(0.5);

  useEffect(() => {
    fetchOpportunities();
    const interval = setInterval(fetchOpportunities, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filterAndSortOpportunities();
  }, [opportunities, sortBy, sportFilter, minROI, minConfidence]);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/opportunities');
      if (res.ok) {
        const data = await res.json();
        setOpportunities(data.opportunities || []);
      }
    } catch (error) {
      console.error('Error fetching opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortOpportunities = () => {
    let filtered = [...opportunities];

    // Sport filter
    if (sportFilter !== 'all') {
      filtered = filtered.filter((opp) => opp.sport === sportFilter);
    }

    // ROI filter
    filtered = filtered.filter((opp) => opp.roi >= minROI);

    // Confidence filter
    filtered = filtered.filter((opp) => opp.confidence >= minConfidence);

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'roi':
          return b.roi - a.roi;
        case 'confidence':
          return b.confidence - a.confidence;
        case 'edge':
          return b.edge - a.edge;
        case 'time':
          return (
            new Date(b.discoveredAt).getTime() - new Date(a.discoveredAt).getTime()
          );
        default:
          return 0;
      }
    });

    setFilteredOpportunities(filtered);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Betting Opportunities</h1>
          <p className="text-gray-600 mt-1">
            {filteredOpportunities.length} opportunities found
          </p>
        </div>
        <button
          onClick={fetchOpportunities}
          disabled={loading}
          className="mt-4 sm:mt-0 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Sport Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sport</label>
            <select
              value={sportFilter}
              onChange={(e) => setSportFilter(e.target.value as FilterSport)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">All Sports</option>
              <option value="tennis">🎾 Tennis</option>
              <option value="football">⚽ Football</option>
              <option value="basketball">🏀 Basketball</option>
              <option value="ice_hockey">🏒 Ice Hockey</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="roi">ROI (Highest)</option>
              <option value="confidence">Confidence (Highest)</option>
              <option value="edge">Edge (Highest)</option>
              <option value="time">Time (Newest)</option>
            </select>
          </div>

          {/* Min ROI */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min ROI: {minROI}%
            </label>
            <input
              type="range"
              min="0"
              max="30"
              value={minROI}
              onChange={(e) => setMinROI(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Min Confidence */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Confidence: {(minConfidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={minConfidence * 100}
              onChange={(e) => setMinConfidence(Number(e.target.value) / 100)}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : filteredOpportunities.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">No opportunities match your filters</p>
          <button
            onClick={() => {
              setSportFilter('all');
              setMinROI(0);
              setMinConfidence(0);
            }}
            className="mt-4 text-primary-600 hover:text-primary-700"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredOpportunities.map((opportunity) => (
            <OpportunityCard key={opportunity.id} opportunity={opportunity} />
          ))}
        </div>
      )}
    </div>
  );
}

