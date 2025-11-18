import { NextResponse } from 'next/server';
import { getNotionStatus } from '@/lib/notion';

export async function GET() {
  try {
    const status = await getNotionStatus();
    return NextResponse.json(status);
  } catch (error: any) {
    return NextResponse.json(
      {
        connected: false,
        error: error.message || 'Failed to get Notion status',
        databases: {},
      },
      { status: 500 }
    );
  }
}

