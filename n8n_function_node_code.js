/**
 * n8n Function Node Code - Tennis ROI Analysis & Data Processing
 * 
 * This code processes tennis match data from Tennis API v2.9.4 and performs:
 * - ROI analysis based on odds and statistics
 * - Profitability flag calculation
 * - Insight generation
 * - Data aggregation from multiple sources
 * 
 * Usage: Copy this code into an n8n Code/Function node
 */

// Combine all data and perform ROI analysis
// This function processes data from multiple parallel HTTP requests
const items = $input.all();

// Identify data sources by checking JSON structure
let fixtureData = {};
let oddsData = {};
let h2hData = {};
let player1Data = {};
let player2Data = {};

// Find fixture data (from Split In Batches - has event_key)
const fixtureItem = items.find(item => item.json.event_key);
if (fixtureItem) {
  fixtureData = fixtureItem.json;
}

// Find odds data (has result object with match_key)
const oddsItem = items.find(item => {
  if (item.json.result && fixtureData.event_key) {
    return item.json.result[fixtureData.event_key] !== undefined;
  }
  return false;
});
if (oddsItem) {
  oddsData = oddsItem.json;
}

// Find H2H data (has result.H2H array)
const h2hItem = items.find(item => item.json.result && item.json.result.H2H !== undefined);
if (h2hItem) {
  h2hData = h2hItem.json;
}

// Find player data (has result array with player_key)
const playerItems = items.filter(item => {
  return item.json.result && Array.isArray(item.json.result) && item.json.result.length > 0;
});

if (playerItems.length > 0) {
  // First player data
  const p1Item = playerItems.find(item => 
    item.json.result[0] && item.json.result[0].player_key === fixtureData.first_player_key
  ) || playerItems[0];
  if (p1Item) player1Data = p1Item.json;
  
  // Second player data
  const p2Item = playerItems.find(item => 
    item.json.result[0] && item.json.result[0].player_key === fixtureData.second_player_key
  ) || playerItems[1];
  if (p2Item) player2Data = p2Item.json;
}

// Extract odds from multiple bookmakers
let odds = [];
if (oddsData.result && oddsData.result[fixtureData.event_key]) {
  const matchOdds = oddsData.result[fixtureData.event_key];
  
  if (matchOdds['Home/Away']) {
    const homeOdds = matchOdds['Home/Away'].Home || {};
    const awayOdds = matchOdds['Home/Away'].Away || {};
    
    // Aggregate odds from multiple bookmakers
    const homeOddsValues = Object.values(homeOdds)
      .map(v => parseFloat(v))
      .filter(v => !isNaN(v) && v > 0);
    
    const awayOddsValues = Object.values(awayOdds)
      .map(v => parseFloat(v))
      .filter(v => !isNaN(v) && v > 0);
    
    if (homeOddsValues.length > 0) {
      const homeMean = homeOddsValues.reduce((a, b) => a + b, 0) / homeOddsValues.length;
      const homeBest = Math.max(...homeOddsValues);
      const homeMedian = [...homeOddsValues].sort((a, b) => a - b)[Math.floor(homeOddsValues.length / 2)];
      const homeStdev = Math.sqrt(
        homeOddsValues.reduce((sum, val) => sum + Math.pow(val - homeMean, 2), 0) / homeOddsValues.length
      );
      
      odds.push({
        outcome: 'Home',
        odd: homeMean.toFixed(2),
        bestPrice: homeBest.toFixed(2),
        median: homeMedian.toFixed(2),
        stdev: homeStdev.toFixed(3),
        books: homeOddsValues.length
      });
    }
    
    if (awayOddsValues.length > 0) {
      const awayMean = awayOddsValues.reduce((a, b) => a + b, 0) / awayOddsValues.length;
      const awayBest = Math.max(...awayOddsValues);
      const awayMedian = [...awayOddsValues].sort((a, b) => a - b)[Math.floor(awayOddsValues.length / 2)];
      const awayStdev = Math.sqrt(
        awayOddsValues.reduce((sum, val) => sum + Math.pow(val - awayMean, 2), 0) / awayOddsValues.length
      );
      
      odds.push({
        outcome: 'Away',
        odd: awayMean.toFixed(2),
        bestPrice: awayBest.toFixed(2),
        median: awayMedian.toFixed(2),
        stdev: awayStdev.toFixed(3),
        books: awayOddsValues.length
      });
    }
  }
}

// Extract player stats (adjust based on actual API response structure)
const stats = {
  homeService: {
    firstServeSuccess: 0,
    breakPointsConverted: 0
  },
  awayService: {
    firstServeSuccess: 0,
    breakPointsConverted: 0
  }
};

// Try to extract stats from player data
// Note: Adjust field names based on actual Tennis API v2.9.4 response structure
if (player1Data.result && player1Data.result[0] && player1Data.result[0].stats) {
  const playerStats = player1Data.result[0].stats[0] || {};
  // Map stats if available (adjust field names based on actual API)
  // Example: stats.homeService.firstServeSuccess = playerStats.serve_percentage || 70;
  stats.homeService.firstServeSuccess = 70; // Default, replace with actual data
  stats.homeService.breakPointsConverted = 0;
}

if (player2Data.result && player2Data.result[0] && player2Data.result[0].stats) {
  const playerStats = player2Data.result[0].stats[0] || {};
  stats.awayService.firstServeSuccess = 70; // Default, replace with actual data
  stats.awayService.breakPointsConverted = 0;
}

// Calculate ROI and insights using the user's provided pattern
return items.map(({json}) => {
  // Use fixture data as base, merge with other data sources
  const matchData = fixtureData.event_key ? fixtureData : json;
  
  // Extract odds for this match
  const impliedHome = odds.find(o => o.outcome === 'Home')?.odd || null;
  const profitabilityFlag = impliedHome && stats.homeService.firstServeSuccess > 70;

  // Calculate Expected Value (EV)
  let ev = 0;
  if (impliedHome && stats.homeService.firstServeSuccess > 70) {
    const impliedP = 1 / parseFloat(impliedHome);
    const bestPrice = parseFloat(odds.find(o => o.outcome === 'Home')?.bestPrice || impliedHome);
    ev = (impliedP * bestPrice - 1) * 100; // As percentage
  }

  // Build insight object using user's pattern
  const insight = {
    edgeSummary: profitabilityFlag ? 'Home serve edge' : 'No statistical edge',
    roiEst: profitabilityFlag ? (parseFloat(impliedHome) - 1).toFixed(2) : '0.00',
    ev: ev.toFixed(2),
    keyDrivers: [
      `1st serve %: ${stats.homeService.firstServeSuccess || 'N/A'}`,
      `Break conversions: ${stats.homeService.breakPointsConverted || 'N/A'}`
    ],
    riskNotes: [
      matchData.event_status !== 'Finished' ? 'Live score may change' : 'Final result confirmed',
      odds.length === 0 ? 'Missing odds; ROI approximated' : null,
      odds.find(o => o.outcome === 'Home')?.books < 6 ? 'Low bookmaker consensus' : null
    ].filter(Boolean)
  };

  // Build match output with all aggregated data
  return {
    json: {
      event_key: matchData.event_key,
      match: `${matchData.event_first_player} vs ${matchData.event_second_player}`,
      score: matchData.event_final_result || '-',
      status: matchData.event_status || 'Scheduled',
      tournament: matchData.tournament_name,
      round: matchData.tournament_round,
      date: matchData.event_date,
      time: matchData.event_time,
      odds: odds,
      stats: stats,
      h2h: h2hData.result || {},
      insight: insight,
      scheduledUtc: matchData.scheduledUtc || new Date().toISOString()
    }
  };
});

