'use client';

import { useState, useEffect } from 'react';
import { NotionSyncStatus } from '@/types';
import { format } from 'date-fns';

export default function NotionSync() {
  const [status, setStatus] = useState<NotionSyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/notion/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Error fetching Notion status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncResult(null);

      // Fetch opportunities to sync
      const oppRes = await fetch('/api/opportunities');
      if (!oppRes.ok) {
        throw new Error('Failed to fetch opportunities');
      }

      const oppData = await oppRes.json();
      const opportunities = oppData.opportunities || [];

      if (opportunities.length === 0) {
        setSyncResult({
          success: false,
          error: 'No opportunities to sync',
        });
        return;
      }

      // Sync to Notion
      const syncRes = await fetch('/api/notion/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          opportunities: opportunities.slice(0, 10), // Limit to 10 for now
        }),
      });

      const syncData = await syncRes.json();
      setSyncResult(syncData);

      // Refresh status
      await fetchStatus();
    } catch (error: any) {
      setSyncResult({
        success: false,
        error: error.message || 'Failed to sync',
      });
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const connected = status?.connected || false;
  const databaseCount = Object.keys(status?.databases || {}).length;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Notion Integration</h2>
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
            connected
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {status?.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{status.error}</p>
        </div>
      )}

      {connected && (
        <>
          <div className="space-y-3 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Databases Found</span>
              <span className="font-semibold">{databaseCount}</span>
            </div>
            {status.lastSync && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Last Sync</span>
                <span className="text-sm font-medium">
                  {format(new Date(status.lastSync), 'MMM dd, HH:mm')}
                </span>
              </div>
            )}
            {databaseCount > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Connected Databases:</p>
                <div className="space-y-1">
                  {Object.entries(status.databases).map(([key, id]) => (
                    <div key={key} className="flex items-center gap-2 text-sm">
                      <span className="text-gray-500">•</span>
                      <span className="capitalize">{key.replace('_', ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={handleSync}
            disabled={syncing || databaseCount === 0}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing ? 'Syncing...' : '🔄 Sync Opportunities to Notion'}
          </button>

          {syncResult && (
            <div
              className={`mt-4 p-3 rounded-lg ${
                syncResult.success
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              {syncResult.success ? (
                <div>
                  <p className="text-sm font-medium text-green-800 mb-1">
                    ✅ Sync Successful
                  </p>
                  <p className="text-xs text-green-700">
                    Synced {syncResult.synced} of {syncResult.total} opportunities
                    {syncResult.failed > 0 && ` (${syncResult.failed} failed)`}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-red-800">
                  ❌ {syncResult.error || 'Sync failed'}
                </p>
              )}
            </div>
          )}
        </>
      )}

      {!connected && (
        <div className="text-sm text-gray-600">
          <p className="mb-2">To connect Notion:</p>
          <ol className="list-decimal list-inside space-y-1 text-xs">
            <li>Create a Notion integration at notion.so/my-integrations</li>
            <li>Copy the integration token</li>
            <li>Add it as NOTION_TOKEN in your environment variables</li>
            <li>Share your Notion databases with the integration</li>
          </ol>
        </div>
      )}
    </div>
  );
}

