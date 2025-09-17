#!/usr/bin/env python3
"""
Simple test script to validate tennis_client.py functionality
"""
import sys
import subprocess
import os

def test_help():
    """Test that help command works"""
    result = subprocess.run([sys.executable, "tennis_client.py", "--help"], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert "--date" in result.stdout
    assert "--match" in result.stdout
    print("✅ Help command works")

def test_missing_api_key():
    """Test error handling for missing API key"""
    env = os.environ.copy()
    env.pop("TENNIS_API_KEY", None)  # Remove API key if it exists
    
    result = subprocess.run([sys.executable, "tennis_client.py", 
                           "--date", "2024-01-15", "--match", "Test vs Player"],
                          capture_output=True, text=True, env=env)
    assert result.returncode == 1
    assert "TENNIS_API_KEY ympäristömuuttuja puuttuu" in result.stderr
    print("✅ Missing API key error handling works")

def test_argument_parsing():
    """Test that argument parsing works correctly"""
    # This will fail due to missing API key, but we can check the error message
    result = subprocess.run([sys.executable, "tennis_client.py", 
                           "--date", "2024-01-15", "--match", "Test vs Player"],
                          capture_output=True, text=True)
    assert result.returncode == 1
    # Should fail with missing API key, not argument parsing error
    assert "required" not in result.stderr.lower()
    print("✅ Argument parsing works")

def main():
    print("Running tennis_client.py tests...")
    test_help()
    test_missing_api_key()
    test_argument_parsing()
    print("\n🎾 All tests passed! Tennis client is ready to use.")
    print("To use with real API:")
    print("1. Set TENNIS_API_KEY in .env file")
    print("2. Set TENNIS_WS_URL in .env file")
    print("3. Run: export $(cat .env | xargs)")
    print("4. Run: python tennis_client.py --date YYYY-MM-DD --match 'Player1 vs Player2'")

if __name__ == "__main__":
    main()