import { BettingOpportunity, PerformanceMetrics, LiveMatch, SystemStatus } from '@/types';
import { readFile, readdir } from 'fs/promises';
import { join } from 'path';

const PROJECT_ROOT = process.cwd();
const DATA_DIR = join(PROJECT_ROOT, '..');

// Helper to read JSON files
async function readJSONFile(filePath: string): Promise<any> {
  try {
    const content = await readFile(filePath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error);
    return null;
  }
}

// Mock data generator for development
function generateMockOpportunities(): BettingOpportunity[] {
  const sports = ['tennis', 'football', 'basketball', 'ice_hockey'];
  const opportunities: BettingOpportunity[] = [];

  for (let i = 0; i < 10; i++) {
    const sport = sports[Math.floor(Math.random() * sports.length)];
    opportunities.push({
      id: `opp-${i}`,
      sport: sport as any,
      league: `${sport} League ${i + 1}`,
      match: `Team A vs Team B ${i + 1}`,
      market: 'Match Winner',
      selection: 'Team A',
      odds: 2.0 + Math.random() * 2,
      edge: 3 + Math.random() * 10,
      roi: 5 + Math.random() * 20,
      confidence: 0.5 + Math.random() * 0.4,
      riskLevel: ['low', 'moderate', 'high'][Math.floor(Math.random() * 3)] as any,
      urgency: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)] as any,
      discoveredAt: new Date(Date.now() - Math.random() * 3600000).toISOString(),
      status: 'upcoming',
    });
  }

  return opportunities.sort((a, b) => b.roi - a.roi);
}

export async function getOpportunities(): Promise<BettingOpportunity[]> {
  try {
    // Try to read from actual data files
    const opportunitiesFile = join(DATA_DIR, 'betting_opportunities_20251108_103141.csv');
    // For now, return mock data
    // In production, this would parse CSV or call Python API
    return generateMockOpportunities();
  } catch (error) {
    console.error('Error fetching opportunities:', error);
    return generateMockOpportunities();
  }
}

export async function getAnalytics(period: string = '30d'): Promise<PerformanceMetrics | null> {
  try {
    // Calculate days from period
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    
    // Mock analytics data
    // In production, this would read from database or call Python API
    return {
      totalBets: 150,
      winRate: 58.5,
      roi: 12.3,
      totalStaked: 5000,
      totalProfit: 615,
      averageOdds: 2.15,
      averageEdge: 5.2,
      period: `${days} days`,
    };
  } catch (error) {
    console.error('Error fetching analytics:', error);
    return null;
  }
}

export async function getAnalyticsTrend(period: string = '30d'): Promise<any> {
  try {
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    const data = [];

    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString(),
        roi: 8 + Math.random() * 10,
        winRate: 0.5 + Math.random() * 0.2,
        totalBets: Math.floor(5 + Math.random() * 10),
      });
    }

    return { data };
  } catch (error) {
    console.error('Error fetching analytics trend:', error);
    return { data: [] };
  }
}

export async function getSportPerformance(period: string = '30d'): Promise<any> {
  try {
    const sports = ['tennis', 'football', 'basketball', 'ice_hockey'];
    const data = sports.map((sport) => ({
      sport: sport.charAt(0).toUpperCase() + sport.slice(1),
      roi: 5 + Math.random() * 15,
      winRate: 50 + Math.random() * 20,
      totalBets: Math.floor(20 + Math.random() * 50),
    }));

    return { data };
  } catch (error) {
    console.error('Error fetching sport performance:', error);
    return { data: [] };
  }
}

export async function getLiveMatches(): Promise<LiveMatch[]> {
  try {
    // Try to read from live_matches.json
    const matchesFile = join(DATA_DIR, 'live_matches.json');
    const data = await readJSONFile(matchesFile);
    
    if (data && Array.isArray(data)) {
      return data.map((match: any, index: number) => ({
        id: match.id || `match-${index}`,
        sport: match.sport || 'tennis',
        league: match.league || 'Unknown League',
        match: match.match || match.name || 'Unknown Match',
        status: match.status || 'upcoming',
        time: match.time || match.matchTime,
        score: match.score,
      }));
    }

    // Return mock data
    return [
      {
        id: '1',
        sport: 'tennis',
        league: 'ATP Masters',
        match: 'Djokovic vs Alcaraz',
        status: 'live',
        score: '2-1',
      },
      {
        id: '2',
        sport: 'football',
        league: 'Premier League',
        match: 'Arsenal vs Chelsea',
        status: 'upcoming',
        time: new Date(Date.now() + 3600000).toISOString(),
      },
    ];
  } catch (error) {
    console.error('Error fetching live matches:', error);
    return [];
  }
}

export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    return {
      active: true,
      lastScan: new Date(Date.now() - 120000).toISOString(),
      opportunitiesToday: 15,
      systemHealth: 'healthy',
    };
  } catch (error) {
    console.error('Error fetching system status:', error);
    return {
      active: false,
      opportunitiesToday: 0,
      systemHealth: 'error',
    };
  }
}

