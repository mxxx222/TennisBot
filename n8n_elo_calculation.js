/**
 * n8n Elo Calculation Code - Tennis Elo Rating System
 * 
 * This code implements Elo rating calculation for tennis players:
 * - K-factor: 32 (or 32 + 5 * tier for tournament weighting)
 * - Initial rating: 1500
 * - Expected win probability: E_A = 1 / (1 + 10^((R_B - R_A)/400))
 * - Rating update: R_A' = R_A + K × (S_A - E_A)
 * 
 * Usage: Add this to your Function Node for Elo calculations
 * Store ratings in Static Data or Notion database
 */

// Elo calculation parameters
const K_BASE = 32; // Base K-factor
const INITIAL_RATING = 1500;
const TIER_MULTIPLIER = 5; // Additional K-factor per tournament tier

// Tournament tier mapping (adjust based on your needs)
const TOURNAMENT_TIERS = {
  'Grand Slam': 5,
  'ATP Masters': 4,
  'ATP 500': 3,
  'ATP 250': 2,
  'Challenger': 1,
  'ITF': 0
};

/**
 * Calculate expected win probability
 * @param {number} ratingA - Player A's current rating
 * @param {number} ratingB - Player B's current rating
 * @returns {number} Expected win probability for Player A (0-1)
 */
function expectedScore(ratingA, ratingB) {
  return 1 / (1 + Math.pow(10, (ratingB - ratingA) / 400));
}

/**
 * Calculate K-factor based on tournament tier
 * @param {string} tournamentType - Tournament type (e.g., 'Challenger', 'ITF')
 * @returns {number} K-factor for this tournament
 */
function getKFactor(tournamentType) {
  const tier = TOURNAMENT_TIERS[tournamentType] || 0;
  return K_BASE + (TIER_MULTIPLIER * tier);
}

/**
 * Update Elo ratings after a match
 * @param {number} ratingA - Player A's current rating
 * @param {number} ratingB - Player B's current rating
 * @param {number} scoreA - Player A's score (1 = win, 0 = loss, 0.5 = draw/WO)
 * @param {number} scoreB - Player B's score (1 = win, 0 = loss, 0.5 = draw/WO)
 * @param {number} kFactor - K-factor for this match
 * @returns {Array} [newRatingA, newRatingB]
 */
function updateElo(ratingA, ratingB, scoreA, scoreB, kFactor = K_BASE) {
  const eA = expectedScore(ratingA, ratingB);
  const eB = expectedScore(ratingB, ratingA);
  
  const newRatingA = ratingA + kFactor * (scoreA - eA);
  const newRatingB = ratingB + kFactor * (scoreB - eB);
  
  return [Math.round(newRatingA), Math.round(newRatingB)];
}

/**
 * Determine match result score from API data
 * @param {Object} fixtureData - Match fixture data from API
 * @param {string} playerKey - Player key to check result for
 * @returns {number} Score (1 = win, 0 = loss, 0.5 = draw/WO)
 */
function getMatchScore(fixtureData, playerKey) {
  const status = fixtureData.event_status || '';
  const winner = fixtureData.event_winner || '';
  const finalResult = fixtureData.event_final_result || '';
  
  // Check if match is finished
  if (status !== 'Finished' && status !== 'Retired' && status !== 'Walkover') {
    return null; // Match not finished
  }
  
  // Check for walkover or retirement
  if (status === 'Walkover' || status === 'Retired') {
    return 0.5; // Neutral result
  }
  
  // Determine winner
  if (winner === 'First Player' && playerKey === fixtureData.first_player_key) {
    return 1; // Win
  } else if (winner === 'Second Player' && playerKey === fixtureData.second_player_key) {
    return 1; // Win
  } else if (winner === 'First Player' || winner === 'Second Player') {
    return 0; // Loss
  }
  
  // Try to determine from score if winner not specified
  if (finalResult && finalResult !== '-') {
    // Parse score (e.g., "2 - 0" means first player won)
    const scoreParts = finalResult.split(' - ');
    if (scoreParts.length === 2) {
      const firstPlayerSets = parseInt(scoreParts[0]);
      const secondPlayerSets = parseInt(scoreParts[1]);
      
      if (firstPlayerSets > secondPlayerSets && playerKey === fixtureData.first_player_key) {
        return 1; // Win
      } else if (secondPlayerSets > firstPlayerSets && playerKey === fixtureData.second_player_key) {
        return 1; // Win
      } else if (firstPlayerSets < secondPlayerSets || secondPlayerSets < firstPlayerSets) {
        return 0; // Loss
      }
    }
  }
  
  return null; // Unable to determine
}

/**
 * Main Elo update function for n8n
 * This should be integrated into your Function Node
 */
function calculateEloUpdate(fixtureData, playerRatings = {}) {
  const player1Key = fixtureData.first_player_key;
  const player2Key = fixtureData.second_player_key;
  const tournamentType = fixtureData.event_type_type || 'ITF';
  
  // Get current ratings (default to INITIAL_RATING if not found)
  const rating1 = playerRatings[player1Key] || INITIAL_RATING;
  const rating2 = playerRatings[player2Key] || INITIAL_RATING;
  
  // Get match scores
  const score1 = getMatchScore(fixtureData, player1Key);
  const score2 = getMatchScore(fixtureData, player2Key);
  
  // Skip if match not finished or unable to determine result
  if (score1 === null || score2 === null) {
    return {
      updated: false,
      reason: 'Match not finished or result unclear',
      ratings: playerRatings
    };
  }
  
  // Calculate K-factor based on tournament tier
  const kFactor = getKFactor(tournamentType);
  
  // Update ratings
  const [newRating1, newRating2] = updateElo(rating1, rating2, score1, score2, kFactor);
  
  // Update ratings object
  const updatedRatings = { ...playerRatings };
  updatedRatings[player1Key] = newRating1;
  updatedRatings[player2Key] = newRating2;
  
  // Calculate expected probabilities before match
  const expectedProb1 = expectedScore(rating1, rating2);
  const expectedProb2 = expectedScore(rating2, rating1);
  
  return {
    updated: true,
    player1: {
      key: player1Key,
      name: fixtureData.event_first_player,
      oldRating: rating1,
      newRating: newRating1,
      change: newRating1 - rating1,
      expectedProb: expectedProb1,
      actualScore: score1
    },
    player2: {
      key: player2Key,
      name: fixtureData.event_second_player,
      oldRating: rating2,
      newRating: newRating2,
      change: newRating2 - rating2,
      expectedProb: expectedProb2,
      actualScore: score2
    },
    tournament: tournamentType,
    kFactor: kFactor,
    ratings: updatedRatings
  };
}

// Example usage in n8n Function Node:
// 
// // Get current ratings from Static Data or previous node
// const staticData = $getWorkflowStaticData('global');
// let playerRatings = staticData.playerRatings || {};
// 
// // Calculate Elo update
// const eloResult = calculateEloUpdate($json, playerRatings);
// 
// // Store updated ratings
// if (eloResult.updated) {
//   staticData.playerRatings = eloResult.ratings;
// }
// 
// // Return result with Elo data
// return [{
//   json: {
//     ...$json,
//     elo: eloResult
//   }
// }];

// Export functions for use
module.exports = {
  expectedScore,
  updateElo,
  getKFactor,
  getMatchScore,
  calculateEloUpdate,
  INITIAL_RATING,
  K_BASE
};

