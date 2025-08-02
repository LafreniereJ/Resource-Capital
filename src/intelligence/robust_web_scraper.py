#!/usr/bin/env python3
"""
Robust Multi-Website Scraper
Advanced web scraping system that can handle multiple website types simultaneously
"""

import asyncio
import aiohttp
import feedparser
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import hashlib
import logging
from pathlib import Path

# Import our existing breaking news system
try:
    from breaking_news_monitor import BreakingNewsEvent
except ImportError:
    from .breaking_news_monitor import BreakingNewsEvent

@dataclass
class ScrapingTarget:
    """Configuration for a scraping target"""
    name: str
    url: str
    scrape_type: str  # 'rss', 'html', 'json_api', 'social'
    selectors: Dict[str, str] = None  # CSS selectors for HTML scraping
    headers: Dict[str, str] = None
    rate_limit: float = 1.0  # seconds between requests
    priority_weight: float = 1.0
    enabled: bool = True
    retry_count: int = 3
    timeout: int = 30
    
    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {}
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mining Intelligence Monitor 2.0 (Research)'
            }

@dataclass
class ScrapingResult:
    """Result from scraping operation"""
    target_name: str
    success: bool
    events: List[BreakingNewsEvent]
    error_message: str = ""
    response_time: float = 0.0
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()

class RobustWebScraper:
    """Advanced multi-website scraping system"""
    
    def __init__(self, config_file: str = "data/processed/scraping_config.json"):
        self.config_file = config_file
        self.session = None
        self.rate_limiters = {}  # Track rate limiting per domain
        self.scraping_targets = self.load_scraping_config()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Advanced selectors for different site types
        self.common_selectors = {
            'headlines': [
                'h1', 'h2', 'h3', '.headline', '.title', '.news-title',
                '[data-testid="headline"]', '.entry-title', '.post-title'
            ],
            'content': [
                '.content', '.article-content', '.post-content', '.entry-content',
                '.story-body', '.article-body', 'main', '.main-content'
            ],
            'dates': [
                '.date', '.published', '.timestamp', '.post-date',
                '[datetime]', '.article-date', '.news-date'
            ],
            'links': [
                'a[href*="article"]', 'a[href*="news"]', 'a[href*="story"]',
                '.news-link', '.article-link', '.headline a'
            ]
        }
    
    def load_scraping_config(self) -> List[ScrapingTarget]:
        """Load scraping targets from configuration"""
        default_targets = [
            # RSS Feeds (existing + new)
            ScrapingTarget(
                name="bloomberg_markets",
                url="https://feeds.bloomberg.com/markets/news.rss",
                scrape_type="rss",
                priority_weight=1.0
            ),
            ScrapingTarget(
                name="reuters_business",
                url="https://feeds.reuters.com/reuters/businessNews",
                scrape_type="rss",
                priority_weight=1.0
            ),
            ScrapingTarget(
                name="bbc_business", 
                url="http://feeds.bbci.co.uk/news/business/rss.xml",
                scrape_type="rss",
                priority_weight=0.9
            ),
            ScrapingTarget(
                name="marketwatch",
                url="http://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
                scrape_type="rss",
                priority_weight=0.8
            ),
            
            # HTML Scraping Targets
            ScrapingTarget(
                name="mining_com_news",
                url="https://www.mining.com/news/",
                scrape_type="html",
                selectors={
                    'headlines': '.post-title a',
                    'content': '.post-excerpt',
                    'dates': '.post-date',
                    'links': '.post-title a'
                },
                rate_limit=2.0,
                priority_weight=0.9
            ),
            ScrapingTarget(
                name="northern_miner",
                url="https://www.northernminer.com/news/",
                scrape_type="html",
                selectors={
                    'headlines': '.entry-title a',
                    'content': '.entry-summary',
                    'dates': '.entry-date',
                    'links': '.entry-title a'
                },
                rate_limit=2.0,
                priority_weight=0.9
            ),
            ScrapingTarget(
                name="financial_post_mining",
                url="https://financialpost.com/commodities",
                scrape_type="html",
                selectors={
                    'headlines': '.article-card__headline',
                    'content': '.article-card__excerpt',
                    'dates': '.article-card__time',
                    'links': '.article-card__headline a'
                },
                rate_limit=1.5,
                priority_weight=0.9
            ),
            ScrapingTarget(
                name="globe_mail_business",
                url="https://www.theglobeandmail.com/business/",
                scrape_type="html",
                selectors={
                    'headlines': '.c-card__headline',
                    'content': '.c-card__excerpt', 
                    'dates': '.c-card__dateline',
                    'links': '.c-card__headline a'
                },
                rate_limit=2.0,
                priority_weight=0.8
            ),
            
            # Alternative/Backup Sources
            ScrapingTarget(
                name="cnbc_markets",
                url="https://www.cnbc.com/markets/",
                scrape_type="html",
                selectors={
                    'headlines': '.Card-title',
                    'links': '.Card-title a'
                },
                rate_limit=2.0,
                priority_weight=0.8
            ),
            
            # Government/Regulatory Sources
            ScrapingTarget(
                name="nrcan_news",
                url="https://www.nrcan.gc.ca/news",
                scrape_type="html",
                selectors={
                    'headlines': '.news-item h3',
                    'content': '.news-item p',
                    'dates': '.news-item .date',
                    'links': '.news-item h3 a'
                },
                rate_limit=3.0,
                priority_weight=0.7
            )
        ]
        
        # Try to load from config file, fall back to defaults
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    targets = []
                    for target_data in config_data.get('targets', []):
                        target = ScrapingTarget(**target_data)
                        targets.append(target)
                    return targets
        except Exception as e:
            self.logger.warning(f"Could not load config file: {e}")
        
        # Save default config
        self.save_scraping_config(default_targets)
        return default_targets
    
    def save_scraping_config(self, targets: List[ScrapingTarget]):
        """Save scraping configuration"""
        config_data = {
            'targets': [asdict(target) for target in targets],
            'updated': datetime.now().isoformat()
        }
        
        Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mining Intelligence Monitor 2.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def respect_rate_limit(self, domain: str, rate_limit: float):
        """Respect rate limiting per domain"""
        now = time.time()
        
        if domain in self.rate_limiters:
            time_since_last = now - self.rate_limiters[domain]
            if time_since_last < rate_limit:
                sleep_time = rate_limit - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.rate_limiters[domain] = now
    
    async def scrape_rss_feed(self, target: ScrapingTarget) -> ScrapingResult:
        """Scrape RSS feed with robust error handling"""
        events = []
        start_time = time.time()
        
        try:
            domain = urlparse(target.url).netloc
            await self.respect_rate_limit(domain, target.rate_limit)
            
            async with self.session.get(target.url, headers=target.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    
                    for entry in feed.entries[:20]:
                        try:
                            # Parse publication date
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                            else:
                                pub_date = datetime.now()
                            
                            if pub_date < cutoff_time:
                                continue
                            
                            # Create event
                            event = BreakingNewsEvent(
                                id="",
                                headline=entry.get('title', ''),
                                summary=entry.get('summary', entry.get('title', '')),
                                url=entry.get('link', ''),
                                source=target.name,
                                published=pub_date
                            )
                            
                            events.append(event)
                            
                        except Exception as e:
                            self.logger.warning(f"Error processing RSS entry: {e}")
                            continue
                else:
                    return ScrapingResult(
                        target_name=target.name,
                        success=False,
                        events=[],
                        error_message=f"HTTP {response.status}",
                        response_time=time.time() - start_time
                    )
                    
        except Exception as e:
            return ScrapingResult(
                target_name=target.name,
                success=False,
                events=[],
                error_message=str(e),
                response_time=time.time() - start_time
            )
        
        return ScrapingResult(
            target_name=target.name,
            success=True,
            events=events,
            response_time=time.time() - start_time
        )
    
    async def scrape_html_content(self, target: ScrapingTarget) -> ScrapingResult:
        """Scrape HTML content with intelligent parsing"""
        events = []
        start_time = time.time()
        
        try:
            domain = urlparse(target.url).netloc
            await self.respect_rate_limit(domain, target.rate_limit)
            
            async with self.session.get(target.url, headers=target.headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract headlines using selectors
                    headlines = self.extract_headlines(soup, target.selectors)
                    
                    for headline_data in headlines[:15]:  # Limit to avoid overload
                        try:
                            event = BreakingNewsEvent(
                                id="",
                                headline=headline_data.get('text', ''),
                                summary=headline_data.get('content', headline_data.get('text', '')),
                                url=headline_data.get('url', target.url),
                                source=target.name,
                                published=headline_data.get('date', datetime.now())
                            )
                            
                            events.append(event)
                            
                        except Exception as e:
                            self.logger.warning(f"Error processing HTML content: {e}")
                            continue
                else:
                    return ScrapingResult(
                        target_name=target.name,
                        success=False,
                        events=[],
                        error_message=f"HTTP {response.status}",
                        response_time=time.time() - start_time
                    )
                    
        except Exception as e:
            return ScrapingResult(
                target_name=target.name,
                success=False,
                events=[],
                error_message=str(e),
                response_time=time.time() - start_time
            )
        
        return ScrapingResult(
            target_name=target.name,
            success=True,
            events=events,
            response_time=time.time() - start_time
        )
    
    def extract_headlines(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract headlines and metadata from HTML"""
        headlines = []
        
        # Try custom selectors first
        headline_elements = []
        
        if 'headlines' in selectors:
            headline_elements = soup.select(selectors['headlines'])
        
        # Fallback to common selectors
        if not headline_elements:
            for selector in self.common_selectors['headlines']:
                headline_elements = soup.select(selector)
                if headline_elements:
                    break
        
        for element in headline_elements[:20]:
            try:
                # Extract text
                text = element.get_text(strip=True)
                if len(text) < 10:  # Skip very short headlines
                    continue
                
                # Extract URL
                url = ""
                if element.name == 'a':
                    url = element.get('href', '')
                else:
                    link = element.find('a')
                    if link:
                        url = link.get('href', '')
                
                # Make absolute URLs
                if url and not url.startswith('http'):
                    url = urljoin(selectors.get('base_url', ''), url)
                
                # Extract content/summary (try to find nearby content)
                content = ""
                if 'content' in selectors:
                    content_elem = element.find_next(selectors['content'])
                    if content_elem:
                        content = content_elem.get_text(strip=True)
                
                # Extract date
                date = datetime.now()
                if 'dates' in selectors:
                    date_elem = element.find_next(selectors['dates'])
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # Simple date parsing (could be enhanced)
                        try:
                            # Try to parse common date formats
                            date = self.parse_date_string(date_text)
                        except:
                            pass
                
                headlines.append({
                    'text': text,
                    'url': url,
                    'content': content,
                    'date': date
                })
                
            except Exception as e:
                self.logger.warning(f"Error extracting headline: {e}")
                continue
        
        return headlines
    
    def parse_date_string(self, date_string: str) -> datetime:
        """Parse various date string formats"""
        # Simple date parsing - could be made more sophisticated
        import dateutil.parser
        try:
            return dateutil.parser.parse(date_string)
        except:
            return datetime.now()
    
    async def scrape_single_target(self, target: ScrapingTarget) -> ScrapingResult:
        """Scrape a single target with retry logic"""
        for attempt in range(target.retry_count):
            try:
                if target.scrape_type == "rss":
                    result = await self.scrape_rss_feed(target)
                elif target.scrape_type == "html":
                    result = await self.scrape_html_content(target)
                else:
                    result = ScrapingResult(
                        target_name=target.name,
                        success=False,
                        events=[],
                        error_message=f"Unsupported scrape type: {target.scrape_type}"
                    )
                
                if result.success:
                    return result
                else:
                    self.logger.warning(f"Attempt {attempt + 1} failed for {target.name}: {result.error_message}")
                    
                    if attempt < target.retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            except Exception as e:
                self.logger.error(f"Exception on attempt {attempt + 1} for {target.name}: {e}")
                if attempt < target.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        return ScrapingResult(
            target_name=target.name,
            success=False,
            events=[],
            error_message="All retry attempts failed"
        )
    
    async def scrape_all_targets(self) -> List[ScrapingResult]:
        """Scrape all enabled targets concurrently"""
        enabled_targets = [t for t in self.scraping_targets if t.enabled]
        
        self.logger.info(f"Starting concurrent scraping of {len(enabled_targets)} targets")
        
        # Create tasks for concurrent scraping
        tasks = [
            self.scrape_single_target(target) 
            for target in enabled_targets
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                valid_results.append(ScrapingResult(
                    target_name=enabled_targets[i].name,
                    success=False,
                    events=[],
                    error_message=str(result)
                ))
            else:
                valid_results.append(result)
        
        return valid_results
    
    def generate_scraping_summary(self, results: List[ScrapingResult]) -> Dict:
        """Generate summary of scraping operation"""
        total_targets = len(results)
        successful_targets = len([r for r in results if r.success])
        total_events = sum(len(r.events) for r in results)
        
        avg_response_time = sum(r.response_time for r in results) / total_targets if total_targets > 0 else 0
        
        target_status = {}
        for result in results:
            target_status[result.target_name] = {
                'success': result.success,
                'events_found': len(result.events),
                'response_time': result.response_time,
                'error': result.error_message if not result.success else None
            }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_targets': total_targets,
            'successful_targets': successful_targets,
            'success_rate': successful_targets / total_targets if total_targets > 0 else 0,
            'total_events_found': total_events,
            'average_response_time': avg_response_time,
            'target_status': target_status
        }

async def main():
    """Test the robust scraper"""
    print("🚀 TESTING ROBUST MULTI-WEBSITE SCRAPER")
    print("=" * 80)
    
    async with RobustWebScraper() as scraper:
        results = await scraper.scrape_all_targets()
        
        summary = scraper.generate_scraping_summary(results)
        
        print(f"📊 SCRAPING SUMMARY:")
        print(f"   Total targets: {summary['total_targets']}")
        print(f"   Successful: {summary['successful_targets']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
        print(f"   Total events: {summary['total_events_found']}")
        print(f"   Avg response time: {summary['average_response_time']:.2f}s")
        
        print(f"\n🎯 TARGET STATUS:")
        for target_name, status in summary['target_status'].items():
            status_icon = "✅" if status['success'] else "❌"
            print(f"   {status_icon} {target_name}: {status['events_found']} events ({status['response_time']:.2f}s)")
            if status['error']:
                print(f"      Error: {status['error']}")
        
        # Show sample events
        all_events = []
        for result in results:
            all_events.extend(result.events)
        
        if all_events:
            print(f"\n📰 SAMPLE HEADLINES:")
            for i, event in enumerate(all_events[:10], 1):
                print(f"   {i}. [{event.source}] {event.headline[:70]}...")

if __name__ == "__main__":
    asyncio.run(main())