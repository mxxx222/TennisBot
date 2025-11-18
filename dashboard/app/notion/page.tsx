'use client';

import NotionSync from '@/components/NotionSync';

export default function NotionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Notion Integration</h1>
        <p className="text-gray-600 mt-1">Sync betting opportunities and analytics to Notion</p>
      </div>

      <NotionSync />
    </div>
  );
}

