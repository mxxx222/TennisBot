import { NextResponse } from 'next/server';
import { getOpportunities } from '@/lib/api';

export async function GET() {
  try {
    const opportunities = await getOpportunities();
    return NextResponse.json({ opportunities });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch opportunities', opportunities: [] },
      { status: 500 }
    );
  }
}

