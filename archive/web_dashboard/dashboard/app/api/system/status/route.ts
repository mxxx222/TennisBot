import { NextResponse } from 'next/server';
import { getSystemStatus } from '@/lib/api';

export async function GET() {
  try {
    const status = await getSystemStatus();
    return NextResponse.json(status);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch system status' },
      { status: 500 }
    );
  }
}

