#!/usr/bin/env python3
"""
🔍 ODDS API DEBUG TEST
======================
Testaa The Odds API -yhteyden ja palauttaa yksityiskohtaisen diagnostiikan
"""

import requests
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / 'telegram_secrets.env'
if env_path.exists():
    load_dotenv(env_path)

def test_odds_api():
    """Debug: Test if odds API is working"""
    
    # Get API key from environment
    api_key = os.getenv('ODDS_API_KEY', '225ec0328df7dd366c0eb42b25f99a13')
    
    if not api_key or api_key == 'your_betting_api_key_here':
        print("❌ ERROR: ODDS_API_KEY not found in environment")
        print("   Check telegram_secrets.env file")
        return False
    
    print("=" * 60)
    print("🔍 ODDS API DIAGNOSTIC TEST")
    print("=" * 60)
    print(f"\n📋 API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"📋 Full Key Length: {len(api_key)} characters")
    
    # Test 1: Basic connection - List sports
    print("\n" + "=" * 60)
    print("TEST 1: Basic Connection - List Available Sports")
    print("=" * 60)
    
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}"
    print(f"\n🌐 URL: {url}")
    
    try:
        print("⏳ Making request...")
        response = requests.get(url, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            if 'x-requests' in key.lower() or 'x-ratelimit' in key.lower():
                print(f"   {key}: {value}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Connection successful!")
            print(f"📈 Available sports: {len(data)} total")
            
            # Show first 10 sports
            print(f"\n📋 Sample sports (first 10):")
            for i, sport in enumerate(data[:10], 1):
                print(f"   {i}. {sport.get('key', 'N/A')} - {sport.get('title', 'N/A')}")
            
            # Find tennis sports
            tennis_sports = [s for s in data if 'tennis' in s.get('key', '').lower()]
            print(f"\n🎾 Tennis sports found: {len(tennis_sports)}")
            for sport in tennis_sports:
                print(f"   - {sport.get('key')}: {sport.get('title')}")
            
            # Test 2: Get tennis odds
            if tennis_sports:
                print("\n" + "=" * 60)
                print("TEST 2: Fetch Tennis Odds")
                print("=" * 60)
                
                tennis_key = tennis_sports[0]['key']
                odds_url = f"https://api.the-odds-api.com/v4/sports/{tennis_key}/odds/?apiKey={api_key}&regions=eu&markets=h2h"
                print(f"\n🌐 URL: {odds_url}")
                
                print("⏳ Fetching odds...")
                odds_response = requests.get(odds_url, timeout=15)
                
                print(f"✅ Status Code: {odds_response.status_code}")
                
                if odds_response.status_code == 200:
                    odds_data = odds_response.json()
                    print(f"✅ Found {len(odds_data)} matches")
                    
                    if odds_data:
                        print(f"\n📋 First match example:")
                        first_match = odds_data[0]
                        print(f"   Match ID: {first_match.get('id', 'N/A')}")
                        print(f"   Home Team: {first_match.get('home_team', 'N/A')}")
                        print(f"   Away Team: {first_match.get('away_team', 'N/A')}")
                        print(f"   Commence Time: {first_match.get('commence_time', 'N/A')}")
                        print(f"   Bookmakers: {len(first_match.get('bookmakers', []))}")
                        
                        # Show odds
                        if first_match.get('bookmakers'):
                            bookmaker = first_match['bookmakers'][0]
                            print(f"\n   📊 Odds from {bookmaker.get('key', 'N/A')}:")
                            for market in bookmaker.get('markets', []):
                                if market.get('key') == 'h2h':
                                    for outcome in market.get('outcomes', []):
                                        print(f"      {outcome.get('name', 'N/A')}: {outcome.get('price', 'N/A')}")
                    else:
                        print("⚠️  No matches found")
                        print("   This is normal if:")
                        print("   - Tennis is off-season")
                        print("   - No matches scheduled today")
                        print("   - All matches already started")
                        
                        # Try with future dates
                        print("\n🔍 Testing with future date range...")
                        from datetime import datetime, timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        future_url = f"{odds_url}&commenceTimeFrom={tomorrow.isoformat()}"
                        future_response = requests.get(future_url, timeout=15)
                        if future_response.status_code == 200:
                            future_data = future_response.json()
                            print(f"   Found {len(future_data)} matches in next 24h")
                else:
                    print(f"❌ Error: {odds_response.status_code}")
                    print(f"   Response: {odds_response.text[:500]}")
                    
                    if odds_response.status_code == 401:
                        print("\n💡 SOLUTION: API key is invalid or expired")
                        print("   - Generate new key at https://the-odds-api.com")
                        print("   - Update telegram_secrets.env")
                    elif odds_response.status_code == 429:
                        print("\n💡 SOLUTION: Rate limit exceeded")
                        print("   - Free tier: 500 requests/month")
                        print("   - Check X-Requests-Remaining header")
                        print("   - Wait for quota reset or upgrade plan")
            
            # Test 3: Test soccer (more likely to have matches)
            print("\n" + "=" * 60)
            print("TEST 3: Test Soccer (More Likely to Have Matches)")
            print("=" * 60)
            
            soccer_sports = [s for s in data if 'soccer' in s.get('key', '').lower()]
            if soccer_sports:
                soccer_key = soccer_sports[0]['key']
                print(f"\n⚽ Testing with: {soccer_key}")
                soccer_url = f"https://api.the-odds-api.com/v4/sports/{soccer_key}/odds/?apiKey={api_key}&regions=eu&markets=h2h"
                
                print("⏳ Fetching soccer odds...")
                soccer_response = requests.get(soccer_url, timeout=15)
                
                if soccer_response.status_code == 200:
                    soccer_data = soccer_response.json()
                    print(f"✅ Found {len(soccer_data)} soccer matches")
                    if soccer_data:
                        print("✅ API is working! Problem is likely no tennis matches available.")
                    else:
                        print("⚠️  No soccer matches either - might be off-peak hours")
                else:
                    print(f"❌ Soccer test failed: {soccer_response.status_code}")
            
            return True
            
        elif response.status_code == 401:
            print("❌ ERROR: Unauthorized (401)")
            print("   API key is invalid or expired")
            print("   Solution: Generate new key at https://the-odds-api.com")
            return False
        elif response.status_code == 429:
            print("❌ ERROR: Rate Limit Exceeded (429)")
            print("   You've used all free tier requests (500/month)")
            print("   Solution: Wait for quota reset or upgrade plan")
            return False
        else:
            print(f"❌ ERROR: Status Code {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print("❌ ERROR: Cannot connect to API")
        print(f"   Error: {str(e)}")
        print("\n💡 POSSIBLE CAUSES:")
        print("   1. No internet connection")
        print("   2. DNS resolution failure")
        print("   3. Firewall blocking connection")
        print("   4. VPN/proxy issues")
        print("\n🔧 SOLUTIONS:")
        print("   - Check internet connection")
        print("   - Try: ping api.the-odds-api.com")
        print("   - Check DNS settings")
        print("   - Disable VPN if active")
        return False
        
    except requests.exceptions.Timeout as e:
        print("❌ ERROR: Request timeout")
        print(f"   Error: {str(e)}")
        print("   API server might be slow or unreachable")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🚀 Starting Odds API Diagnostic Test...\n")
    success = test_odds_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ DIAGNOSTIC COMPLETE - Check results above")
    else:
        print("❌ DIAGNOSTIC FAILED - See errors above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

