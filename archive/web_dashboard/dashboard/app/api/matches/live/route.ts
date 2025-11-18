import { NextResponse } from 'next/server';
import { getLiveMatches } from '@/lib/api';

export async function GET() {
  try {
    const matches = await getLiveMatches();
    return NextResponse.json({ matches });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch live matches', matches: [] },
      { status: 500 }
    );
  }
}

