#!/usr/bin/env python3
"""
Web Scraper Node for N8N-Style Scraper

Scrapes text content from websites and forums.
Supports both static HTML parsing and dynamic content via Selenium.
"""

import asyncio
import logging
import re
import random
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import hashlib
import time
from datetime import datetime

import aiohttp
import requests
from bs4 import BeautifulSoup

# Optional Selenium support
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None

from .base_node import SourceNode, NodeExecutionResult

logger = logging.getLogger(__name__)


class WebScraperNode(SourceNode):
    """
    Node for scraping text content from websites and forums.

    Supports:
    - Static HTML parsing with BeautifulSoup
    - Dynamic content via Selenium
    - Multiple selectors for different content types
    - Rate limiting and anti-detection measures
    - Pagination and link following
    """

    def __init__(self, node_id: str, config: Dict[str, Any]):
        super().__init__(node_id, config)

        # Scraping configuration
        self.urls = config.get('urls', [])
        self.selectors = config.get('selectors', {})
        self.max_pages = config.get('max_pages', 10)
        self.follow_links = config.get('follow_links', False)
        self.link_patterns = config.get('link_patterns', [])
        self.use_browser = config.get('use_browser', False)
        self.anti_detection = config.get('anti_detection', True)

        # Content filtering
        self.min_content_length = config.get('min_content_length', 10)
        self.content_types = config.get('content_types', ['text', 'posts', 'comments'])

        # Browser settings (if using Selenium)
        self.browser_wait_timeout = config.get('browser_wait_timeout', 10)
        self.headless = config.get('headless', True)

        # Session management
        self.session = None
        self.driver = None

        # Tracking
        self.visited_urls = set()
        self.scraped_content = []

        # Validate configuration
        if not self.urls:
            raise ValueError("No URLs provided for web scraper")

        if self.use_browser and not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available, falling back to requests")
            self.use_browser = False

    @property
    def inputs(self) -> List[str]:
        return ['trigger', 'optional_urls']

    @property
    def outputs(self) -> List[str]:
        return ['data', 'metadata']

    async def execute(self, input_data: Dict[str, Any]) -> NodeExecutionResult:
        """Execute web scraping"""
        try:
            # Get URLs from input or config
            urls_to_scrape = self._get_urls_to_scrape(input_data)

            if not urls_to_scrape:
                return NodeExecutionResult(
                    success=False,
                    error="No URLs to scrape",
                    node_id=self.node_id
                )

            # Initialize scraping session
            await self._init_session()

            scraped_data = []
            metadata = {
                'total_urls': len(urls_to_scrape),
                'successful_scrapes': 0,
                'failed_scrapes': 0,
                'total_content_items': 0,
                'content_types': self.content_types,
                'selectors_used': list(self.selectors.keys())
            }

            # Scrape each URL
            for url in urls_to_scrape[:self.max_pages]:  # Limit total pages
                try:
                    content = await self._scrape_url(url)
                    if content:
                        scraped_data.extend(content)
                        metadata['successful_scrapes'] += 1
                        metadata['total_content_items'] += len(content)
                    else:
                        metadata['failed_scrapes'] += 1

                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    metadata['failed_scrapes'] += 1
                    continue

            # Clean up
            await self._cleanup()

            return NodeExecutionResult(
                success=True,
                data={
                    'content': scraped_data,
                    'urls_scraped': urls_to_scrape[:len(urls_to_scrape)],
                    'content_count': len(scraped_data)
                },
                metadata=metadata,
                node_id=self.node_id
            )

        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            await self._cleanup()
            return NodeExecutionResult(
                success=False,
                error=str(e),
                node_id=self.node_id
            )

    def _get_urls_to_scrape(self, input_data: Dict[str, Any]) -> List[str]:
        """Get URLs to scrape from config and inputs"""
        urls = list(self.urls)  # Copy config URLs

        # Add URLs from input if provided
        if 'optional_urls' in input_data:
            additional_urls = input_data['optional_urls']
            if isinstance(additional_urls, list):
                urls.extend(additional_urls)
            elif isinstance(additional_urls, str):
                urls.append(additional_urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    async def _init_session(self) -> None:
        """Initialize HTTP session and browser if needed"""
        if self.use_browser:
            await self._init_browser()
        else:
            await self._init_http_session()

    async def _init_http_session(self) -> None:
        """Initialize aiohttp session with anti-detection headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        if self.anti_detection:
            # Add random delays and rotating user agents
            headers['User-Agent'] = self._get_random_user_agent()

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def _init_browser(self) -> None:
        """Initialize Selenium browser"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium not available")

        options = Options()
        if self.headless:
            options.add_argument('--headless')

        # Anti-detection options
        if self.anti_detection:
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-extensions')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)

        # Execute script to remove webdriver property
        if self.anti_detection:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    async def _scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """Scrape content from a single URL"""
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        try:
            if self.use_browser:
                return await self._scrape_with_browser(url)
            else:
                return await self._scrape_with_requests(url)

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    async def _scrape_with_requests(self, url: str) -> List[Dict[str, Any]]:
        """Scrape using aiohttp/requests"""
        async with self.session.get(url) as response:
            if response.status != 200:
                logger.warning(f"HTTP {response.status} for {url}")
                return []

            html = await response.text()
            return self._parse_html_content(html, url)

    async def _scrape_with_browser(self, url: str) -> List[Dict[str, Any]]:
        """Scrape using Selenium browser"""
        try:
            self.driver.get(url)

            # Wait for content to load
            WebDriverWait(self.driver, self.browser_wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for dynamic content
            await asyncio.sleep(2)

            html = self.driver.page_source
            return self._parse_html_content(html, url)

        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Browser scraping failed for {url}: {e}")
            return []

    def _parse_html_content(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse HTML content using BeautifulSoup"""
        soup = BeautifulSoup(html, 'html.parser')
        content_items = []

        # Extract content based on selectors
        for content_type, selector in self.selectors.items():
            if content_type not in self.content_types:
                continue

            try:
                elements = soup.select(selector)
                for element in elements:
                    text_content = self._extract_text_from_element(element)

                    if len(text_content) >= self.min_content_length:
                        content_item = {
                            'id': self._generate_content_id(url, text_content),
                            'url': url,
                            'content_type': content_type,
                            'content': text_content,
                            'timestamp': datetime.now().isoformat(),
                            'metadata': {
                                'element_tag': element.name,
                                'element_attrs': dict(element.attrs) if element.attrs else {},
                                'content_length': len(text_content)
                            }
                        }
                        content_items.append(content_item)

            except Exception as e:
                logger.warning(f"Failed to parse {content_type} from {url}: {e}")
                continue

        # Extract forum posts/comments if no specific selectors
        if not self.selectors and ('posts' in self.content_types or 'comments' in self.content_types):
            forum_content = self._extract_forum_content(soup, url)
            content_items.extend(forum_content)

        # Follow links if enabled
        if self.follow_links:
            new_urls = self._extract_links(soup, url)
            # Note: In a real implementation, you'd queue these for scraping
            logger.debug(f"Found {len(new_urls)} links to follow from {url}")

        return content_items

    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from HTML element"""
        # Remove script and style elements
        for script in element(["script", "style"]):
            script.decompose()

        # Get text and clean it up
        text = element.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_forum_content(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract forum posts and comments using common patterns"""
        content_items = []

        # Common forum selectors
        forum_selectors = [
            '.post', '.comment', '.message', '.thread-post',
            '[class*="post"]', '[class*="comment"]', '[class*="message"]',
            '.forum-post', '.discussion-item'
        ]

        for selector in forum_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text_content = self._extract_text_from_element(element)

                    if len(text_content) >= self.min_content_length:
                        content_item = {
                            'id': self._generate_content_id(url, text_content),
                            'url': url,
                            'content_type': 'forum_post',
                            'content': text_content,
                            'timestamp': datetime.now().isoformat(),
                            'metadata': {
                                'element_tag': element.name,
                                'content_length': len(text_content),
                                'source': 'forum_extraction'
                            }
                        }
                        content_items.append(content_item)

            except Exception as e:
                continue

        return content_items

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links that match patterns"""
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)

            # Check if URL matches patterns
            if self._url_matches_patterns(full_url):
                links.append(full_url)

        return links[:10]  # Limit links to prevent explosion

    def _url_matches_patterns(self, url: str) -> bool:
        """Check if URL matches configured patterns"""
        if not self.link_patterns:
            return True  # Allow all if no patterns specified

        for pattern in self.link_patterns:
            if re.search(pattern, url):
                return True

        return False

    def _generate_content_id(self, url: str, content: str) -> str:
        """Generate unique ID for content item"""
        content_hash = hashlib.md5(f"{url}{content}".encode()).hexdigest()[:8]
        return f"web_{content_hash}"

    def _get_random_user_agent(self) -> str:
        """Get a random user agent for anti-detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(user_agents) if user_agents else user_agents[0]

    async def _cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None

        if self.driver:
            self.driver.quit()
            self.driver = None