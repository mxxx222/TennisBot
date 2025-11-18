#!/usr/bin/env python3
"""
Check what sports are available with current API key
"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv('telegram_secrets.env')

async def check_sports():
    api_key = os.getenv('ODDS_API_KEY')
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.the-odds-api.com/v4/sports"
        params = {'apiKey': api_key}
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                sports = await response.json()
                
                print(f"✅ Found {len(sports)} total sports")
                print("\n🏈 All Available Sports:")
                print("-" * 50)
                
                tennis_found = False
                for sport in sports:
                    key = sport.get('key', '')
                    title = sport.get('title', '')
                    active = sport.get('active', False)
                    
                    if 'tennis' in key.lower():
                        tennis_found = True
                        print(f"🎾 {key}: {title} (Active: {active})")
                    else:
                        print(f"   {key}: {title} (Active: {active})")
                
                if not tennis_found:
                    print("\n❌ No tennis sports found in available sports list")
                    print("💡 Tennis might not be available in free tier")
                    
                    # Check for similar sports
                    print("\n🔍 Looking for alternative sports...")
                    alternatives = []
                    for sport in sports:
                        key = sport.get('key', '').lower()
                        title = sport.get('title', '').lower()
                        if any(word in key or word in title for word in ['sport', 'match', 'game']):
                            alternatives.append(sport)
                    
                    if alternatives:
                        print("📋 Potential alternatives:")
                        for alt in alternatives[:10]:  # Show first 10
                            print(f"   {alt['key']}: {alt['title']}")

asyncio.run(check_sports())
