#!/usr/bin/env python3
"""
Simplified Mining & Canadian News Scraper
Systematically scrapes mining industry news sources using basic web scraping
"""

import asyncio
import json
import logging
import time
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Simple result format for scraped data"""
    url: str
    success: bool
    content: str = ""
    title: str = ""
    error_message: str = ""
    response_time: float = 0.0
    word_count: int = 0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.content:
            self.word_count = len(self.content.split())

@dataclass
class MiningNewsReport:
    """Report for mining news scraping session"""
    session_start: datetime
    session_end: Optional[datetime] = None
    total_sites_scraped: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    total_articles_found: int = 0
    key_insights: List[str] = None
    raw_data: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.key_insights is None:
            self.key_insights = []
        if self.raw_data is None:
            self.raw_data = []

class SimplifiedMiningNewsScraper:
    """Simplified scraper for mining industry news sources"""
    
    def __init__(self):
        # Target websites for mining & Canadian news
        self.target_urls = [
            ("BNN Bloomberg", "https://www.bnnbloomberg.ca/"),
            ("BNN Bloomberg TSX", "https://www.bnnbloomberg.ca/markets/tsx/"),
            ("BNN Bloomberg Gold", "https://www.bnnbloomberg.ca/markets/gold/"),
            ("Financial Post Canadian Economy", "https://financialpost.com/tag/canadian-economy/"),
            ("Reuters Canada", "https://www.reuters.com/world/canada/"),
            ("Mining.com", "https://www.mining.com/"),
            ("Northern Miner", "https://www.northernminer.com/"),
            ("Canadian Mining Journal", "https://www.canadianminingjournal.com/"),
            ("Mining News Net", "https://www.miningnews.net/"),
            ("Northern Ontario Business Mining", "https://www.northernontariobusiness.com/industry-news/mining")
        ]
        
        # Mining intelligence keywords
        self.mining_companies = [
            'Barrick Gold', 'Newmont', 'Kinross Gold', 'Agnico Eagle', 'Franco-Nevada',
            'First Quantum', 'Lundin Mining', 'Hudbay Minerals', 'Eldorado Gold',
            'Centerra Gold', 'IAMGOLD', 'Kirkland Lake', 'B2Gold', 'Teck Resources',
            'Pan American Silver', 'Wheaton Precious Metals', 'Canadian National Railway'
        ]
        
        self.commodities = [
            'gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc',
            'lead', 'iron ore', 'aluminum', 'uranium', 'lithium', 'cobalt'
        ]
        
        self.mining_keywords = [
            'mining', 'mine', 'miner', 'exploration', 'drilling', 'ore', 'deposit',
            'resource', 'reserve', 'production', 'TSX', 'TSXV', 'earnings', 'guidance'
        ]
        
        # Initialize report
        self.report = MiningNewsReport(session_start=datetime.now())
        
        # HTTP session configuration
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def scrape_all_mining_news(self) -> MiningNewsReport:
        """Execute comprehensive scraping of all mining news sources"""
        
        logger.info("🚀 Starting simplified mining news scraping session")
        logger.info(f"Target date: August 4, 2025")
        logger.info(f"Target sites: {len(self.target_urls)} mining & Canadian news sources")
        
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            for site_name, url in self.target_urls:
                await self._scrape_site(session, site_name, url)
                # Rate limiting between sites
                await asyncio.sleep(2)
        
        # Finalize report
        await self._finalize_report()
        return self.report
    
    async def _scrape_site(self, session: aiohttp.ClientSession, site_name: str, url: str):
        """Scrape a specific mining news site"""
        
        logger.info(f"📰 Scraping {site_name}...")
        self.report.total_sites_scraped += 1
        start_time = time.time()
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    response_time = time.time() - start_time
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else site_name
                    
                    # Extract main content
                    content = self._extract_content(soup)
                    
                    if len(content) > 100:  # Minimum content threshold
                        # Extract mining intelligence
                        mining_data = await self._extract_mining_intelligence(
                            url, site_name, title, content, response_time
                        )
                        
                        self.report.raw_data.append(mining_data)
                        self.report.successful_scrapes += 1
                        
                        logger.info(f"  ✅ Success: {len(content.split()):,} words")
                    else:
                        self.report.failed_scrapes += 1
                        logger.warning(f"  ❌ Insufficient content: {len(content)} chars")
                        
                else:
                    self.report.failed_scrapes += 1
                    logger.warning(f"  ❌ HTTP {response.status}")
                    
        except Exception as e:
            self.report.failed_scrapes += 1
            logger.error(f"  💥 Error: {str(e)}")
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Try common content selectors
        content_selectors = [
            'article', '.article-content', '.content', '.post-content',
            '.entry-content', '.story-body', 'main', '.main-content',
            '.article-body', '.news-content', '.text-content'
        ]
        
        content_parts = []
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if len(text) > 100:  # Only substantial content
                    content_parts.append(text)
        
        # If no specific content found, use body text
        if not content_parts:
            body = soup.find('body')
            if body:
                content_parts.append(body.get_text().strip())
        
        return '\n\n'.join(content_parts)
    
    async def _extract_mining_intelligence(self, url: str, source: str, title: str, 
                                         content: str, response_time: float) -> Dict[str, Any]:
        """Extract mining-specific intelligence from content"""
        
        content_lower = content.lower()
        
        # Extract company mentions
        companies_mentioned = []
        for company in self.mining_companies:
            if company.lower() in content_lower:
                companies_mentioned.append(company)
        
        # Extract commodity mentions
        commodities_mentioned = []
        for commodity in self.commodities:
            if commodity in content_lower:
                commodities_mentioned.append(commodity)
        
        # Extract mining keywords
        mining_keywords_found = []
        for keyword in self.mining_keywords:
            if keyword.lower() in content_lower:
                mining_keywords_found.append(keyword)
        
        # Extract headlines and key phrases
        headlines = self._extract_headlines(content)
        
        # Extract financial data
        financial_data = self._extract_financial_data(content)
        
        # Calculate relevance score
        relevance_score = (
            len(companies_mentioned) * 3 +
            len(commodities_mentioned) * 2 +
            len(mining_keywords_found) * 1
        )
        
        # Count articles (estimate based on content structure)
        article_count = max(1, len(headlines))
        self.report.total_articles_found += article_count
        
        return {
            'source': source,
            'url': url,
            'title': title,
            'content_length': len(content),
            'word_count': len(content.split()),
            'response_time': response_time,
            'scraped_at': datetime.now().isoformat(),
            'relevance_score': relevance_score,
            'article_count': article_count,
            
            # Mining intelligence
            'companies_mentioned': companies_mentioned,
            'commodities_mentioned': commodities_mentioned,
            'mining_keywords_found': mining_keywords_found,
            'headlines': headlines[:10],  # Top 10 headlines
            'financial_data': financial_data,
            
            # Content preview
            'content_preview': content[:1000] + "..." if len(content) > 1000 else content
        }
    
    def _extract_headlines(self, content: str) -> List[str]:
        """Extract potential headlines from content"""
        
        # Look for headline patterns
        headline_patterns = [
            r'[A-Z][^.!?]*(?:mining|gold|silver|copper|TSX|announces|reports)[^.!?]*[.!?]',
            r'[A-Z][^.!?]*(?:million|billion|\$)[^.!?]*(?:mining|gold|copper)[^.!?]*[.!?]',
            r'[A-Z][^.!?]*(?:earnings|revenue|guidance|production)[^.!?]*[.!?]'
        ]
        
        headlines = []
        for pattern in headline_patterns:
            matches = re.findall(pattern, content)
            headlines.extend(matches)
        
        # Also look for text in title case (likely headlines)
        lines = content.split('\n')
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if (len(line) > 20 and len(line) < 200 and 
                any(keyword in line.lower() for keyword in ['mining', 'gold', 'tsx', 'announces'])):
                headlines.append(line)
        
        return list(set(headlines))  # Remove duplicates
    
    def _extract_financial_data(self, content: str) -> List[str]:
        """Extract financial indicators and data"""
        
        financial_patterns = [
            r'\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)',
            r'\d+(?:\.\d+)?%\s*(?:up|down|higher|lower|increase|decrease)',
            r'Q[1-4]\s*\d{4}|quarterly|annual|year-over-year',
            r'earnings|revenue|profit|EBITDA|cash flow|guidance'
        ]
        
        financial_data = []
        for pattern in financial_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            financial_data.extend(matches)
        
        return list(set(financial_data))
    
    async def _finalize_report(self):
        """Finalize the mining news report"""
        
        self.report.session_end = datetime.now()
        
        # Generate insights
        company_mentions = {}
        commodity_mentions = {}
        
        for data in self.report.raw_data:
            for company in data.get('companies_mentioned', []):
                company_mentions[company] = company_mentions.get(company, 0) + 1
            
            for commodity in data.get('commodities_mentioned', []):
                commodity_mentions[commodity] = commodity_mentions.get(commodity, 0) + 1
        
        # Generate key insights
        insights = []
        
        if company_mentions:
            top_company = max(company_mentions, key=company_mentions.get)
            insights.append(f"{top_company} was mentioned most frequently across mining news sources")
        
        if commodity_mentions:
            top_commodity = max(commodity_mentions, key=commodity_mentions.get)
            insights.append(f"{top_commodity.title()} was the most discussed commodity")
        
        session_duration = (self.report.session_end - self.report.session_start).total_seconds()
        success_rate = (self.report.successful_scrapes / self.report.total_sites_scraped * 100) if self.report.total_sites_scraped > 0 else 0
        
        insights.extend([
            f"Successfully scraped {self.report.successful_scrapes} out of {self.report.total_sites_scraped} mining news sources ({success_rate:.1f}% success rate)",
            f"Collected approximately {self.report.total_articles_found} mining industry articles and news items",
            f"Session completed in {session_duration:.1f} seconds"
        ])
        
        self.report.key_insights = insights
        
        logger.info("📊 Mining News Scraping Session Complete")
        logger.info(f"   Success rate: {success_rate:.1f}%")
        logger.info(f"   Articles found: {self.report.total_articles_found}")
    
    async def save_report(self, output_dir: str = "/Projects/Resource Capital/reports/2025-08-04"):
        """Save the mining news report"""
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save raw JSON data
        json_path = os.path.join(output_dir, "mining_news_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.report), f, indent=2, ensure_ascii=False, default=str)
        
        # Save summary report
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
            success_rate = (self.report.successful_scrapes / self.report.total_sites_scraped * 100) if self.report.total_sites_scraped > 0 else 0
            f.write(f"Success rate: {success_rate:.1f}%\n")
            f.write(f"Total articles found: {self.report.total_articles_found}\n\n")
            
            f.write("MINING INTELLIGENCE SUMMARY\n")
            f.write("-" * 28 + "\n")
            
            # Aggregate data
            all_companies = []
            all_commodities = []
            total_words = 0
            
            for data in self.report.raw_data:
                all_companies.extend(data.get('companies_mentioned', []))
                all_commodities.extend(data.get('commodities_mentioned', []))
                total_words += data.get('word_count', 0)
            
            # Count mentions
            company_counts = {}
            for company in all_companies:
                company_counts[company] = company_counts.get(company, 0) + 1
            
            commodity_counts = {}
            for commodity in all_commodities:
                commodity_counts[commodity] = commodity_counts.get(commodity, 0) + 1
            
            f.write("Top Mining Companies Mentioned:\n")
            for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {company}: {count} mentions\n")
            
            f.write("\nTop Commodities Discussed:\n")
            for commodity, count in sorted(commodity_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {commodity.title()}: {count} mentions\n")
            
            f.write(f"\nTotal content words collected: {total_words:,}\n")
            
            f.write("\nKEY INSIGHTS\n")
            f.write("-" * 12 + "\n")
            for i, insight in enumerate(self.report.key_insights, 1):
                f.write(f"{i}. {insight}\n")
            
            f.write("\nSITE-BY-SITE PERFORMANCE\n")
            f.write("-" * 24 + "\n")
            for data in self.report.raw_data:
                f.write(f"\n{data['source']}:\n")
                f.write(f"  - Content: {data['word_count']:,} words\n")
                f.write(f"  - Response time: {data['response_time']:.1f}s\n")
                f.write(f"  - Companies mentioned: {len(data.get('companies_mentioned', []))}\n")
                f.write(f"  - Commodities mentioned: {len(data.get('commodities_mentioned', []))}\n")
                f.write(f"  - Relevance score: {data.get('relevance_score', 0)}\n")
        
        logger.info(f"💾 Reports saved:")
        logger.info(f"   📄 Raw data: {json_path}")
        logger.info(f"   📄 Summary: {summary_path}")
        
        return json_path, summary_path

async def main():
    """Execute mining news scraping"""
    
    print("🚀 MINING & CANADIAN NEWS SCRAPER")
    print("=" * 50)
    print("Target Date: August 4, 2025")
    print("Target Sources: 10 Mining & Canadian News Websites")
    print("=" * 50)
    
    scraper = SimplifiedMiningNewsScraper()
    
    try:
        # Execute scraping
        report = await scraper.scrape_all_mining_news()
        
        # Save reports
        json_path, summary_path = await scraper.save_report()
        
        # Display summary
        print("\n🎯 SCRAPING SESSION COMPLETE")
        print("=" * 40)
        print(f"Sites scraped: {report.total_sites_scraped}")
        print(f"Successful: {report.successful_scrapes}")
        success_rate = (report.successful_scrapes / report.total_sites_scraped * 100) if report.total_sites_scraped > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Articles found: {report.total_articles_found}")
        
        print(f"\n💡 KEY INSIGHTS:")
        for insight in report.key_insights:
            print(f"   • {insight}")
        
        print(f"\n📁 Reports saved to: /Projects/Resource Capital/reports/2025-08-04/")
        
        return report
        
    except Exception as e:
        logger.error(f"💥 Error in mining news scraping: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())