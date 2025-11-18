// Type definitions for the betting dashboard

export interface BettingOpportunity {
  id: string;
  sport: 'tennis' | 'football' | 'basketball' | 'ice_hockey';
  league: string;
  match: string;
  player1?: string;
  player2?: string;
  team1?: string;
  team2?: string;
  market: string;
  selection: string;
  odds: number;
  edge: number;
  roi: number;
  confidence: number;
  riskLevel: 'low' | 'moderate' | 'high';
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  betfuryLink?: string;
  discoveredAt: string;
  matchTime?: string;
  status: 'upcoming' | 'live' | 'finished';
}

export interface PerformanceMetrics {
  totalBets: number;
  winRate: number;
  roi: number;
  totalStaked: number;
  totalProfit: number;
  averageOdds: number;
  averageEdge: number;
  period: string;
}

export interface AnalyticsData {
  roi: number;
  winRate: number;
  totalBets: number;
  date: string;
  sport?: string;
}

export interface NotionSyncStatus {
  connected: boolean;
  lastSync?: string;
  databases: {
    tennis?: string;
    football?: string;
    basketball?: string;
    ice_hockey?: string;
    roi_analysis?: string;
  };
  error?: string;
}

export interface LiveMatch {
  id: string;
  sport: string;
  league: string;
  match: string;
  status: 'upcoming' | 'live' | 'finished';
  time?: string;
  score?: string;
}

export interface SystemStatus {
  active: boolean;
  lastScan?: string;
  opportunitiesToday: number;
  systemHealth: 'healthy' | 'warning' | 'error';
}

