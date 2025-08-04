#!/usr/bin/env python3
"""
Comprehensive Mining & Canadian News Scraper
Systematically scrapes all mining industry news sources for August 4, 2025
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import os
import sys

# Add src to path for imports
sys.path.append('/Projects/Resource Capital/src')

from scrapers.unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from utils.scraper_config import load_scraper_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Projects/Resource Capital/logs/mining_news_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MiningNewsReport:
    """Structured report for mining news scraping session"""
    session_start: datetime
    session_end: Optional[datetime] = None
    total_sites_scraped: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    total_articles_found: int = 0
    total_mining_keywords: int = 0
    top_mining_companies: List[str] = None
    top_commodities: List[str] = None
    key_insights: List[str] = None
    performance_stats: Dict[str, Any] = None
    raw_data: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.top_mining_companies is None:
            self.top_mining_companies = []
        if self.top_commodities is None:
            self.top_commodities = []
        if self.key_insights is None:
            self.key_insights = []
        if self.performance_stats is None:
            self.performance_stats = {}
        if self.raw_data is None:
            self.raw_data = []

class ComprehensiveMiningNewsScraper:
    """Comprehensive scraper for mining industry news and Canadian business news"""
    
    def __init__(self):
        self.config_manager = load_scraper_config()
        self.unified_scraper = UnifiedScraper(self.config_manager)
        
        # Target websites for mining & Canadian news
        self.target_sites = [
            "BNN Bloomberg",
            "BNN Bloomberg TSX", 
            "BNN Bloomberg Gold",
            "Financial Post Canadian Economy",
            "Reuters Canada",
            "Mining.com",
            "Northern Miner",
            "Canadian Mining Journal",
            "Mining News Net",
            "Northern Ontario Business Mining"
        ]
        
        # Mining intelligence keywords and entities
        self.mining_companies = [
            'Barrick Gold', 'Newmont', 'Kinross Gold', 'Agnico Eagle Mines', 'Franco-Nevada',
            'First Quantum Minerals', 'Lundin Mining', 'Hudbay Minerals', 'Eldorado Gold',
            'Centerra Gold', 'IAMGOLD', 'Kirkland Lake Gold', 'Detour Gold', 'B2Gold',
            'Osisko Gold Royalties', 'Yamana Gold', 'Goldcorp', 'Teck Resources', 'Magna Mining',
            'Pan American Silver', 'Hecla Mining', 'Coeur Mining', 'Sandstorm Gold',
            'Royal Gold', 'Wheaton Precious Metals', 'Canadian National Railway', 'Cameco'
        ]
        
        self.commodities = [
            'gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lead',
            'iron ore', 'aluminum', 'uranium', 'lithium', 'cobalt', 'rare earth elements',
            'molybdenum', 'tungsten', 'tin', 'coal', 'oil', 'natural gas'
        ]
        
        self.mining_keywords = [
            'mining', 'mine', 'miner', 'exploration', 'drilling', 'ore', 'deposit',
            'resource', 'reserve', 'production', 'extraction', 'processing', 'mill',
            'smelting', 'refining', 'concentrate', 'tailings', 'TSX', 'TSXV',
            'Toronto Stock Exchange', 'commodity', 'metal prices', 'earnings', 'guidance'
        ]
        
        # Initialize report
        self.report = MiningNewsReport(session_start=datetime.now())
        
    async def scrape_all_mining_news(self) -> MiningNewsReport:
        """Execute comprehensive scraping of all mining news sources"""
        
        logger.info("🚀 Starting comprehensive mining news scraping session")
        logger.info(f"Target date: August 4, 2025")
        logger.info(f"Target sites: {len(self.target_sites)} mining & Canadian news sources")
        
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return self.report
            
        # Get mining/Canadian news targets from config
        mining_news_targets = []
        if hasattr(self.config_manager, 'config') and 'websites' in self.config_manager.config:
            mining_news_section = self.config_manager.config['websites'].get('mining_canadian_news', [])
            mining_news_targets = [
                target for target in mining_news_section 
                if target.get('enabled', True) and target.get('name') in self.target_sites
            ]
        
        logger.info(f"Found {len(mining_news_targets)} configured targets")
        
        # Execute scraping for each target
        for target_config in mining_news_targets:
            await self._scrape_target_site(target_config)
            
        # Finalize report
        await self._finalize_report()
        
        return self.report
    
    async def _scrape_target_site(self, target_config: Dict[str, Any]):
        """Scrape a specific mining news target site"""
        
        site_name = target_config.get('name', 'Unknown Site')
        logger.info(f"📰 Scraping {site_name}...")
        
        self.report.total_sites_scraped += 1
        site_start_time = time.time()
        
        try:
            # Configure scraping strategy based on site requirements
            strategy = ScrapingStrategy()
            scraper_config = target_config.get('scraper_strategy', {})
            
            strategy.primary = scraper_config.get('primary', 'crawl4ai')
            strategy.fallbacks = scraper_config.get('fallbacks', ['requests', 'playwright'])
            strategy.timeout = 30
            strategy.retries = 3
            strategy.rate_limit = target_config.get('rate_limit', 2.0)
            
            site_results = []
            
            # Scrape all target pages for this site
            for page_config in target_config.get('target_pages', []):
                url = page_config['url']
                page_type = page_config['type']
                
                logger.info(f"  🔍 Scraping {page_type}: {url}")
                
                try:
                    result = await self.unified_scraper.scrape(
                        url=url,
                        target_config=target_config,
                        strategy=strategy
                    )
                    
                    if result.success and len(result.content) > 100:
                        # Extract mining intelligence from the content
                        mining_data = await self._extract_mining_intelligence(
                            result, site_name, page_type
                        )
                        site_results.append(mining_data)
                        
                        logger.info(f"    ✅ Success: {result.word_count:,} words, {result.scraper_used}")
                    else:
                        logger.warning(f"    ❌ Failed: {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"    💥 Error scraping {url}: {str(e)}")
                    continue
            
            # Process site results
            if site_results:
                self.report.successful_scrapes += 1
                self.report.raw_data.extend(site_results)
                
                # Count articles and analyze content
                total_articles = sum(len(data.get('article_links', [])) for data in site_results)
                self.report.total_articles_found += total_articles
                
                site_response_time = time.time() - site_start_time
                
                logger.info(f"  📊 {site_name} Summary:")
                logger.info(f"    - Pages scraped: {len(site_results)}")
                logger.info(f"    - Articles found: {total_articles}")
                logger.info(f"    - Response time: {site_response_time:.1f}s")
                
            else:
                self.report.failed_scrapes += 1
                logger.warning(f"  ⚠️ No successful data extraction from {site_name}")
                
        except Exception as e:
            self.report.failed_scrapes += 1
            logger.error(f"💥 Failed to scrape {site_name}: {str(e)}")
    
    async def _extract_mining_intelligence(self, result: ScrapingResult, source: str, page_type: str) -> Dict[str, Any]:
        """Extract mining-specific intelligence from scraped content"""
        
        content = result.content.lower()
        
        # Extract company mentions
        companies_mentioned = []
        for company in self.mining_companies:
            if company.lower() in content:
                companies_mentioned.append(company)
        
        # Extract commodity mentions
        commodities_mentioned = []
        for commodity in self.commodities:
            if commodity in content:
                commodities_mentioned.append(commodity)
        
        # Extract mining keywords
        mining_keywords_found = []
        for keyword in self.mining_keywords:
            if keyword.lower() in content:
                mining_keywords_found.append(keyword)
        
        # Extract article links (headlines/URLs)
        article_links = self._extract_article_links(result.content)
        
        # Extract financial indicators
        financial_indicators = self._extract_financial_indicators(result.content)
        
        # Extract market data mentions
        market_data = self._extract_market_data(result.content)
        
        # Calculate relevance score
        relevance_score = (
            len(companies_mentioned) * 3 +
            len(commodities_mentioned) * 2 +
            len(mining_keywords_found) * 1
        )
        
        mining_data = {
            'source': source,
            'page_type': page_type,
            'url': result.url,
            'title': result.title,
            'content_length': len(result.content),
            'word_count': result.word_count,
            'scraper_used': result.scraper_used,
            'response_time': result.response_time,
            'scraped_at': result.timestamp.isoformat(),
            'relevance_score': relevance_score,
            
            # Mining intelligence
            'companies_mentioned': companies_mentioned,
            'commodities_mentioned': commodities_mentioned,
            'mining_keywords_found': mining_keywords_found,
            'article_links': article_links,
            'financial_indicators': financial_indicators,
            'market_data': market_data,
            
            # Content analysis
            'content_preview': result.content[:500] + "..." if len(result.content) > 500 else result.content,
            'metadata': result.metadata
        }
        
        # Update global counters
        self.report.total_mining_keywords += len(mining_keywords_found)
        
        return mining_data
    
    def _extract_article_links(self, content: str) -> List[str]:
        """Extract article headlines and links from content"""
        import re
        
        # Look for news article patterns
        article_patterns = [
            r'https?://[^\s]+/(?:news|article|story|press-release)/[^\s]+',
            r'https?://[^\s]+/\d{4}/\d{2}/\d{2}/[^\s]+',
            r'https?://[^\s]+/[^\s]*(?:mining|gold|copper|tsx)[^\s]*'
        ]
        
        links = []
        for pattern in article_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            links.extend(matches)
        
        # Also extract headline-like text patterns
        headline_patterns = [
            r'[A-Z][^.!?]*(?:mining|gold|silver|copper|TSX|earnings|announces)[^.!?]*[.!?]',
            r'[A-Z][^.!?]*(?:million|billion|\$)[^.!?]*(?:mining|gold|copper)[^.!?]*[.!?]'
        ]
        
        for pattern in headline_patterns:
            matches = re.findall(pattern, content)
            links.extend(matches[:10])  # Limit headlines
        
        return list(set(links))  # Remove duplicates
    
    def _extract_financial_indicators(self, content: str) -> List[str]:
        """Extract financial indicators and metrics"""
        import re
        
        financial_patterns = [
            r'\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)',
            r'\d+(?:\.\d+)?%\s*(?:up|down|higher|lower)',
            r'earnings|revenue|profit|loss|EBITDA|cash flow|guidance',
            r'Q[1-4]\s*\d{4}|quarterly|annual|year-over-year'
        ]
        
        indicators = []
        content_lower = content.lower()
        
        for pattern in financial_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            indicators.extend(matches)
        
        return list(set(indicators))
    
    def _extract_market_data(self, content: str) -> Dict[str, List[str]]:
        """Extract market data and trading information"""
        import re
        
        market_data = {
            'stock_prices': [],
            'volume_data': [],
            'market_moves': [],
            'tsx_mentions': []
        }
        
        # Stock price patterns
        price_patterns = [
            r'\$\d+(?:\.\d+)?\s*(?:per share|CAD|USD)',
            r'(?:up|down|gained|lost)\s*\d+(?:\.\d+)?%',
            r'(?:high|low)\s*of\s*\$\d+(?:\.\d+)?'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            market_data['stock_prices'].extend(matches)
        
        # TSX mentions
        tsx_patterns = [
            r'TSX[:\s]+[A-Z]{1,5}',
            r'Toronto Stock Exchange',
            r'TSXV[:\s]+[A-Z]{1,5}'
        ]
        
        for pattern in tsx_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            market_data['tsx_mentions'].extend(matches)
        
        return market_data
    
    async def _finalize_report(self):
        """Finalize the mining news report with analysis"""
        
        self.report.session_end = datetime.now()
        
        # Analyze top companies and commodities mentioned
        company_mentions = {}
        commodity_mentions = {}
        
        for data in self.report.raw_data:
            for company in data.get('companies_mentioned', []):
                company_mentions[company] = company_mentions.get(company, 0) + 1
            
            for commodity in data.get('commodities_mentioned', []):
                commodity_mentions[commodity] = commodity_mentions.get(commodity, 0) + 1
        
        # Sort by frequency
        self.report.top_mining_companies = sorted(
            company_mentions.items(), key=lambda x: x[1], reverse=True
        )[:10]
        
        self.report.top_commodities = sorted(
            commodity_mentions.items(), key=lambda x: x[1], reverse=True
        )[:10]
        
        # Generate key insights
        self.report.key_insights = await self._generate_key_insights()
        
        # Performance statistics
        session_duration = (self.report.session_end - self.report.session_start).total_seconds()
        success_rate = (self.report.successful_scrapes / self.report.total_sites_scraped * 100) if self.report.total_sites_scraped > 0 else 0
        
        self.report.performance_stats = {
            'session_duration_seconds': session_duration,
            'success_rate_percent': round(success_rate, 1),
            'average_response_time': round(sum(data.get('response_time', 0) for data in self.report.raw_data) / len(self.report.raw_data), 2) if self.report.raw_data else 0,
            'total_content_words': sum(data.get('word_count', 0) for data in self.report.raw_data),
            'highest_relevance_score': max((data.get('relevance_score', 0) for data in self.report.raw_data), default=0)
        }
        
        logger.info("📊 Mining News Scraping Session Complete")
        logger.info(f"   Total sites: {self.report.total_sites_scraped}")
        logger.info(f"   Successful: {self.report.successful_scrapes}")
        logger.info(f"   Success rate: {success_rate:.1f}%")
        logger.info(f"   Articles found: {self.report.total_articles_found}")
        logger.info(f"   Session duration: {session_duration:.1f}s")
    
    async def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the scraped mining news data"""
        
        insights = []
        
        # Top company insight
        if self.report.top_mining_companies:
            top_company, mentions = self.report.top_mining_companies[0]
            insights.append(f"{top_company} was the most mentioned mining company with {mentions} references across news sources")
        
        # Top commodity insight
        if self.report.top_commodities:
            top_commodity, mentions = self.report.top_commodities[0]
            insights.append(f"{top_commodity.title()} was the most discussed commodity with {mentions} mentions")
        
        # Performance insight
        insights.append(f"Successfully scraped {self.report.successful_scrapes} out of {self.report.total_sites_scraped} target mining news sources")
        
        # Content volume insight
        total_words = sum(data.get('word_count', 0) for data in self.report.raw_data)
        insights.append(f"Collected {total_words:,} words of mining industry content and analysis")
        
        # Market focus insight
        tsx_mentions = sum(1 for data in self.report.raw_data 
                          if any('tsx' in keyword.lower() for keyword in data.get('mining_keywords_found', [])))
        if tsx_mentions > 0:
            insights.append(f"Found {tsx_mentions} articles with TSX/Toronto Stock Exchange references")
        
        return insights
    
    async def save_report(self, output_dir: str = "/Projects/Resource Capital/reports/2025-08-04"):
        """Save the comprehensive mining news report"""
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save raw JSON data
        json_path = os.path.join(output_dir, "mining_news_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.report), f, indent=2, ensure_ascii=False, default=str)
        
        # Save performance summary
        summary_path = os.path.join(output_dir, "mining_news_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("MINING & CANADIAN NEWS SCRAPING REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: August 4, 2025\n")
            f.write(f"Session: {self.report.session_start} to {self.report.session_end}\n\n")
            
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total sites targeted: {self.report.total_sites_scraped}\n")
            f.write(f"Successful scrapes: {self.report.successful_scrapes}\n")
            f.write(f"Failed scrapes: {self.report.failed_scrapes}\n")
            f.write(f"Success rate: {self.report.performance_stats.get('success_rate_percent', 0)}%\n")
            f.write(f"Total articles found: {self.report.total_articles_found}\n")
            f.write(f"Total content words: {self.report.performance_stats.get('total_content_words', 0):,}\n\n")
            
            f.write("TOP MINING COMPANIES MENTIONED\n")
            f.write("-" * 32 + "\n")
            for company, count in self.report.top_mining_companies:
                f.write(f"{company}: {count} mentions\n")
            
            f.write("\nTOP COMMODITIES DISCUSSED\n")
            f.write("-" * 25 + "\n")
            for commodity, count in self.report.top_commodities:
                f.write(f"{commodity.title()}: {count} mentions\n")
            
            f.write("\nKEY INSIGHTS\n")
            f.write("-" * 12 + "\n")
            for i, insight in enumerate(self.report.key_insights, 1):
                f.write(f"{i}. {insight}\n")
        
        logger.info(f"💾 Reports saved:")
        logger.info(f"   📄 Raw data: {json_path}")
        logger.info(f"   📄 Summary: {summary_path}")
        
        return json_path, summary_path
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.unified_scraper.cleanup()

async def main():
    """Execute comprehensive mining news scraping"""
    
    print("🚀 COMPREHENSIVE MINING & CANADIAN NEWS SCRAPER")
    print("=" * 60)
    print("Target Date: August 4, 2025")
    print("Target Sources: 10 Mining & Canadian News Websites")
    print("=" * 60)
    
    scraper = ComprehensiveMiningNewsScraper()
    
    try:
        # Execute comprehensive scraping
        report = await scraper.scrape_all_mining_news()
        
        # Save reports
        json_path, summary_path = await scraper.save_report()
        
        # Display final summary
        print("\n🎯 SCRAPING SESSION COMPLETE")
        print("=" * 40)
        print(f"Sites scraped: {report.total_sites_scraped}")
        print(f"Successful: {report.successful_scrapes}")
        print(f"Success rate: {report.performance_stats.get('success_rate_percent', 0)}%")
        print(f"Articles found: {report.total_articles_found}")
        print(f"Mining keywords: {report.total_mining_keywords}")
        
        print(f"\n📊 TOP MINING COMPANIES:")
        for company, count in report.top_mining_companies[:5]:
            print(f"   {company}: {count} mentions")
        
        print(f"\n🏗️ TOP COMMODITIES:")
        for commodity, count in report.top_commodities[:5]:
            print(f"   {commodity.title()}: {count} mentions")
        
        print(f"\n💡 KEY INSIGHTS:")
        for insight in report.key_insights:
            print(f"   • {insight}")
        
        print(f"\n📁 Reports saved to: /Projects/Resource Capital/reports/2025-08-04/")
        
        return report
        
    except Exception as e:
        logger.error(f"💥 Critical error in mining news scraping: {str(e)}")
        raise
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())