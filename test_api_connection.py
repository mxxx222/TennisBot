#!/usr/bin/env python3
"""
Test API connections for Tennis ITF Screener
Verifies that The Odds API key is working and shows available sports
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('telegram_secrets.env')

async def test_odds_api():
    """Test The Odds API connection"""
    
    api_key = os.getenv('ODDS_API_KEY', '1108325cf70df63e93c3d2aa09813f63')
    base_url = "https://api.the-odds-api.com/v4"
    
    print(f"🔑 Testing API Key: {api_key[:8]}...")
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Get sports list
        print("\n📋 Testing sports endpoint...")
        url = f"{base_url}/sports"
        params = {'apiKey': api_key}
        
        try:
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API connection successful!")
                    print(f"📊 Found {len(data)} sports")
                    
                    # Look for tennis sports
                    tennis_sports = [sport for sport in data if 'tennis' in sport.get('key', '').lower()]
                    print(f"🎾 Tennis sports available: {len(tennis_sports)}")
                    
                    for sport in tennis_sports:
                        print(f"  - {sport['key']}: {sport['title']}")
                    
                    # Check if ITF Women's tennis is available
                    itf_women = next((s for s in tennis_sports if s['key'] == 'tennis_itf_women'), None)
                    if itf_women:
                        print(f"✅ ITF Women's tennis found: {itf_women['title']}")
                    else:
                        print(f"❌ ITF Women's tennis not found")
                        print("Available tennis sports:")
                        for sport in tennis_sports:
                            print(f"  - {sport['key']}")
                    
                elif response.status == 401:
                    print(f"❌ Authentication failed - Invalid API key")
                    print(f"💡 Please check your ODDS_API_KEY in telegram_secrets.env")
                    
                elif response.status == 429:
                    print(f"⚠️ Rate limit exceeded")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API error: {response.status}")
                    print(f"Response: {error_text}")
                    
        except Exception as e:
            print(f"💥 Connection error: {e}")
        
        # Test 2: Try to get odds for a tennis sport (if API key works)
        if response.status == 200:
            print(f"\n🎾 Testing tennis odds endpoint...")
            
            # Try different tennis sport keys
            tennis_keys = ['tennis_wta', 'tennis_atp', 'tennis_itf_women']
            
            for sport_key in tennis_keys:
                print(f"\nTrying {sport_key}...")
                url = f"{base_url}/sports/{sport_key}/odds"
                params = {
                    'apiKey': api_key,
                    'regions': 'eu',
                    'markets': 'h2h',
                    'oddsFormat': 'decimal'
                }
                
                try:
                    async with session.get(url, params=params) as response:
                        print(f"  Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"  ✅ Found {len(data)} matches")
                            
                            if data:
                                match = data[0]
                                print(f"  📋 Sample: {match.get('home_team')} vs {match.get('away_team')}")
                        
                        elif response.status == 404:
                            print(f"  ❌ Sport not found or no matches available")
                        
                        else:
                            print(f"  ⚠️ Error: {response.status}")
                            
                except Exception as e:
                    print(f"  💥 Error: {e}")

def main():
    """Main entry point"""
    print("🎾 Tennis ITF Screener - API Connection Test")
    print("=" * 50)
    
    asyncio.run(test_odds_api())
    
    print("\n💡 Next steps:")
    print("1. If API key is invalid, sign up at https://the-odds-api.com")
    print("2. Update ODDS_API_KEY in telegram_secrets.env")
    print("3. Run this test again to verify connection")

if __name__ == "__main__":
    main()
