#!/usr/bin/env python3
"""
Specialized Mining News Scraper
Enhanced version focused specifically on mining industry news and analysis

Focuses on:
- Mining industry publications (Northern Miner, Mining.com, etc.)
- Financial news with mining focus (Reuters, S&P Global)
- Company-specific news and announcements
- Regulatory and policy news affecting mining
- Market analysis and commentary
- Exploration and development updates
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib

from ..unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from ..scraper_intelligence import ScraperIntelligence


class SpecializedMiningNewsScraper:
    """Enhanced mining news scraper with specialized filtering and analysis"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/news")
        self.intelligence = ScraperIntelligence()
        self.unified_scraper = UnifiedScraper(intelligence=self.intelligence)
        
        # Ensure data directories exist
        self._setup_data_directories()
        
        # Enhanced news sources configuration
        self.news_sources = {
            "northern_miner": {
                "base_url": "https://www.northernminer.com",
                "priority": "critical",
                "specialization": "mining_industry",
                "endpoints": {
                    "latest_news": "/news/",
                    "markets": "/markets/",
                    "exploration": "/exploration/",
                    "mining_operations": "/mining-operations/",
                    "corporate": "/corporate/",
                    "junior_miners": "/junior-miners/"
                },
                "selectors": {
                    "articles": [".article", ".post", ".news-item"],
                    "title": [".article-title", ".entry-title", "h1", "h2"],
                    "content": [".article-content", ".entry-content", ".post-content"],
                    "date": [".article-date", ".entry-date", ".post-date"],
                    "author": [".author", ".byline"],
                    "category": [".category", ".tag", ".section"]
                }
            },
            "mining_dot_com": {
                "base_url": "https://www.mining.com",
                "priority": "high",
                "specialization": "global_mining_news",
                "endpoints": {
                    "main_feed": "/",
                    "rss_feed": "/feed/",
                    "base_metals": "/category/base-metals/",
                    "precious_metals": "/category/precious-metals/",
                    "energy_minerals": "/category/energy-minerals/",
                    "industrial_minerals": "/category/industrial-minerals/",
                    "investment": "/category/investment/"
                },
                "selectors": {
                    "articles": [".entry", ".post", ".article"],
                    "title": [".entry-title", "h1", "h2"],
                    "content": [".entry-content", ".post-content"],
                    "date": [".entry-date", ".published"],
                    "excerpt": [".entry-summary", ".excerpt"]
                }
            },
            "reuters_mining": {
                "base_url": "https://www.reuters.com",
                "priority": "critical",
                "specialization": "financial_mining_news",
                "endpoints": {
                    "commodities": "/markets/commodities/",
                    "mining_energy": "/business/energy/",
                    "canada_business": "/world/americas/canada/business/"
                },
                "selectors": {
                    "articles": [".story-content", ".article-wrap"],
                    "title": [".story-title", "h1"],
                    "content": [".story-body", ".article-body"],
                    "date": [".date-line", ".article-time"],
                    "topic": [".topic", ".kicker"]
                }
            },
            "sp_global_mining": {
                "base_url": "https://www.spglobal.com",
                "priority": "high",
                "specialization": "market_analysis",
                "endpoints": {
                    "metals_analysis": "/commodityinsights/en/market-insights/latest-news/metals",
                    "mining_analysis": "/commodityinsights/en/market-insights/latest-news/mining",
                    "market_data": "/commodityinsights/en/market-data"
                },
                "selectors": {
                    "articles": [".article-card", ".content-item"],
                    "title": [".article-title", "h2", "h3"],
                    "content": [".article-content", ".summary"],
                    "date": [".publish-date", ".date"],
                    "analysis_type": [".content-type", ".category"]
                }
            },
            "mining_weekly": {
                "base_url": "https://www.miningweekly.com",
                "priority": "medium",
                "specialization": "industry_updates",
                "endpoints": {
                    "latest": "/latest-news",
                    "gold": "/topic/gold",
                    "platinum": "/topic/platinum",
                    "mining_companies": "/topic/mining-companies"
                },
                "selectors": {
                    "articles": [".article", ".news-item"],
                    "title": [".headline", "h1", "h2"],
                    "content": [".body", ".content"],
                    "date": [".date", ".timestamp"]
                }
            },
            "kitco_news": {
                "base_url": "https://www.kitco.com",
                "priority": "medium",
                "specialization": "precious_metals_news",
                "endpoints": {
                    "gold_news": "/news/gold/",
                    "silver_news": "/news/silver/",
                    "mining_news": "/news/mining/"
                },
                "selectors": {
                    "articles": [".article", ".news-article"],
                    "title": [".title", "h1"],
                    "content": [".article-body", ".content"],
                    "date": [".date", ".published-date"]
                }
            }
        }
        
        # News categorization and filtering
        self.news_categories = {
            "breaking_news": {
                "keywords": ["breaking", "urgent", "alert", "just in", "developing"],
                "priority": "critical"
            },
            "company_news": {
                "keywords": ["announces", "reports", "earnings", "acquisition", "merger", 
                           "dividend", "appointment", "resignation", "partnership"],
                "priority": "high"
            },
            "production_updates": {
                "keywords": ["production", "output", "mining", "extraction", "processing",
                           "mill", "plant", "operation", "shutdown", "expansion"],
                "priority": "high"
            },
            "exploration_news": {
                "keywords": ["exploration", "drilling", "discovery", "resource", "reserve",
                           "deposit", "ore", "grade", "assay", "geophysical"],
                "priority": "medium"
            },
            "market_analysis": {
                "keywords": ["analysis", "outlook", "forecast", "trend", "price", "demand",
                           "supply", "market", "commentary", "research"],
                "priority": "medium"
            },
            "regulatory_policy": {
                "keywords": ["regulation", "policy", "government", "permit", "approval",
                           "environmental", "tax", "royalty", "legislation"],
                "priority": "high"
            },
            "financial_results": {
                "keywords": ["quarterly", "annual", "results", "revenue", "profit", "loss",
                           "cash flow", "debt", "financing", "capex"],
                "priority": "high"
            }
        }
        
        # Sentiment indicators
        self.sentiment_indicators = {
            "positive": ["strong", "growth", "increase", "robust", "successful", "profitable",
                        "optimistic", "bullish", "expansion", "breakthrough", "discovery"],
            "negative": ["decline", "weak", "loss", "shutdown", "suspension", "delay",
                        "bearish", "cautious", "challenging", "difficult", "struggle"],
            "neutral": ["stable", "steady", "maintained", "unchanged", "continues",
                       "ongoing", "regular", "normal", "standard"]
        }
    
    def _setup_data_directories(self):
        """Create necessary data directories"""
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "historical",
            self.data_dir / "by_category",
            self.data_dir / datetime.now().strftime("%Y-%m")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create category subdirectories
        for category in self.news_categories.keys():
            (self.data_dir / "by_category" / category).mkdir(exist_ok=True)
    
    async def scrape_all_mining_news(self) -> Dict[str, Any]:
        """Scrape all configured mining news sources"""
        
        print("📰 Starting comprehensive mining news scraping...")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'sources_data': {},
            'categorized_news': {category: [] for category in self.news_categories.keys()},
            'sentiment_analysis': {},
            'duplicate_detection': {},
            'errors': [],
            'summary': {}
        }
        
        all_articles = []
        
        # Scrape each news source
        for source_name, source_config in self.news_sources.items():
            try:
                print(f"📰 Scraping {source_name} ({source_config['specialization']})...")
                source_data = await self._scrape_news_source(source_name, source_config)
                results['sources_data'][source_name] = source_data
                
                # Collect articles for processing
                if source_data.get('articles'):
                    all_articles.extend(source_data['articles'])
                
            except Exception as e:
                error_msg = f"Error scraping {source_name}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Process all collected articles
        if all_articles:
            print(f"🔍 Processing {len(all_articles)} articles...")
            
            # Remove duplicates
            unique_articles = self._remove_duplicate_articles(all_articles)
            results['duplicate_detection'] = {
                'total_articles': len(all_articles),
                'unique_articles': len(unique_articles),
                'duplicates_removed': len(all_articles) - len(unique_articles)
            }
            
            # Categorize articles
            results['categorized_news'] = self._categorize_articles(unique_articles)
            
            # Perform sentiment analysis
            results['sentiment_analysis'] = self._analyze_sentiment(unique_articles)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_news_summary(results)
        
        # Save results
        await self._save_news_data(results)
        
        return results
    
    async def _scrape_news_source(self, source_name: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape news from a specific source"""
        
        source_data = {
            'source_name': source_name,
            'source_specialization': source_config['specialization'],
            'scraped_at': datetime.now().isoformat(),
            'endpoints_scraped': {},
            'articles': [],
            'source_stats': {}
        }
        
        # Scrape each endpoint for this source
        for endpoint_name, endpoint_path in source_config['endpoints'].items():
            try:
                url = source_config['base_url'] + endpoint_path
                
                print(f"  📖 Scraping {endpoint_name}...")
                
                # Configure scraping strategy
                strategy = ScrapingStrategy()
                if source_name in ['sp_global_mining', 'reuters_mining']:
                    strategy.primary = 'playwright'  # These sites are often JS-heavy
                    strategy.fallbacks = ['crawl4ai', 'requests']
                else:
                    strategy.primary = 'crawl4ai'
                    strategy.fallbacks = ['playwright', 'requests']
                
                # Scrape the endpoint
                result = await self.unified_scraper.scrape(url=url, strategy=strategy)
                
                if result.success:
                    # Extract news articles from content
                    articles = self._extract_news_articles(
                        result.content,
                        source_config['selectors'],
                        source_name,
                        endpoint_name,
                        url
                    )
                    
                    source_data['endpoints_scraped'][endpoint_name] = {
                        'url': url,
                        'scraped_at': result.timestamp.isoformat(),
                        'scraper_used': result.scraper_used,
                        'response_time': result.response_time,
                        'articles_found': len(articles)
                    }
                    
                    source_data['articles'].extend(articles)
                
                # Rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"    ❌ Failed to scrape {endpoint_name}: {str(e)}")
                continue
        
        # Generate source statistics
        source_data['source_stats'] = {
            'total_articles': len(source_data['articles']),
            'endpoints_successful': len(source_data['endpoints_scraped']),
            'average_response_time': self._calculate_avg_response_time(source_data['endpoints_scraped'])
        }
        
        return source_data
    
    def _extract_news_articles(self, content: str, selectors: Dict, source: str, 
                              endpoint: str, url: str) -> List[Dict[str, Any]]:
        """Extract individual news articles from page content"""
        
        articles = []
        
        # Extract article text blocks
        article_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*(?:article|post|news)[^"]*"[^>]*>(.*?)</div>',
            r'<section[^>]*class="[^"]*(?:article|story)[^"]*"[^>]*>(.*?)</section>'
        ]
        
        article_blocks = []
        for pattern in article_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            article_blocks.extend(matches)
        
        # If no structured articles found, look for title patterns
        if not article_blocks and endpoint != 'rss_feed':
            title_patterns = [
                r'<h[1-6][^>]*>(.*?)</h[1-6]>',
                r'<a[^>]*href="[^"]*"[^>]*>([^<]{20,150})</a>'
            ]
            
            for pattern in title_patterns:
                titles = re.findall(pattern, content, re.IGNORECASE)
                for title in titles[:10]:  # Limit to first 10
                    if self._is_mining_relevant(title):
                        articles.append(self._create_article_entry(
                            title=title.strip(),
                            content="",
                            source=source,
                            endpoint=endpoint,
                            url=url
                        ))
        else:
            # Process article blocks
            for i, block in enumerate(article_blocks[:20]):  # Limit to 20 articles per endpoint
                article = self._parse_article_block(block, source, endpoint, url)
                if article and self._is_mining_relevant(article.get('title', '') + ' ' + article.get('content', '')):
                    articles.append(article)
        
        return articles
    
    def _parse_article_block(self, block: str, source: str, endpoint: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse an individual article block"""
        
        # Extract title
        title_patterns = [
            r'<h[1-6][^>]*>(.*?)</h[1-6]>',
            r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>',
            r'<span[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</span>'
        ]
        
        title = ""
        for pattern in title_patterns:
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if len(title) > 10:  # Valid title
                    break
        
        if not title:
            return None
        
        # Extract content/summary
        content_patterns = [
            r'<p[^>]*>(.*?)</p>',
            r'<div[^>]*class="[^"]*(?:content|summary|excerpt)[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*(?:summary|excerpt)[^"]*"[^>]*>(.*?)</span>'
        ]
        
        content_parts = []
        for pattern in content_patterns:
            matches = re.findall(pattern, block, re.IGNORECASE | re.DOTALL)
            for match in matches[:3]:  # Limit to first 3 paragraphs
                clean_content = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_content) > 20:
                    content_parts.append(clean_content)
        
        content = ' '.join(content_parts)
        
        # Extract date
        date_patterns = [
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # January 15, 2024
            r'(\d{1,2}/\d{1,2}/\d{4})',    # 01/15/2024
            r'(\d{4}-\d{2}-\d{2})',        # 2024-01-15
        ]
        
        article_date = None
        for pattern in date_patterns:
            match = re.search(pattern, block)
            if match:
                article_date = match.group(1)
                break
        
        return self._create_article_entry(
            title=title,
            content=content,
            source=source,
            endpoint=endpoint,
            url=url,
            date=article_date
        )
    
    def _create_article_entry(self, title: str, content: str, source: str, 
                             endpoint: str, url: str, date: str = None) -> Dict[str, Any]:
        """Create standardized article entry"""
        
        # Generate article hash for duplicate detection
        article_text = f"{title} {content}".lower()
        article_hash = hashlib.md5(article_text.encode()).hexdigest()
        
        return {
            'id': article_hash,
            'title': title,
            'content': content,
            'source': source,
            'endpoint': endpoint,
            'source_url': url,
            'date': date,
            'scraped_at': datetime.now().isoformat(),
            'word_count': len(content.split()) if content else len(title.split()),
            'mining_relevance_score': self._calculate_mining_relevance(title + ' ' + content),
            'preliminary_sentiment': self._get_preliminary_sentiment(title + ' ' + content)
        }
    
    def _is_mining_relevant(self, text: str) -> bool:
        """Check if text is relevant to mining industry"""
        
        text_lower = text.lower()
        
        # Mining-specific keywords
        mining_keywords = [
            'mining', 'mine', 'miner', 'miners', 'mineral', 'minerals',
            'ore', 'deposit', 'reserves', 'resources', 'exploration',
            'drilling', 'extraction', 'processing', 'smelting', 'refining',
            'gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel',
            'zinc', 'iron ore', 'aluminum', 'lithium', 'cobalt', 'uranium',
            'rare earth', 'coal', 'diamond', 'precious metals', 'base metals',
            'commodity', 'commodities'
        ]
        
        # Company indicators
        company_indicators = [
            'corp', 'corporation', 'ltd', 'limited', 'inc', 'incorporated',
            'mines', 'resources', 'metals', 'gold', 'silver', 'copper'
        ]
        
        # Check for mining keywords
        mining_score = sum(1 for keyword in mining_keywords if keyword in text_lower)
        
        # Check for company indicators
        company_score = sum(0.5 for indicator in company_indicators if indicator in text_lower)
        
        # Relevance threshold
        total_score = mining_score + company_score
        return total_score >= 1.0
    
    def _calculate_mining_relevance(self, text: str) -> float:
        """Calculate mining relevance score for an article"""
        
        text_lower = text.lower()
        
        # Weighted keywords
        keyword_weights = {
            'mining': 3, 'mine': 3, 'miner': 2, 'mineral': 2,
            'gold': 2, 'silver': 2, 'copper': 2, 'platinum': 2,
            'exploration': 2, 'drilling': 2, 'production': 2,
            'ore': 1, 'deposit': 1, 'reserves': 1, 'resources': 1,
            'commodity': 1, 'metals': 1, 'extraction': 1
        }
        
        total_score = 0
        text_length = len(text.split())
        
        for keyword, weight in keyword_weights.items():
            count = text_lower.count(keyword)
            total_score += count * weight
        
        # Normalize by text length
        if text_length > 0:
            relevance_score = min(total_score / text_length * 10, 10.0)
        else:
            relevance_score = 0.0
        
        return round(relevance_score, 2)
    
    def _get_preliminary_sentiment(self, text: str) -> str:
        """Get preliminary sentiment analysis of text"""
        
        text_lower = text.lower()
        
        positive_score = sum(1 for word in self.sentiment_indicators['positive'] if word in text_lower)
        negative_score = sum(1 for word in self.sentiment_indicators['negative'] if word in text_lower)
        neutral_score = sum(1 for word in self.sentiment_indicators['neutral'] if word in text_lower)
        
        if positive_score > negative_score and positive_score > neutral_score:
            return 'positive'
        elif negative_score > positive_score and negative_score > neutral_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _remove_duplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on content similarity"""
        
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            article_id = article.get('id')
            if article_id and article_id not in seen_hashes:
                seen_hashes.add(article_id)
                unique_articles.append(article)
        
        return unique_articles
    
    def _categorize_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize articles by content type"""
        
        categorized = {category: [] for category in self.news_categories.keys()}
        
        for article in articles:
            article_text = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            # Check each category
            for category, category_config in self.news_categories.items():
                keyword_matches = sum(1 for keyword in category_config['keywords'] 
                                    if keyword in article_text)
                
                if keyword_matches > 0:
                    article_copy = article.copy()
                    article_copy['category'] = category
                    article_copy['category_match_score'] = keyword_matches
                    categorized[category].append(article_copy)
        
        return categorized
    
    def _analyze_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform sentiment analysis on articles"""
        
        sentiment_stats = {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total_analyzed': len(articles),
            'sentiment_by_source': {},
            'sentiment_by_category': {}
        }
        
        for article in articles:
            sentiment = article.get('preliminary_sentiment', 'neutral')
            sentiment_stats[sentiment] += 1
            
            # Track by source
            source = article.get('source', 'unknown')
            if source not in sentiment_stats['sentiment_by_source']:
                sentiment_stats['sentiment_by_source'][source] = {'positive': 0, 'negative': 0, 'neutral': 0}
            sentiment_stats['sentiment_by_source'][source][sentiment] += 1
        
        return sentiment_stats
    
    def _calculate_avg_response_time(self, endpoints_data: Dict[str, Any]) -> float:
        """Calculate average response time for endpoints"""
        
        response_times = []
        for endpoint_data in endpoints_data.values():
            if endpoint_data.get('response_time'):
                response_times.append(endpoint_data['response_time'])
        
        return sum(response_times) / len(response_times) if response_times else 0.0
    
    def _generate_news_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for scraped news data"""
        
        summary = {
            'total_sources_scraped': len(results['sources_data']),
            'total_articles_found': 0,
            'unique_articles': 0,
            'articles_by_category': {},
            'sentiment_distribution': {},
            'top_sources_by_volume': {},
            'scraping_duration': None
        }
        
        # Count articles
        all_articles = 0
        for source_data in results['sources_data'].values():
            all_articles += source_data.get('source_stats', {}).get('total_articles', 0)
        
        summary['total_articles_found'] = all_articles
        summary['unique_articles'] = results.get('duplicate_detection', {}).get('unique_articles', 0)
        
        # Category breakdown
        for category, articles in results.get('categorized_news', {}).items():
            summary['articles_by_category'][category] = len(articles)
        
        # Sentiment distribution
        sentiment_data = results.get('sentiment_analysis', {})
        summary['sentiment_distribution'] = {
            'positive': sentiment_data.get('positive', 0),
            'negative': sentiment_data.get('negative', 0),
            'neutral': sentiment_data.get('neutral', 0)
        }
        
        # Top sources
        source_volumes = {}
        for source_name, source_data in results['sources_data'].items():
            volume = source_data.get('source_stats', {}).get('total_articles', 0)
            source_volumes[source_name] = volume
        
        summary['top_sources_by_volume'] = dict(sorted(source_volumes.items(), 
                                                      key=lambda x: x[1], reverse=True))
        
        # Calculate scraping duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_duration'] = (end - start).total_seconds()
        
        return summary
    
    async def _save_news_data(self, results: Dict[str, Any]):
        """Save scraped news data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive results
        raw_file = self.data_dir / "raw" / f"mining_news_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save monthly data
        monthly_dir = self.data_dir / datetime.now().strftime("%Y-%m")
        monthly_file = monthly_dir / f"news_{timestamp}.json"
        with open(monthly_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save categorized news
        for category, articles in results.get('categorized_news', {}).items():
            if articles:
                category_file = self.data_dir / "by_category" / category / f"{category}_{timestamp}.json"
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump(articles, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Mining news data saved to:")
        print(f"   Comprehensive: {raw_file}")
        print(f"   Monthly: {monthly_file}")
        print(f"   By category: data/news/by_category/")
    
    async def get_recent_news_by_category(self, category: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent news articles for a specific category"""
        
        category_dir = self.data_dir / "by_category" / category
        if not category_dir.exists():
            return []
        
        recent_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for file_path in category_dir.glob("*.json"):
            try:
                # Check file modification time
                if datetime.fromtimestamp(file_path.stat().st_mtime) > cutoff_time:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        articles = json.load(f)
                    recent_articles.extend(articles)
            except (json.JSONDecodeError, OSError):
                continue
        
        # Sort by scraped_at time
        return sorted(recent_articles, key=lambda x: x.get('scraped_at', ''), reverse=True)
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        await self.unified_scraper.cleanup()


# Convenience functions
async def scrape_specialized_mining_news() -> Dict[str, Any]:
    """Convenience function to scrape specialized mining news"""
    scraper = SpecializedMiningNewsScraper()
    try:
        return await scraper.scrape_all_mining_news()
    finally:
        await scraper.cleanup()


async def get_mining_news_by_category(category: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Convenience function to get recent news by category"""
    scraper = SpecializedMiningNewsScraper()
    try:
        return await scraper.get_recent_news_by_category(category, hours)
    finally:
        await scraper.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        print("📰 Specialized Mining News Scraper - Industry Intelligence")
        print("=" * 60)
        
        scraper = SpecializedMiningNewsScraper()
        
        try:
            # Test comprehensive mining news scraping
            print("\n🚀 Testing comprehensive mining news scraping...")
            results = await scraper.scrape_all_mining_news()
            
            print(f"\n📊 MINING NEWS SUMMARY:")
            print(f"   Total Sources: {results['summary']['total_sources_scraped']}")
            print(f"   Total Articles Found: {results['summary']['total_articles_found']}")
            print(f"   Unique Articles: {results['summary']['unique_articles']}")
            print(f"   Duplicates Removed: {results['duplicate_detection']['duplicates_removed']}")
            print(f"   Scraping Duration: {results['summary']['scraping_duration']:.1f}s")
            
            # Show category breakdown
            print(f"\n📂 ARTICLES BY CATEGORY:")
            for category, count in results['summary']['articles_by_category'].items():
                if count > 0:
                    print(f"   {category.replace('_', ' ').title()}: {count}")
            
            # Show sentiment analysis
            print(f"\n😊 SENTIMENT ANALYSIS:")
            sentiment = results['summary']['sentiment_distribution']
            print(f"   Positive: {sentiment['positive']}")
            print(f"   Negative: {sentiment['negative']}")  
            print(f"   Neutral: {sentiment['neutral']}")
            
            # Show top sources
            print(f"\n🏆 TOP SOURCES BY VOLUME:")
            for source, count in list(results['summary']['top_sources_by_volume'].items())[:5]:
                print(f"   {source.replace('_', ' ').title()}: {count} articles")
            
        finally:
            await scraper.cleanup()
    
    asyncio.run(main())