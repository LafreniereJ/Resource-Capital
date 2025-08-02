#!/usr/bin/env python3
"""
Advanced Web Scraper Infrastructure
Main orchestrator for high-volume news scraping across multiple sources
"""

import sys
import os
sys.path.append('../')

import asyncio
import aiohttp
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import json
import sqlite3
import hashlib
from urllib.parse import urljoin, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Web scraping libraries
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..core.config import Config

@dataclass
class ScrapedArticle:
    """Scraped article data structure"""
    url: str
    title: str
    content: str
    published_date: Optional[datetime]
    source: str
    author: Optional[str]
    category: Optional[str]
    relevance_score: float = 0.0
    companies_mentioned: List[str] = None
    commodities_mentioned: List[str] = None
    sentiment: str = "neutral"
    hash_id: str = ""
    
    def __post_init__(self):
        if self.companies_mentioned is None:
            self.companies_mentioned = []
        if self.commodities_mentioned is None:
            self.commodities_mentioned = []
        
        # Generate unique hash ID for deduplication
        content_hash = hashlib.md5(
            f"{self.title}{self.content[:200]}".encode('utf-8')
        ).hexdigest()
        self.hash_id = content_hash

@dataclass
class SourceConfig:
    """Configuration for a news source"""
    name: str
    base_url: str
    news_section_urls: List[str]
    scraping_method: str  # 'requests', 'playwright', 'selenium'
    rate_limit: float  # seconds between requests
    selectors: Dict[str, str]  # CSS selectors for content extraction
    headers: Dict[str, str]
    enabled: bool = True
    priority: int = 1  # 1=high, 2=medium, 3=low

class AdvancedWebScraper:
    """High-volume web scraper for mining news intelligence"""
    
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.setup_logging()
        self.setup_database()
        
        # Rate limiting and performance
        self.max_concurrent = 50
        self.global_rate_limit = 0.1  # seconds between requests
        self.last_request_time = {}
        
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # Load source configurations
        self.sources = self.load_source_configs()
        
        # Load Canadian mining companies for entity recognition
        self.canadian_companies = self.load_canadian_companies()
        
        # Commodity keywords for detection
        self.commodities = [
            'gold', 'silver', 'copper', 'zinc', 'nickel', 'iron', 'aluminum',
            'platinum', 'palladium', 'uranium', 'lithium', 'cobalt', 'rare earth',
            'oil', 'natural gas', 'coal'
        ]
    
    def setup_logging(self):
        """Setup logging for scraping operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/logs/scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup SQLite database for article storage"""
        os.makedirs('data/databases', exist_ok=True)
        self.db_path = 'data/databases/articles.db'
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE,
                url TEXT,
                title TEXT,
                content TEXT,
                published_date DATETIME,
                source TEXT,
                author TEXT,
                category TEXT,
                relevance_score REAL,
                companies_mentioned TEXT,
                commodities_mentioned TEXT,
                sentiment TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash_id ON articles(hash_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_relevance_score ON articles(relevance_score)
        ''')
        
        conn.commit()
        conn.close()
    
    def load_source_configs(self) -> List[SourceConfig]:
        """Load configuration for all news sources"""
        sources = []
        
        # Major Mining News Sites
        sources.extend([
            SourceConfig(
                name="Mining.com",
                base_url="https://www.mining.com",
                news_section_urls=[
                    "https://www.mining.com/category/news/",
                    "https://www.mining.com/category/mining/",
                    "https://www.mining.com/category/markets/"
                ],
                scraping_method="requests",
                rate_limit=1.0,
                selectors={
                    "articles": ".post",
                    "title": "h2.entry-title a",
                    "link": "h2.entry-title a",
                    "content": ".entry-content",
                    "date": ".entry-date",
                    "author": ".author"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=1
            ),
            
            SourceConfig(
                name="Northern Miner",
                base_url="https://www.northernminer.com",
                news_section_urls=[
                    "https://www.northernminer.com/news/",
                    "https://www.northernminer.com/category/mining/",
                    "https://www.northernminer.com/category/exploration/"
                ],
                scraping_method="requests",
                rate_limit=1.5,
                selectors={
                    "articles": "article.post",
                    "title": "h2.entry-title a",
                    "link": "h2.entry-title a",
                    "content": ".entry-content",
                    "date": ".published",
                    "author": ".author-name"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=1
            ),
            
            SourceConfig(
                name="Kitco News",
                base_url="https://www.kitco.com",
                news_section_urls=[
                    "https://www.kitco.com/news/",
                    "https://www.kitco.com/news/mining/",
                    "https://www.kitco.com/news/gold/"
                ],
                scraping_method="playwright",
                rate_limit=2.0,
                selectors={
                    "articles": ".news-item",
                    "title": ".news-title a",
                    "link": ".news-title a",
                    "content": ".news-content",
                    "date": ".news-date",
                    "author": ".news-author"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=1
            ),
            
            SourceConfig(
                name="Reuters Mining",
                base_url="https://www.reuters.com",
                news_section_urls=[
                    "https://www.reuters.com/business/mining-metals/",
                    "https://www.reuters.com/business/commodities/"
                ],
                scraping_method="playwright",
                rate_limit=2.0,
                selectors={
                    "articles": "[data-testid='MediaStoryCard']",
                    "title": "[data-testid='Heading']",
                    "link": "a",
                    "content": "[data-testid='paragraph']",
                    "date": "time",
                    "author": "[data-testid='Author']"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=1
            )
        ])
        
        # Financial News Sources
        sources.extend([
            SourceConfig(
                name="MarketWatch Materials",
                base_url="https://www.marketwatch.com",
                news_section_urls=[
                    "https://www.marketwatch.com/investing/stock/xphe",
                    "https://www.marketwatch.com/investing/stock/xlb"
                ],
                scraping_method="requests",
                rate_limit=1.0,
                selectors={
                    "articles": ".article__summary",
                    "title": ".link",
                    "link": ".link",
                    "content": ".article__content",
                    "date": ".article__timestamp",
                    "author": ".author"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=2
            ),
            
            SourceConfig(
                name="Financial Post Commodities",
                base_url="https://financialpost.com",
                news_section_urls=[
                    "https://financialpost.com/commodities",
                    "https://financialpost.com/category/commodities"
                ],
                scraping_method="requests",
                rate_limit=1.5,
                selectors={
                    "articles": ".article-card",
                    "title": ".headline a",
                    "link": ".headline a",
                    "content": ".article-content",
                    "date": ".published-date",
                    "author": ".author-name"
                },
                headers={"User-Agent": "Mining Intelligence Bot 1.0"},
                priority=2
            )
        ])
        
        return sources
    
    def load_canadian_companies(self) -> List[str]:
        """Load Canadian mining company names for entity recognition"""
        try:
            import pandas as pd
            
            # Load both TSX and TSXV companies
            tsx_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSX Canadian Companies',
                header=8
            )
            
            tsxv_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSXV Canadian Companies',
                header=8
            )
            
            companies = []
            
            # Extract company names
            for df in [tsx_df, tsxv_df]:
                if 'Name' in df.columns:
                    names = df['Name'].dropna().tolist()
                    companies.extend(names)
            
            # Clean company names (remove common suffixes)
            cleaned_companies = []
            for name in companies:
                # Remove common corporate suffixes
                cleaned = name.replace(' Corp.', '').replace(' Inc.', '').replace(' Ltd.', '')
                cleaned = cleaned.replace(' Limited', '').replace(' Corporation', '')
                cleaned_companies.append(cleaned.strip())
            
            # Remove duplicates and sort by length (longer names first for better matching)
            unique_companies = list(set(cleaned_companies))
            unique_companies.sort(key=len, reverse=True)
            
            self.logger.info(f"Loaded {len(unique_companies)} Canadian mining companies for entity recognition")
            return unique_companies
            
        except Exception as e:
            self.logger.error(f"Error loading Canadian companies: {e}")
            return []
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent for rotation"""
        return random.choice(self.user_agents)
    
    def respect_rate_limit(self, source_name: str, rate_limit: float):
        """Respect rate limiting for a specific source"""
        current_time = time.time()
        last_request = self.last_request_time.get(source_name, 0)
        
        time_since_last = current_time - last_request
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[source_name] = time.time()
    
    def scrape_with_requests(self, url: str, source: SourceConfig) -> Optional[BeautifulSoup]:
        """Scrape using requests library"""
        try:
            self.respect_rate_limit(source.name, source.rate_limit)
            
            headers = source.headers.copy()
            headers['User-Agent'] = self.get_random_user_agent()
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Error scraping {url} with requests: {e}")
            return None
    
    async def scrape_with_playwright(self, url: str, source: SourceConfig) -> Optional[BeautifulSoup]:
        """Scrape using Playwright for JavaScript-heavy sites"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(
                    user_agent=self.get_random_user_agent()
                )
                
                await page.goto(url, wait_until='networkidle')
                content = await page.content()
                await browser.close()
                
                return BeautifulSoup(content, 'html.parser')
                
        except Exception as e:
            self.logger.error(f"Error scraping {url} with Playwright: {e}")
            return None
    
    def scrape_with_selenium(self, url: str, source: SourceConfig) -> Optional[BeautifulSoup]:
        """Scrape using Selenium for complex interactions"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.get_random_user_agent()}')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            content = driver.page_source
            driver.quit()
            
            return BeautifulSoup(content, 'html.parser')
            
        except Exception as e:
            self.logger.error(f"Error scraping {url} with Selenium: {e}")
            return None
    
    def extract_articles_from_page(self, soup: BeautifulSoup, source: SourceConfig, page_url: str) -> List[Dict]:
        """Extract article information from a page"""
        articles = []
        
        try:
            # Find all article elements
            article_elements = soup.select(source.selectors.get('articles', 'article'))
            
            for element in article_elements:
                try:
                    # Extract title and link
                    title_elem = element.select_one(source.selectors.get('title', 'h1, h2, h3'))
                    link_elem = element.select_one(source.selectors.get('link', 'a'))
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href')
                    
                    # Make link absolute
                    if link and not link.startswith('http'):
                        link = urljoin(source.base_url, link)
                    
                    # Extract other metadata
                    date_elem = element.select_one(source.selectors.get('date', 'time, .date'))
                    author_elem = element.select_one(source.selectors.get('author', '.author'))
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'date_text': date_elem.get_text(strip=True) if date_elem else None,
                        'author': author_elem.get_text(strip=True) if author_elem else None,
                        'source': source.name
                    })
                    
                except Exception as e:
                    self.logger.debug(f"Error extracting article from element: {e}")
                    continue
            
            self.logger.info(f"Extracted {len(articles)} articles from {page_url}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error extracting articles from {page_url}: {e}")
            return []
    
    def scrape_article_content(self, article_url: str, source: SourceConfig) -> Optional[str]:
        """Scrape full content from an individual article"""
        try:
            # Choose scraping method based on source configuration
            if source.scraping_method == 'playwright':
                soup = asyncio.run(self.scrape_with_playwright(article_url, source))
            elif source.scraping_method == 'selenium':
                soup = self.scrape_with_selenium(article_url, source)
            else:
                soup = self.scrape_with_requests(article_url, source)
            
            if not soup:
                return None
            
            # Extract content using source selectors
            content_elem = soup.select_one(source.selectors.get('content', '.content, .article-content, .post-content'))
            
            if content_elem:
                # Extract text and clean it
                content = content_elem.get_text(separator=' ', strip=True)
                # Remove extra whitespace
                content = ' '.join(content.split())
                return content
            
            # Fallback: try to extract from common content containers
            for selector in ['.content', '.article-body', '.post-content', '.entry-content', 'main']:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator=' ', strip=True)
                    content = ' '.join(content.split())
                    return content
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping content from {article_url}: {e}")
            return None
    
    def is_duplicate(self, article_hash: str) -> bool:
        """Check if article already exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM articles WHERE hash_id = ?", (article_hash,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def save_article(self, article: ScrapedArticle):
        """Save article to database"""
        if self.is_duplicate(article.hash_id):
            self.logger.debug(f"Skipping duplicate article: {article.title}")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO articles (
                hash_id, url, title, content, published_date, source, author, 
                category, relevance_score, companies_mentioned, commodities_mentioned, sentiment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article.hash_id,
            article.url,
            article.title,
            article.content,
            article.published_date,
            article.source,
            article.author,
            article.category,
            article.relevance_score,
            json.dumps(article.companies_mentioned),
            json.dumps(article.commodities_mentioned),
            article.sentiment
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Saved article: {article.title}")
    
    def extract_entities(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract mentioned companies and commodities from text"""
        text_lower = text.lower()
        
        # Find mentioned companies
        mentioned_companies = []
        for company in self.canadian_companies[:500]:  # Check top 500 companies for performance
            if len(company) > 3 and company.lower() in text_lower:
                mentioned_companies.append(company)
        
        # Find mentioned commodities
        mentioned_commodities = []
        for commodity in self.commodities:
            if commodity in text_lower:
                mentioned_commodities.append(commodity)
        
        return mentioned_companies, mentioned_commodities
    
    def calculate_relevance_score(self, article: ScrapedArticle) -> float:
        """Calculate relevance score for Canadian mining industry"""
        score = 0.0
        text = f"{article.title} {article.content}".lower()
        
        # Canadian relevance
        canadian_terms = ['canada', 'canadian', 'toronto', 'vancouver', 'tsx', 'tsxv', 'ontario', 'quebec', 'british columbia']
        canada_score = sum(5 for term in canadian_terms if term in text)
        score += min(canada_score, 25)
        
        # Mining relevance
        mining_terms = ['mining', 'mine', 'exploration', 'production', 'ore', 'deposit', 'reserves', 'resources']
        mining_score = sum(3 for term in mining_terms if term in text)
        score += min(mining_score, 20)
        
        # Company mentions
        score += len(article.companies_mentioned) * 5
        
        # Commodity mentions
        score += len(article.commodities_mentioned) * 3
        
        # High-value keywords
        high_value = ['merger', 'acquisition', 'takeover', 'earnings', 'production', 'discovery', 'permit', 'approval']
        hv_score = sum(8 for term in high_value if term in text)
        score += min(hv_score, 30)
        
        return min(score, 100.0)
    
    def process_article(self, article_data: Dict, source: SourceConfig) -> Optional[ScrapedArticle]:
        """Process a single article - scrape content and analyze"""
        try:
            # Scrape full content
            content = self.scrape_article_content(article_data['url'], source)
            if not content or len(content) < 100:  # Skip very short articles
                return None
            
            # Parse date
            published_date = None
            if article_data.get('date_text'):
                try:
                    from dateutil.parser import parse
                    published_date = parse(article_data['date_text'])
                except:
                    pass
            
            # Create article object
            article = ScrapedArticle(
                url=article_data['url'],
                title=article_data['title'],
                content=content,
                published_date=published_date,
                source=article_data['source'],
                author=article_data.get('author')
            )
            
            # Extract entities
            companies, commodities = self.extract_entities(f"{article.title} {article.content}")
            article.companies_mentioned = companies
            article.commodities_mentioned = commodities
            
            # Calculate relevance score
            article.relevance_score = self.calculate_relevance_score(article)
            
            # Skip low-relevance articles
            if article.relevance_score < 10.0:
                return None
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error processing article {article_data.get('url', 'unknown')}: {e}")
            return None
    
    def scrape_source(self, source: SourceConfig, max_articles: int = 100) -> List[ScrapedArticle]:
        """Scrape all articles from a single source"""
        self.logger.info(f"Starting to scrape {source.name}")
        articles = []
        
        try:
            for section_url in source.news_section_urls:
                if len(articles) >= max_articles:
                    break
                
                self.logger.info(f"Scraping section: {section_url}")
                
                # Choose scraping method
                if source.scraping_method == 'playwright':
                    soup = asyncio.run(self.scrape_with_playwright(section_url, source))
                elif source.scraping_method == 'selenium':
                    soup = self.scrape_with_selenium(section_url, source)
                else:
                    soup = self.scrape_with_requests(section_url, source)
                
                if not soup:
                    continue
                
                # Extract article links from the page
                article_data_list = self.extract_articles_from_page(soup, source, section_url)
                
                # Process articles with threading
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for article_data in article_data_list[:max_articles - len(articles)]:
                        future = executor.submit(self.process_article, article_data, source)
                        futures.append(future)
                    
                    for future in as_completed(futures):
                        article = future.result()
                        if article:
                            articles.append(article)
                            self.save_article(article)
            
            self.logger.info(f"Completed scraping {source.name}: {len(articles)} articles processed")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error scraping {source.name}: {e}")
            return []
    
    def run_full_scrape(self, max_articles_per_source: int = 50) -> Dict[str, int]:
        """Run full scraping across all sources"""
        self.logger.info("Starting full scraping operation")
        start_time = time.time()
        
        results = {}
        total_articles = 0
        
        # Sort sources by priority
        sorted_sources = sorted(self.sources, key=lambda x: x.priority)
        
        for source in sorted_sources:
            if not source.enabled:
                continue
            
            try:
                articles = self.scrape_source(source, max_articles_per_source)
                results[source.name] = len(articles)
                total_articles += len(articles)
                
                self.logger.info(f"{source.name}: {len(articles)} articles scraped")
                
            except Exception as e:
                self.logger.error(f"Error scraping {source.name}: {e}")
                results[source.name] = 0
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Scraping completed: {total_articles} total articles in {elapsed_time:.2f}s")
        
        return results

def main():
    """Test the advanced web scraper"""
    print("🕷️ Advanced Web Scraper Test")
    print("=" * 50)
    
    scraper = AdvancedWebScraper()
    
    # Run a limited test scrape
    print("🚀 Starting test scrape...")
    results = scraper.run_full_scrape(max_articles_per_source=10)
    
    print(f"\n📊 SCRAPING RESULTS:")
    total = 0
    for source, count in results.items():
        print(f"  • {source}: {count} articles")
        total += count
    
    print(f"\n✅ Total articles scraped: {total}")
    print("🎯 Advanced web scraping infrastructure ready!")

if __name__ == "__main__":
    main()