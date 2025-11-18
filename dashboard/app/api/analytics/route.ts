import { NextRequest, NextResponse } from 'next/server';
import { getAnalytics } from '@/lib/api';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const period = searchParams.get('period') || '30d';
    
    const metrics = await getAnalytics(period);
    return NextResponse.json(metrics);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch analytics' },
      { status: 500 }
    );
  }
}

