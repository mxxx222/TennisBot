import { NextRequest, NextResponse } from 'next/server';
import { syncMultipleOpportunities, getNotionStatus } from '@/lib/notion';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { opportunities, databaseType } = body;

    if (!opportunities || !Array.isArray(opportunities)) {
      return NextResponse.json(
        { error: 'Invalid opportunities data' },
        { status: 400 }
      );
    }

    // Get Notion status to find database ID
    const status = await getNotionStatus();
    
    if (!status.connected) {
      return NextResponse.json(
        { error: 'Notion not connected', status },
        { status: 400 }
      );
    }

    // Determine database ID based on type or first opportunity's sport
    let databaseId: string | undefined;
    
    if (databaseType && status.databases[databaseType as keyof typeof status.databases]) {
      databaseId = status.databases[databaseType as keyof typeof status.databases];
    } else if (opportunities.length > 0) {
      const sport = opportunities[0].sport;
      const sportKey = sport === 'ice_hockey' ? 'ice_hockey' : sport;
      databaseId = status.databases[sportKey as keyof typeof status.databases];
    }

    if (!databaseId) {
      return NextResponse.json(
        { error: 'Database not found. Please create the database in Notion first.' },
        { status: 404 }
      );
    }

    // Sync opportunities
    const result = await syncMultipleOpportunities(opportunities, databaseId);

    return NextResponse.json({
      success: true,
      synced: result.success,
      failed: result.failed,
      total: opportunities.length,
      lastSync: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to sync to Notion' },
      { status: 500 }
    );
  }
}

