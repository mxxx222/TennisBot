#!/usr/bin/env python3
"""
🎯 MANUAL GOOGLE SNIPPET TENNIS VALIDATOR
Generates Google search links for manual validation of 21 tennis picks

Usage: python manual_snippet_validator.py
Then: Click links, copy snippet results, paste back
"""

import csv
from pathlib import Path
from urllib.parse import quote_plus

# Your 21 matches
MATCHES = [
    {"EventKey": 12070966, "Match": "T. Seyboth Wild vs V. Kopriva", "Predicted": "Away"},
    {"EventKey": 12071014, "Match": "A. Molcan vs K. Coppejans", "Predicted": "Home"},
    {"EventKey": 12071066, "Match": "F. Bondioli vs A. Martin", "Predicted": "Away"},
    {"EventKey": 12071186, "Match": "N. D. Ionel vs D. Rincon", "Predicted": "Away"},
    {"EventKey": 12071190, "Match": "M. Mrva vs M. Erhard", "Predicted": "Home"},
    {"EventKey": 12071266, "Match": "S. Rokusek vs A. Smith", "Predicted": "Home"},
    {"EventKey": 12071267, "Match": "H. Sato vs N. McKenzie", "Predicted": "Away"},
    {"EventKey": 12071344, "Match": "D. Sumizawa vs J. Brumm", "Predicted": "Home"},
    {"EventKey": 12071345, "Match": "R. Taguchi vs S. Shin", "Predicted": "Away"},
    {"EventKey": 12071349, "Match": "J. Lu vs K. Pavlova", "Predicted": "Home"},
    {"EventKey": 12071360, "Match": "M. Dodig vs Z. Kolar", "Predicted": "Away"},
    {"EventKey": 12071361, "Match": "P. Martinez vs M. Topo", "Predicted": "Home"},
    {"EventKey": 12071364, "Match": "D. Novak vs R. Carballes Baena", "Predicted": "Away"},
    {"EventKey": 12071366, "Match": "C. Stebe vs J. J. Schwaerzler", "Predicted": "Away"},
    {"EventKey": 12071482, "Match": "R. Peniston vs L. Maxted", "Predicted": "Home"},
    {"EventKey": 12071495, "Match": "G. Pedone vs A. Prisacariu", "Predicted": "Home"},
    {"EventKey": 12071499, "Match": "K. Deichmann vs G. Ce", "Predicted": "Home"},
    {"EventKey": 12071542, "Match": "H. Wendelken vs Y. Ghazouani Durand", "Predicted": "Home"},
    {"EventKey": 12071557, "Match": "N. Kicker vs H. Casanova", "Predicted": "Home"},
    {"EventKey": 12071723, "Match": "C. Sinclair vs Je. Delaney", "Predicted": "Home"},
    {"EventKey": 12071729, "Match": "O. Anderson vs P. Brown", "Predicted": "Home"},
]

MATCH_DATE = "17 September 2024"  # Better format for Google
OUTPUT_FILE = Path('validation_results.csv')

def generate_google_links():
    """Generate clickable Google search links"""
    
    print("=" * 80)
    print("🎯 MANUAL GOOGLE SNIPPET VALIDATOR")
    print("=" * 80)
    print(f"📅 Date: {MATCH_DATE}")
    print(f"📊 Matches to validate: {len(MATCHES)}")
    print()
    print("📋 INSTRUCTIONS:")
    print("1. Click each Google link below")
    print("2. Look at the FIRST search result snippet (don't click the link!)")
    print("3. Look for score like: 'Player1 6 4 Player2 3 6' or 'Player beats Player 6-3, 6-4'")
    print("4. Note the winner and come back here")
    print("5. At the end, input all results")
    print("=" * 80)
    
    search_links = []
    
    for i, match in enumerate(MATCHES, 1):
        player1, player2 = match['Match'].split(' vs ')
        
        # Create optimized search queries
        queries = [
            f"{player1} {player2} {MATCH_DATE} tennis result",
            f"{player1} vs {player2} September 17 2024",
            f'"{player1}" "{player2}" tennis September 2024'
        ]
        
        print(f"\n[{i:2d}/21] {match['Match']}")
        print(f"         EventKey: {match['EventKey']}")
        print(f"         Predicted: {match['Predicted']} ({player2 if match['Predicted'] == 'Away' else player1})")
        
        # Generate search links
        for j, query in enumerate(queries, 1):
            encoded_query = quote_plus(query)
            google_url = f"https://www.google.com/search?q={encoded_query}"
            print(f"         🔍 Search {j}: {google_url}")
            
            if j == 1:  # Store primary search
                search_links.append({
                    'match': match,
                    'url': google_url,
                    'query': query
                })
    
    return search_links

def collect_results():
    """Manually collect results from user"""
    
    print("\n" + "=" * 80)
    print("📝 RESULT COLLECTION")
    print("=" * 80)
    print("Now input the results you found:")
    print("Format: Home/Away or H/A")
    print("If unclear/not found: Skip or S")
    print()
    
    results = []
    
    for i, match in enumerate(MATCHES, 1):
        player1, player2 = match['Match'].split(' vs ')
        
        print(f"\n[{i:2d}/21] {match['Match']}")
        print(f"         Predicted: {match['Predicted']}")
        print(f"         Home = {player1}")
        print(f"         Away = {player2}")
        
        while True:
            result = input(f"         Actual winner (Home/Away/Skip): ").strip().lower()
            
            if result in ['h', 'home']:
                results.append({
                    'EventKey': match['EventKey'],
                    'Match': match['Match'],
                    'Predicted': match['Predicted'],
                    'Actual': 'Home',
                    'Correct': match['Predicted'] == 'Home'
                })
                print(f"         ✅ Recorded: Home")
                break
            elif result in ['a', 'away']:
                results.append({
                    'EventKey': match['EventKey'],
                    'Match': match['Match'],
                    'Predicted': match['Predicted'],
                    'Actual': 'Away',
                    'Correct': match['Predicted'] == 'Away'
                })
                print(f"         ✅ Recorded: Away")
                break
            elif result in ['s', 'skip', '']:
                print(f"         ⏭️ Skipped")
                break
            else:
                print(f"         ❌ Invalid input. Use: Home/Away/Skip")
    
    return results

def save_and_analyze_results(results):
    """Save results and show analysis"""
    
    if not results:
        print("\n❌ No results collected")
        return
    
    # Save to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['EventKey', 'Match', 'Predicted', 'Actual', 'Correct'])
        writer.writeheader()
        writer.writerows(results)
    
    # Analysis
    total = len(results)
    correct = sum(1 for r in results if r['Correct'])
    accuracy = correct / total if total > 0 else 0
    
    home_predicted = sum(1 for r in results if r['Predicted'] == 'Home')
    away_predicted = sum(1 for r in results if r['Predicted'] == 'Away')
    
    home_actual = sum(1 for r in results if r['Actual'] == 'Home')
    away_actual = sum(1 for r in results if r['Actual'] == 'Away')
    
    print("\n" + "=" * 80)
    print("📊 VALIDATION RESULTS")
    print("=" * 80)
    print(f"💾 Saved to: {OUTPUT_FILE}")
    print(f"📈 Matches validated: {total}")
    print(f"🎯 Correct predictions: {correct}/{total}")
    print(f"📊 Accuracy: {accuracy:.1%}")
    print()
    print("📋 BREAKDOWN:")
    print(f"   Predicted Home: {home_predicted} → Actual Home: {home_actual}")
    print(f"   Predicted Away: {away_predicted} → Actual Away: {away_actual}")
    
    if accuracy > 0.52:
        print(f"\n✅ GOOD: {accuracy:.1%} accuracy > 52% (profitable at avg odds 1.90)")
    else:
        print(f"\n⚠️ BELOW: {accuracy:.1%} accuracy < 52% (need better model)")
    
    # ROI estimation
    if total > 0:
        expected_profit_per_bet = (accuracy * 0.90) - (1 - accuracy)  # Assuming avg odds 1.90
        roi_percent = expected_profit_per_bet * 100
        
        print(f"\n💰 ESTIMATED ROI:")
        print(f"   Per bet: {expected_profit_per_bet:.1%} (assuming 1.90 avg odds)")
        print(f"   Per 100 bets: {roi_percent:.1f}% ROI")
        
        if expected_profit_per_bet > 0:
            print(f"   📈 PROFITABLE strategy")
        else:
            print(f"   📉 LOSING strategy - need improvements")

def main():
    """Main execution"""
    
    print("Welcome! This tool helps validate your 21 tennis predictions.")
    print("Press Enter to start, or Ctrl+C to exit.")
    input()
    
    # Generate links
    generate_google_links()
    
    print(f"\n🔍 Take your time to check each match above.")
    print(f"📝 When ready, press Enter to input results...")
    input()
    
    # Collect results
    results = collect_results()
    
    # Analysis
    save_and_analyze_results(results)
    
    print("\n🚀 DONE! Check the results file for detailed breakdown.")

if __name__ == '__main__':
    main()

