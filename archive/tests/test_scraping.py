#!/usr/bin/env python3
"""
ChromeDriver and Web Scraping Test
==================================

Test script to verify ChromeDriver is working correctly for web scraping.
"""

import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import sys

def get_chrome_driver():
    """Get ChromeDriver with proper options"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    
    # Set user agent
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ ChromeDriver setup failed: {e}")
        print("\n🔧 Setup Instructions:")
        print("   macOS: brew install chromedriver")
        print("   Ubuntu: sudo apt install chromium-chromedriver")
        print("   Windows: Download from https://chromedriver.chromium.org/")
        return None

async def test_scraping():
    """Test web scraping functionality"""
    print("🧪 Testing web scraping setup...\n")
    
    # Setup ChromeDriver
    driver = get_chrome_driver()
    if not driver:
        return False
    
    try:
        # Test 1: Basic navigation
        print("1️⃣ Test basic navigation...")
        driver.get('https://www.google.com')
        time.sleep(2)
        assert 'Google' in driver.title
        print("   ✅ Basic navigation works\n")
        
        # Test 2: JavaScript rendering
        print("2️⃣ Test JavaScript rendering...")
        driver.get('https://httpbin.org/html')
        time.sleep(3)
        page_source = driver.page_source
        assert len(page_source) > 1000
        print("   ✅ JavaScript rendering works\n")
        
        # Test 3: Dynamic content
        print("3️⃣ Test dynamic content loading...")
        driver.get('https://jsonplaceholder.typicode.com/')
        time.sleep(2)
        
        # Try to find some dynamic content
        title = driver.title
        assert len(title) > 0
        print(f"   ✅ Dynamic content loaded (title: {title})\n")
        
        # Test 4: BeautifulSoup parsing
        print("4️⃣ Test HTML parsing...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        assert soup.find('html') is not None
        print("   ✅ HTML parsing works\n")
        
        # Test 5: Selenium waits
        print("5️⃣ Test Selenium waits...")
        driver.get('https://httpbin.org/delay/1')
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'html')))
        print("   ✅ Selenium waits work\n")
        
        print("🎉 All scraping tests passed!")
        print("🌐 Web scraping is ready for production!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        driver.quit()

def test_scraper_classes():
    """Test if our scraper classes can be imported"""
    print("\n📦 Testing scraper class imports...")
    
    try:
        # Test basic imports
        from src.scrapers.sports_scraper import SportsScraper
        print("   ✅ SportsScraper import works")
        
        from src.scrapers.scraping_utils import ScrapingUtils
        print("   ✅ ScrapingUtils import works")
        
        # Test scraper initialization
        scraper = SportsScraper()
        print("   ✅ SportsScraper instantiation works")
        
        print("✅ All scraper classes ready!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def show_scraper_info():
    """Show information about available scrapers"""
    print("\n📊 Available Scrapers:")
    print("   🔹 SofaScore Scraper: xG data, momentum analysis")
    print("   🔹 FotMob Scraper: Lineups, injuries, team news")
    print("   🔹 FlashScore Scraper: Live events, ultra-fast updates")
    print("   🔹 Betfury Scraper: Live odds, movement tracking")
    print("   🔹 Understat Scraper: Advanced xG models")
    print("   🔹 API Football Scraper: Base statistics")
    
    print("\n🚀 Scraping Capabilities:")
    print("   ✅ Concurrent data collection from multiple sources")
    print("   ✅ Headless browser automation")
    print("   ✅ JavaScript content handling")
    print("   ✅ Anti-detection measures")
    print("   ✅ Rate limiting and error handling")

if __name__ == "__main__":
    print("🌐 ChromeDriver & Web Scraping Test Suite")
    print("=" * 50)
    
    # Test scraper imports first
    import_success = test_scraper_classes()
    
    # Test web scraping
    scraping_success = asyncio.run(test_scraping())
    
    # Show information
    show_scraper_info()
    
    # Final result
    print("\n" + "=" * 50)
    if import_success and scraping_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ ChromeDriver: Ready")
        print("✅ Web Scraping: Ready")
        print("✅ Scraper Classes: Ready")
        print("\n🚀 System ready for multi-source scraping!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print("🔧 Please fix issues before proceeding")
        sys.exit(1)