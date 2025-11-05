#!/usr/bin/env python3
"""
OpenAI API Connection Test
==========================

Test script to verify OpenAI API key is working correctly.
"""

import asyncio
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

async def test_openai():
    """Test OpenAI API connection"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("🔑 Please add your OpenAI API key to .env file:")
        print('   echo "OPENAI_API_KEY=sk-proj-your-key-here" >> .env')
        return False
    
    print("🧪 Testing OpenAI API connection...")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    try:
        # Initialize client
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'OpenAI connection successful!' if you receive this."}
            ],
            max_tokens=50,
            temperature=0.3
        )
        
        message = response.choices[0].message.content
        print(f"✅ OpenAI Response: {message}")
        print("✅ Connection successful!")
        
        # Check usage
        usage = response.usage
        print(f"\n📊 Token Usage:")
        print(f"   Prompt tokens: {usage.prompt_tokens}")
        print(f"   Completion tokens: {usage.completion_tokens}")
        print(f"   Total tokens: {usage.total_tokens}")
        
        # Calculate cost (GPT-3.5 pricing)
        prompt_cost = (usage.prompt_tokens / 1_000_000) * 0.5  # $0.5 per 1M input tokens
        completion_cost = (usage.completion_tokens / 1_000_000) * 1.5  # $1.5 per 1M output tokens
        total_cost = prompt_cost + completion_cost
        
        print(f"💰 Estimated cost: ~${total_cost:.4f}")
        
        print(f"\n🎯 Ready for GPT Analysis!")
        print(f"   - Model: gpt-3.5-turbo (test)")
        print(f"   - Cost per analysis: ~$0.001")
        print(f"   - Monthly budget ($20): ~20,000 analyses")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check API key format: should start with 'sk-proj-'")
        print(f"   2. Verify billing is set up at: https://platform.openai.com/account/billing")
        print(f"   3. Ensure sufficient credits (try $5 minimum)")
        print(f"   4. Check API key permissions")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_openai())
    exit(0 if result else 1)