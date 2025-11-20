# AI Analysis Prompt Template
=============================

Use this prompt to analyze Review-status picks in Notion.

## Prompt Template

```
Analyze these tennis betting candidates from Notion. Each candidate has:
- Player 1 vs Player 2
- Selected Player (who to bet on)
- Odds (1.40-1.80 range)
- Tournament (ITF W15/W25/W35 or ATP Challenger)
- Date & Time
- Player rankings (if available)

Candidates:
[PASTE LIST OF REVIEW-STATUS PICKS FROM NOTION HERE]

For each candidate, check:
1. ELO delta (if available) - ideal: 20-80 point difference
2. Ranking trends - is the selected player improving or declining?
3. Head-to-head (H2H) - historical performance between players
4. Surface stats - how does each player perform on this surface?
5. Red flags - recent injuries, form issues, etc.

Output format:
- Top 3 picks with reasoning
- For each pick: confidence level (High/Medium/Low)
- Key factors that make it a good bet
- Any red flags to watch

Example output:
1. Player A vs Player B (Player A selected)
   - Confidence: High
   - Odds: 1.65
   - Reasoning: ELO delta 45 points, Player A has 3-1 H2H record, strong on hard court (75% win rate), ranking improving
   - Red flags: None

2. Player C vs Player D (Player C selected)
   - Confidence: Medium
   - Odds: 1.55
   - Reasoning: ELO delta 30 points, good surface match, but Player C lost last 2 matches
   - Red flags: Recent form concerns

3. Player E vs Player F (Player E selected)
   - Confidence: Low
   - Odds: 1.75
   - Reasoning: Odds value good, but ranking delta only 15 points, no clear advantage
   - Red flags: Close match, unpredictable
```

## Usage Instructions

1. **Open Notion database**
   - Filter by Status = "Review"
   - Copy the list of candidates

2. **Paste into AI (ChatGPT/Claude/etc.)**
   - Use the prompt template above
   - Replace `[PASTE LIST...]` with actual candidates

3. **Review AI analysis**
   - Check top 3 picks
   - Read reasoning and red flags

4. **Update Notion**
   - Select 2-3 best picks
   - Change Status to "Approved"
   - Copy AI analysis to Notes field

5. **Place bets**
   - Go to betfury.io
   - Place bets on approved picks
   - Update Status to "Pending" when bet placed

## Example Notion Entry Format

When copying from Notion, format like this:

```
Candidate 1:
- Player 1: Maria Garcia
- Player 2: Anna Smith
- Selected: Maria Garcia
- Odds: 1.65
- Tournament: ITF W15 Antalya
- Date: 2025-11-20 14:00
- Rankings: 250 vs 290

Candidate 2:
- Player 1: John Doe
- Player 2: Jane Roe
- Selected: John Doe
- Odds: 1.55
- Tournament: ATP Challenger
- Date: 2025-11-20 16:00
- Rankings: 180 vs 220
```

## Tips

- **Focus on top 3**: Don't try to analyze all 20 candidates
- **Check ELO if available**: More reliable than rankings
- **Surface matters**: Hard court vs clay vs grass performance
- **Recent form**: Last 5 matches performance
- **H2H history**: Previous meetings between players
- **Red flags**: Injuries, withdrawals, poor recent form

## Sprint 2 Improvements

In Sprint 2, ELO data will be automatically added to candidates, making analysis easier and more accurate.

