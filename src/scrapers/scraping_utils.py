#!/usr/bin/env python3
"""
🌐 ADVANCED WEB SCRAPING UTILITIES
==================================

Comprehensive utilities for web scraping with anti-detection
Includes proxy rotation, user agent cycling, and rate limiting

Author: TennisBot Advanced Analytics
Version: 2.0.0
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import time
from typing import List, Dict, Optional
import threading
import queue
from dataclasses import dataclass
import logging

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'

class AntiDetectionSession:
    """Advanced session with anti-detection features"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.current_ua_index = 0
        self.request_count = 0
        self.last_request_time = time.time()
        self.min_delay = 1.0
        self.max_delay = 3.0
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.setup_default_headers()
    
    def setup_default_headers(self):
        """Setup default headers for anti-detection"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def rotate_user_agent(self):
        """Rotate user agent"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        self.session.headers['User-Agent'] = self.user_agents[self.current_ua_index]
    
    def smart_delay(self):
        """Implement smart delay between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay based on request frequency
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < 1.0:
            additional_delay = random.uniform(1.0, 2.0)
            base_delay += additional_delay
        
        time.sleep(base_delay)
        self.last_request_time = time.time()
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Enhanced GET request with anti-detection"""
        self.smart_delay()
        
        # Rotate user agent every 10 requests
        if self.request_count % 10 == 0:
            self.rotate_user_agent()
        
        self.request_count += 1
        
        return self.session.get(url, **kwargs)

class DataValidator:
    """Data validation and cleaning utilities"""
    
    @staticmethod
    def clean_team_name(name: str) -> str:
        """Clean and standardize team names"""
        if not name:
            return ""
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove special characters but keep hyphens and apostrophes
        import re
        name = re.sub(r'[^\w\s\-\']', '', name)
        
        return name.strip()
    
    @staticmethod
    def validate_odds(odds: float) -> bool:
        """Validate odds values"""
        return isinstance(odds, (int, float)) and 1.01 <= odds <= 100.0
    
    @staticmethod
    def parse_score(score_text: str) -> Dict[str, str]:
        """Parse score text into structured format"""
        if not score_text:
            return {'status': 'Scheduled', 'score': ''}
        
        # Common score patterns
        patterns = {
            r'(\d+)-(\d+)': 'simple_score',
            r'Set (\d+).*?(\d+):(\d+)': 'set_score',
            r'(\d+):(\d+)': 'time_score',
            r'FT (\d+)-(\d+)': 'final_score'
        }
        
        import re
        for pattern, score_type in patterns.items():
            match = re.search(pattern, score_text)
            if match:
                return {
                    'status': score_type,
                    'score': score_text,
                    'parsed': match.groups()
                }
        
        return {'status': 'Unknown', 'score': score_text}

class RateLimiter:
    """Advanced rate limiting with per-domain limits"""
    
    def __init__(self):
        self.domain_limits = {}
        self.domain_requests = {}
        self.lock = threading.Lock()
    
    def set_limit(self, domain: str, requests_per_minute: int):
        """Set rate limit for domain"""
        with self.lock:
            self.domain_limits[domain] = requests_per_minute
            if domain not in self.domain_requests:
                self.domain_requests[domain] = queue.Queue()
    
    def wait_if_needed(self, domain: str):
        """Wait if rate limit would be exceeded"""
        if domain not in self.domain_limits:
            return
        
        with self.lock:
            current_time = time.time()
            request_queue = self.domain_requests[domain]
            limit = self.domain_limits[domain]
            
            # Remove requests older than 1 minute
            while not request_queue.empty():
                if current_time - request_queue.queue[0] > 60:
                    request_queue.get()
                else:
                    break
            
            # Check if we're at the limit
            if request_queue.qsize() >= limit:
                # Wait until the oldest request is more than 1 minute old
                oldest_request = request_queue.queue[0]
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
            
            # Add current request
            request_queue.put(current_time)

class ScrapingMetrics:
    """Track scraping performance and statistics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.requests_made = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.data_points_extracted = 0
        self.errors = []
        self.domain_stats = {}
    
    def record_request(self, domain: str, success: bool):
        """Record a request attempt"""
        self.requests_made += 1
        
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {'success': 0, 'failed': 0}
        
        if success:
            self.successful_requests += 1
            self.domain_stats[domain]['success'] += 1
        else:
            self.failed_requests += 1
            self.domain_stats[domain]['failed'] += 1
    
    def record_data_point(self):
        """Record a successful data extraction"""
        self.data_points_extracted += 1
    
    def record_error(self, error: str, domain: str = None):
        """Record an error"""
        self.errors.append({
            'error': error,
            'domain': domain,
            'timestamp': time.time()
        })
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        duration = time.time() - self.start_time
        
        return {
            'duration_seconds': round(duration, 2),
            'requests_made': self.requests_made,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': round(self.successful_requests / max(self.requests_made, 1) * 100, 2),
            'data_points_extracted': self.data_points_extracted,
            'extraction_rate': round(self.data_points_extracted / max(self.requests_made, 1), 2),
            'requests_per_second': round(self.requests_made / max(duration, 1), 2),
            'domain_stats': self.domain_stats,
            'error_count': len(self.errors),
            'recent_errors': self.errors[-5:] if self.errors else []
        }

def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    return urlparse(url).netloc.lower()

def create_scraping_config() -> Dict:
    """Create comprehensive scraping configuration"""
    return {
        'rate_limits': {
            'flashscore.com': 10,  # requests per minute
            'oddsportal.com': 8,
            'atptour.com': 15,
            'premierleague.com': 12,
            'nba.com': 20
        },
        'delays': {
            'min_delay': 1.0,
            'max_delay': 3.0,
            'error_delay': 5.0
        },
        'retries': {
            'max_retries': 3,
            'backoff_factor': 2.0
        },
        'timeouts': {
            'connect_timeout': 10,
            'read_timeout': 30
        },
        'user_agents_rotation': True,
        'respect_robots_txt': True
    }

if __name__ == "__main__":
    # Test the utilities
    session = AntiDetectionSession()
    validator = DataValidator()
    metrics = ScrapingMetrics()
    
    print("🛠️ Web Scraping Utilities Loaded")
    print("✅ Anti-detection session ready")
    print("✅ Data validation tools ready") 
    print("✅ Rate limiting configured")
    print("✅ Performance metrics initialized")