import { NextRequest, NextResponse } from 'next/server';
import { getAnalyticsTrend } from '@/lib/api';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const period = searchParams.get('period') || '30d';
    
    const data = await getAnalyticsTrend(period);
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch trend data', data: [] },
      { status: 500 }
    );
  }
}

