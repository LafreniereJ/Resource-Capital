#!/usr/bin/env python3
"""
Unified Web Scraper System
Primary: crawl4ai (94.7% success rate)
Fallbacks: requests+BeautifulSoup, Playwright, Selenium, feedparser
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib
import feedparser
import aiohttp
import requests
from bs4 import BeautifulSoup

# Import our intelligence system
from .scraper_intelligence import ScraperIntelligence, record_scraper_attempt

# Import all scraping tools
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logging.warning("crawl4ai not available, using fallback scrapers")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Unified result format for all scrapers"""
    url: str
    success: bool
    content: str = ""
    title: str = ""
    metadata: Dict[str, Any] = None
    scraper_used: str = ""
    response_time: float = 0.0
    word_count: int = 0
    error_message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.content:
            self.word_count = len(self.content.split())

@dataclass 
class ScrapingStrategy:
    """Strategy configuration for fallback handling"""
    primary: str = "crawl4ai"
    fallbacks: List[str] = None
    timeout: int = 30
    retries: int = 3
    rate_limit: float = 2.0
    
    def __post_init__(self):
        if self.fallbacks is None:
            self.fallbacks = ["requests", "playwright", "selenium"]

class UnifiedScraper:
    """Unified web scraper with intelligent fallback system"""
    
    def __init__(self, config_manager=None, intelligence: ScraperIntelligence = None):
        self.config_manager = config_manager
        self.session = None
        self.playwright_context = None
        self.selenium_driver = None
        
        # Initialize intelligence system
        self.intelligence = intelligence or ScraperIntelligence()
        
        # Track performance for auto-optimization (deprecated in favor of intelligence system)
        self.performance_stats = {
            'crawl4ai': {'attempts': 0, 'successes': 0, 'avg_time': 0.0},
            'requests': {'attempts': 0, 'successes': 0, 'avg_time': 0.0},
            'playwright': {'attempts': 0, 'successes': 0, 'avg_time': 0.0},
            'selenium': {'attempts': 0, 'successes': 0, 'avg_time': 0.0},
            'feedparser': {'attempts': 0, 'successes': 0, 'avg_time': 0.0}
        }
        
        # Rate limiting per domain
        self.last_request = {}
        
    async def scrape(self, url: str, target_config: Dict[str, Any] = None, strategy: ScrapingStrategy = None) -> ScrapingResult:
        """Main scraping method with intelligent fallback"""
        
        if strategy is None:
            strategy = ScrapingStrategy()
        
        # Apply rate limiting
        await self._apply_rate_limit(url, strategy.rate_limit)
        
        # Determine scraping strategy based on URL, config, and learned intelligence
        scrapers_to_try = self._determine_scraper_order(url, target_config, strategy)
        
        last_error = ""
        
        for scraper_name in scrapers_to_try:
            try:
                logger.info(f"Attempting to scrape {url} with {scraper_name}")
                start_time = time.time()
                
                result = await self._scrape_with_method(url, scraper_name, target_config)
                
                response_time = time.time() - start_time
                result.response_time = response_time
                result.scraper_used = scraper_name
                
                # Record attempt in intelligence system
                record_scraper_attempt(
                    url=url,
                    scraper_used=scraper_name,
                    success=result.success and len(result.content) > 100,
                    response_time=response_time,
                    content_length=len(result.content),
                    intelligence=self.intelligence
                )
                
                # Update performance stats (legacy)
                self._update_performance_stats(scraper_name, True, response_time)
                
                if result.success and len(result.content) > 100:  # Minimum content threshold
                    logger.info(f"Successfully scraped {url} with {scraper_name} in {response_time:.1f}s")
                    return result
                else:
                    last_error = f"{scraper_name}: Insufficient content ({len(result.content)} chars)"
                    
            except Exception as e:
                error_msg = f"{scraper_name}: {str(e)}"
                logger.warning(f"Scraper {scraper_name} failed for {url}: {error_msg}")
                last_error = error_msg
                
                # Record failed attempt in intelligence system
                record_scraper_attempt(
                    url=url,
                    scraper_used=scraper_name,
                    success=False,
                    response_time=0.0,
                    content_length=0,
                    error_message=error_msg,
                    intelligence=self.intelligence
                )
                
                self._update_performance_stats(scraper_name, False, 0.0)
                continue
        
        # All scrapers failed
        return ScrapingResult(
            url=url,
            success=False,
            error_message=f"All scrapers failed. Last error: {last_error}",
            scraper_used="none"
        )
    
    def _determine_scraper_order(self, url: str, target_config: Dict[str, Any], strategy: ScrapingStrategy) -> List[str]:
        """Intelligently determine which scrapers to try and in what order"""
        
        # First, get learned optimal order from intelligence system
        default_strategy_order = [strategy.primary] + strategy.fallbacks
        learned_order = self.intelligence.get_optimal_scraper_order(url, default_strategy_order)
        
        # Apply special rules that override learning
        
        # Check if it's an RSS feed
        if url.endswith(('.rss', '.xml')) or '/feed/' in url or '/rss/' in url:
            # RSS feeds should always use feedparser first
            rss_order = ['feedparser'] + [s for s in learned_order if s != 'feedparser']
            return rss_order
        
        # Check for JavaScript-heavy sites that typically need browser-based scraping
        js_heavy_indicators = [
            'linkedin.com', 'twitter.com', 'facebook.com', 'sedar', 'sedi',
            'react', 'angular', 'vue', 'spa'
        ]
        
        if any(indicator in url.lower() for indicator in js_heavy_indicators):
            # For JS-heavy sites, prefer browser-based scrapers but still respect learning
            browser_scrapers = [s for s in learned_order if s in ['playwright', 'selenium']]
            other_scrapers = [s for s in learned_order if s not in ['playwright', 'selenium']]
            return browser_scrapers + other_scrapers
        
        # For most sites, use the learned optimal order
        logger.info(f"Using learned scraper order for {urlparse(url).netloc}: {learned_order}")
        return learned_order
    
    async def _scrape_with_method(self, url: str, method: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape using specific method"""
        
        if method == "crawl4ai":
            return await self._scrape_with_crawl4ai(url, target_config)
        elif method == "requests":
            return await self._scrape_with_requests(url, target_config)
        elif method == "playwright":
            return await self._scrape_with_playwright(url, target_config)
        elif method == "selenium":
            return await self._scrape_with_selenium(url, target_config)
        elif method == "feedparser":
            return await self._scrape_with_feedparser(url, target_config)
        else:
            raise ValueError(f"Unknown scraping method: {method}")
    
    async def _scrape_with_crawl4ai(self, url: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape using crawl4ai - our primary method"""
        
        if not CRAWL4AI_AVAILABLE:
            raise ImportError("crawl4ai not available")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            # Configure crawl4ai based on target config
            kwargs = {
                'word_count_threshold': target_config.get('min_word_count', 50) if target_config else 50
            }
            
            # Add custom headers if specified
            if target_config and target_config.get('headers'):
                kwargs['headers'] = target_config['headers']
            
            result = await crawler.arun(url=url, **kwargs)
            
            return ScrapingResult(
                url=url,
                success=bool(result.markdown and len(result.markdown) > 50),
                content=result.markdown or "",
                title=getattr(result, 'title', ''),
                metadata={
                    'links': getattr(result, 'links', {}),
                    'images': getattr(result, 'images', []),
                    'raw_metadata': getattr(result, 'metadata', {})
                }
            )
    
    async def _scrape_with_requests(self, url: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape using requests + BeautifulSoup"""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if target_config and target_config.get('headers'):
            headers.update(target_config['headers'])
        
        # Use aiohttp for async requests
        async with aiohttp.ClientSession(headers=headers) as session:
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
                
                # Extract main content using common selectors
                content_selectors = [
                    'article', '.article-content', '.content', '.post-content',
                    '.entry-content', '.story-body', 'main', '.main-content'
                ]
                
                content_parts = []
                for selector in content_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        if len(text) > 100:  # Only include substantial content
                            content_parts.append(text)
                
                # If no specific content found, use body text
                if not content_parts:
                    body = soup.find('body')
                    if body:
                        content_parts.append(body.get_text().strip())
                
                content = '\n\n'.join(content_parts)
                
                return ScrapingResult(
                    url=url,
                    success=len(content) > 100,
                    content=content,
                    title=title,
                    metadata={'content_type': response.headers.get('content-type', '')}
                )
    
    async def _scrape_with_playwright(self, url: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape using Playwright for JavaScript-heavy sites"""
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("playwright not available")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # Block unnecessary resources for speed
            await context.route('**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}', lambda route: route.abort())
            
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Let page settle
                
                # Get title
                title = await page.title()
                
                # Get main content
                content_selectors = [
                    'article', '.article-content', '.content', '.post-content',
                    '.entry-content', '.story-body', 'main', '.main-content'
                ]
                
                content_parts = []
                for selector in content_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            text = await element.inner_text()
                            if len(text.strip()) > 100:
                                content_parts.append(text.strip())
                    except:
                        continue
                
                # If no specific content found, get body text
                if not content_parts:
                    body = await page.query_selector('body')
                    if body:
                        text = await body.inner_text()
                        content_parts.append(text.strip())
                
                content = '\n\n'.join(content_parts)
                
                return ScrapingResult(
                    url=url,
                    success=len(content) > 100,
                    content=content,
                    title=title,
                    metadata={'page_title': title}
                )
                
            finally:
                await browser.close()
    
    async def _scrape_with_selenium(self, url: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape using Selenium for complex interactions"""
        
        if not SELENIUM_AVAILABLE:
            raise ImportError("selenium not available")
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            title = driver.title
            
            # Try to find main content
            content_selectors = [
                "article", ".article-content", ".content", ".post-content",
                ".entry-content", ".story-body", "main", ".main-content"
            ]
            
            content_parts = []
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if len(text) > 100:
                            content_parts.append(text)
                except:
                    continue
            
            # If no specific content found, get body text
            if not content_parts:
                body = driver.find_element(By.TAG_NAME, "body")
                content_parts.append(body.text.strip())
            
            content = '\n\n'.join(content_parts)
            
            return ScrapingResult(
                url=url,
                success=len(content) > 100,
                content=content,
                title=title,
                metadata={'page_title': title}
            )
            
        finally:
            driver.quit()
    
    async def _scrape_with_feedparser(self, url: str, target_config: Dict[str, Any] = None) -> ScrapingResult:
        """Scrape RSS/XML feeds using feedparser"""
        
        feed = feedparser.parse(url)
        
        if feed.bozo and not feed.entries:
            raise Exception(f"Invalid feed or no entries found")
        
        # Extract feed content
        content_parts = []
        
        # Add feed title and description
        if hasattr(feed.feed, 'title'):
            content_parts.append(f"Feed: {feed.feed.title}")
        
        if hasattr(feed.feed, 'description'):
            content_parts.append(f"Description: {feed.feed.description}")
        
        # Add entries
        for entry in feed.entries[:50]:  # Limit to 50 entries
            entry_parts = []
            
            if hasattr(entry, 'title'):
                entry_parts.append(f"Title: {entry.title}")
            
            if hasattr(entry, 'summary'):
                entry_parts.append(f"Summary: {entry.summary}")
            elif hasattr(entry, 'description'):
                entry_parts.append(f"Description: {entry.description}")
            
            if hasattr(entry, 'published'):
                entry_parts.append(f"Published: {entry.published}")
            
            if hasattr(entry, 'link'):
                entry_parts.append(f"Link: {entry.link}")
            
            if entry_parts:
                content_parts.append('\n'.join(entry_parts))
        
        content = '\n\n---\n\n'.join(content_parts)
        title = getattr(feed.feed, 'title', 'RSS Feed')
        
        return ScrapingResult(
            url=url,
            success=len(content) > 100,
            content=content,
            title=title,
            metadata={
                'feed_entries': len(feed.entries),
                'feed_info': {
                    'title': getattr(feed.feed, 'title', ''),
                    'description': getattr(feed.feed, 'description', ''),
                    'updated': getattr(feed.feed, 'updated', '')
                }
            }
        )
    
    async def _apply_rate_limit(self, url: str, rate_limit: float):
        """Apply rate limiting per domain"""
        domain = urlparse(url).netloc
        
        if domain in self.last_request:
            time_since_last = time.time() - self.last_request[domain]
            if time_since_last < rate_limit:
                sleep_time = rate_limit - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request[domain] = time.time()
    
    def _update_performance_stats(self, scraper: str, success: bool, response_time: float):
        """Update performance statistics for auto-optimization"""
        if scraper in self.performance_stats:
            stats = self.performance_stats[scraper]
            stats['attempts'] += 1
            
            if success:
                stats['successes'] += 1
                # Update rolling average response time
                if stats['avg_time'] == 0:
                    stats['avg_time'] = response_time
                else:
                    stats['avg_time'] = (stats['avg_time'] * 0.8) + (response_time * 0.2)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance statistics for all scrapers"""
        
        report = {}
        for scraper, stats in self.performance_stats.items():
            if stats['attempts'] > 0:
                success_rate = (stats['successes'] / stats['attempts']) * 100
                report[scraper] = {
                    'attempts': stats['attempts'],
                    'successes': stats['successes'],
                    'success_rate': round(success_rate, 1),
                    'avg_response_time': round(stats['avg_time'], 2)
                }
        
        return report
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        
        if self.playwright_context:
            await self.playwright_context.close()
        
        if self.selenium_driver:
            self.selenium_driver.quit()

# Convenience function for easy import
async def scrape_url(url: str, config_manager=None, strategy: ScrapingStrategy = None) -> ScrapingResult:
    """Convenience function to scrape a single URL"""
    scraper = UnifiedScraper(config_manager)
    try:
        return await scraper.scrape(url, strategy=strategy)
    finally:
        await scraper.cleanup()

# Example usage
if __name__ == "__main__":
    async def test_unified_scraper():
        """Test the unified scraper system"""
        
        test_urls = [
            "https://www.northernminer.com/news/",
            "https://www.mining.com/feed/",
            "https://tradingeconomics.com/commodities"
        ]
        
        scraper = UnifiedScraper()
        
        for url in test_urls:
            print(f"\n{'='*60}")
            print(f"Testing: {url}")
            print(f"{'='*60}")
            
            result = await scraper.scrape(url)
            
            print(f"Success: {result.success}")
            print(f"Scraper Used: {result.scraper_used}")
            print(f"Response Time: {result.response_time:.1f}s")
            print(f"Content Length: {len(result.content):,} chars")
            print(f"Word Count: {result.word_count:,}")
            
            if result.content:
                preview = result.content[:200].replace('\n', ' ')
                print(f"Preview: {preview}...")
            
            if not result.success:
                print(f"Error: {result.error_message}")
        
        # Show performance report
        print(f"\n{'='*60}")
        print("PERFORMANCE REPORT")
        print(f"{'='*60}")
        
        report = scraper.get_performance_report()
        for scraper_name, stats in report.items():
            print(f"{scraper_name}: {stats['success_rate']}% success rate, {stats['avg_response_time']}s avg time")
        
        await scraper.cleanup()
    
    asyncio.run(test_unified_scraper())