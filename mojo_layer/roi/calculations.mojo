"""
ROI Calculations Module for Mojo Performance Layer
High-performance ROI, arbitrage, and Kelly Criterion calculations
"""

from python import Python
from python.object import PythonObject
from math_utils import clip_value

alias DType = DType.float64

fn batch_calculate_roi(
    probabilities: Tensor[DType],
    odds: Tensor[DType],
    stakes: Tensor[DType],
) -> Tensor[DType]:
    """
    Calculate ROI for batch of bets
    
    Args:
        probabilities: Win probabilities (batch_size)
        odds: Betting odds (batch_size)
        stakes: Stake amounts (batch_size)
    
    Returns:
        ROI percentages (batch_size)
    """
    var batch_size = probabilities.num_elements()
    var result = Tensor[DType](shape=(batch_size,))
    
    for i in range(batch_size):
        let prob = probabilities[i]
        let bet_odds = odds[i]
        let stake = stakes[i]
        
        # Expected value: (probability * odds - 1) * stake
        let expected_value = (prob * bet_odds - 1.0) * stake
        let roi = (expected_value / stake) * 100.0 if stake > 0.0 else 0.0
        
        result[i] = roi
    
    return result


fn calculate_arbitrage(
    home_odds: Tensor[DType],
    draw_odds: Tensor[DType],
    away_odds: Tensor[DType],
) -> PythonObject:
    """
    Calculate arbitrage opportunities from odds
    
    Args:
        home_odds: Home odds from different bookmakers
        draw_odds: Draw odds from different bookmakers
        away_odds: Away odds from different bookmakers
    
    Returns:
        Python dict with arbitrage margin and stake distribution
    """
    # Find best odds for each outcome
    var best_home: Float64 = home_odds[0]
    var best_home_idx = 0
    var best_away: Float64 = away_odds[0]
    var best_away_idx = 0
    var best_draw: Float64 = 0.0
    var best_draw_idx = -1
    var has_draw = false
    
    for i in range(home_odds.num_elements()):
        if home_odds[i] > best_home:
            best_home = home_odds[i]
            best_home_idx = i
        
        if away_odds[i] > best_away:
            best_away = away_odds[i]
            best_away_idx = i
        
        if i < draw_odds.num_elements() and draw_odds[i] > 0.0:
            if not has_draw:
                best_draw = draw_odds[i]
                best_draw_idx = i
                has_draw = true
            elif draw_odds[i] > best_draw:
                best_draw = draw_odds[i]
                best_draw_idx = i
    
    # Calculate total probability
    var total_prob: Float64 = (1.0 / best_home) + (1.0 / best_away)
    if has_draw and best_draw > 0.0:
        total_prob += (1.0 / best_draw)
    
    # Calculate arbitrage margin
    let margin = 1.0 - total_prob
    
    # Calculate stake distribution if arbitrage exists
    if margin > 0.0:
        let total_stake: Float64 = 100.0
        let home_stake = total_stake / best_home
        let away_stake = total_stake / best_away
        let draw_stake = total_stake / best_draw if has_draw and best_draw > 0.0 else 0.0
        
        # Return as Python dict
        var result = PythonObject({})
        result["margin"] = margin * 100.0  # Convert to percentage
        result["profit_percentage"] = margin * 100.0
        result["has_arbitrage"] = true
        result["stake_distribution"] = PythonObject({
            "home": home_stake,
            "away": away_stake,
            "draw": draw_stake if has_draw else 0.0
        })
        result["best_odds"] = PythonObject({
            "home": best_home,
            "away": best_away,
            "draw": best_draw if has_draw else 0.0
        })
        result["guaranteed_profit"] = total_stake * margin
        
        return result
    
    # No arbitrage
    var result = PythonObject({})
    result["margin"] = margin * 100.0
    result["has_arbitrage"] = false
    return result


fn kelly_criterion(
    probability: Float64,
    odds: Float64,
    bankroll: Float64,
) -> Float64:
    """
    Calculate Kelly Criterion optimal stake
    
    Args:
        probability: True win probability
        odds: Betting odds
        bankroll: Total bankroll
    
    Returns:
        Optimal stake amount
    """
    if odds <= 1.0 or probability <= 0.0 or probability >= 1.0:
        return 0.0
    
    # Kelly fraction: (probability * odds - 1) / (odds - 1)
    let numerator = probability * odds - 1.0
    let denominator = odds - 1.0
    
    if denominator <= 0.0:
        return 0.0
    
    var kelly_fraction = numerator / denominator
    
    # Clip to reasonable range (0 to 0.25 = 25% of bankroll max)
    kelly_fraction = clip_value(kelly_fraction, 0.0, 0.25)
    
    # Calculate optimal stake
    let optimal_stake = kelly_fraction * bankroll
    
    return optimal_stake


fn expected_roi(
    probability: Float64,
    odds: Float64,
    stake: Float64,
) -> Float64:
    """
    Calculate expected ROI for a bet
    
    Args:
        probability: Win probability
        odds: Betting odds
        stake: Stake amount
    
    Returns:
        Expected ROI percentage
    """
    if stake <= 0.0:
        return 0.0
    
    # Expected value: probability * (odds - 1) * stake - (1 - probability) * stake
    let win_return = probability * (odds - 1.0) * stake
    let loss_amount = (1.0 - probability) * stake
    let expected_value = win_return - loss_amount
    
    # ROI as percentage
    let roi = (expected_value / stake) * 100.0
    
    return roi


fn find_best_odds(
    odds_matrix: Tensor[DType],
    bookmaker_indices: Tensor[Int],
) -> PythonObject:
    """
    Find best odds across multiple bookmakers
    
    Args:
        odds_matrix: Matrix of odds (num_bookmakers x num_outcomes)
        bookmaker_indices: Bookmaker indices for each outcome
    
    Returns:
        Python dict with best odds and bookmaker indices
    """
    var num_bookmakers = odds_matrix.shape()[0]
    var num_outcomes = odds_matrix.shape()[1]
    
    var best_odds = Tensor[DType](shape=(num_outcomes,))
    var best_bookmakers = Tensor[Int](shape=(num_outcomes,))
    
    for outcome_idx in range(num_outcomes):
        var best_odd: Float64 = odds_matrix[0, outcome_idx]
        var best_bm_idx = 0
        
        for bm_idx in range(num_bookmakers):
            let odd = odds_matrix[bm_idx, outcome_idx]
            if odd > best_odd:
                best_odd = odd
                best_bm_idx = bm_idx
        
        best_odds[outcome_idx] = best_odd
        best_bookmakers[outcome_idx] = best_bm_idx
    
    # Convert to Python dict
    var result = PythonObject({})
    var odds_list = PythonObject([])
    var bookmakers_list = PythonObject([])
    
    for i in range(num_outcomes):
        odds_list.append(best_odds[i])
        bookmakers_list.append(best_bookmakers[i])
    
    result["best_odds"] = odds_list
    result["best_bookmakers"] = bookmakers_list
    
    return result


fn batch_kelly_criterion(
    probabilities: Tensor[DType],
    odds: Tensor[DType],
    bankrolls: Tensor[DType],
    kelly_fraction: Float64,
) -> Tensor[DType]:
    """
    Calculate Kelly Criterion for batch of bets
    
    Args:
        probabilities: Win probabilities (batch_size)
        odds: Betting odds (batch_size)
        bankrolls: Bankroll amounts (batch_size)
        kelly_fraction: Conservative fraction to apply (e.g., 0.25 for quarter Kelly)
    
    Returns:
        Optimal stakes (batch_size)
    """
    var batch_size = probabilities.num_elements()
    var result = Tensor[DType](shape=(batch_size,))
    
    for i in range(batch_size):
        let prob = probabilities[i]
        let bet_odds = odds[i]
        let bankroll = bankrolls[i]
        
        # Calculate raw Kelly
        var kelly = kelly_criterion(prob, bet_odds, bankroll)
        
        # Apply conservative fraction
        kelly = kelly * kelly_fraction
        
        result[i] = kelly
    
    return result


fn batch_expected_roi(
    probabilities: Tensor[DType],
    odds: Tensor[DType],
    stakes: Tensor[DType],
) -> Tensor[DType]:
    """
    Calculate expected ROI for batch of bets
    
    Args:
        probabilities: Win probabilities (batch_size)
        odds: Betting odds (batch_size)
        stakes: Stake amounts (batch_size)
    
    Returns:
        Expected ROI percentages (batch_size)
    """
    var batch_size = probabilities.num_elements()
    var result = Tensor[DType](shape=(batch_size,))
    
    for i in range(batch_size):
        let prob = probabilities[i]
        let bet_odds = odds[i]
        let stake = stakes[i]
        
        let roi = expected_roi(prob, bet_odds, stake)
        result[i] = roi
    
    return result

