#!/usr/bin/env python3
"""
Mining News Scraper
Specialized scraper for mining industry news sources using unified scraper system
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from .unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from utils.scraper_config import load_scraper_config

class MiningNewsScraper:
    """Specialized scraper for mining industry news"""
    
    def __init__(self):
        self.config_manager = load_scraper_config()
        self.unified_scraper = UnifiedScraper(self.config_manager)
        
        # News-specific targets
        self.news_targets = [
            'Northern Miner',
            'Mining.com', 
            'Reuters'
        ]
    
    async def scrape_all_news(self) -> List[Dict[str, Any]]:
        """Scrape all mining news sources"""
        
        results = []
        
        if not self.config_manager:
            return results
        
        # Get news targets
        targets = [
            self.config_manager.get_target_by_name(name) 
            for name in self.news_targets
        ]
        targets = [t for t in targets if t and t.enabled]
        
        for target in targets:
            print(f"Scraping mining news from {target.name}...")
            
            target_results = await self._scrape_target(target)
            results.extend(target_results)
            
            # Rate limiting between targets
            await asyncio.sleep(target.rate_limit)
        
        return results
    
    async def _scrape_target(self, target) -> List[Dict[str, Any]]:
        """Scrape a specific news target"""
        
        results = []
        
        for page_config in target.target_pages:
            url = page_config['url']
            page_type = page_config['type']
            
            # Configure strategy for news scraping
            strategy = ScrapingStrategy()
            if target.scraper_strategy:
                strategy.primary = target.scraper_strategy.get('primary', 'crawl4ai')
                strategy.fallbacks = target.scraper_strategy.get('fallbacks', ['requests', 'playwright'])
            
            try:
                result = await self.unified_scraper.scrape(
                    url=url,
                    target_config=target.__dict__,
                    strategy=strategy
                )
                
                if result.success:
                    # Extract news-specific information
                    news_data = self._extract_news_data(result, target.name, page_type)
                    results.append(news_data)
                    
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
        
        return results
    
    def _extract_news_data(self, result: ScrapingResult, source: str, page_type: str) -> Dict[str, Any]:
        """Extract and structure news data"""
        
        return {
            'source': source,
            'page_type': page_type,
            'url': result.url,
            'title': result.title,
            'content': result.content,
            'word_count': result.word_count,
            'scraper_used': result.scraper_used,
            'response_time': result.response_time,
            'scraped_at': result.timestamp.isoformat(),
            'metadata': result.metadata,
            
            # News-specific extractions
            'article_links': self._extract_article_links(result.content),
            'companies_mentioned': self._extract_companies(result.content),
            'commodities_mentioned': self._extract_commodities(result.content),
            'financial_keywords': self._extract_financial_keywords(result.content)
        }
    
    def _extract_article_links(self, content: str) -> List[str]:
        """Extract article links from content"""
        import re
        
        # Look for mining-related article URLs
        article_patterns = [
            r'https?://[^\s]+/(?:news|article|story)/[^\s]+',
            r'https?://[^\s]+/\d{4}/\d{2}/[^\s]+'
        ]
        
        links = []
        for pattern in article_patterns:
            matches = re.findall(pattern, content)
            links.extend(matches)
        
        return list(set(links))  # Remove duplicates
    
    def _extract_companies(self, content: str) -> List[str]:
        """Extract mining company mentions"""
        companies = [
            'Barrick Gold', 'Newmont', 'Kinross', 'Agnico Eagle', 'Franco Nevada',
            'First Quantum', 'Lundin Mining', 'Hudbay Minerals', 'Eldorado Gold',
            'Centerra Gold', 'IAMGOLD', 'Kirkland Lake', 'Detour Gold',
            'Osisko', 'Yamana', 'Goldcorp', 'Teck Resources', 'Magna Mining'
        ]
        
        mentioned = []
        content_lower = content.lower()
        
        for company in companies:
            if company.lower() in content_lower:
                mentioned.append(company)
        
        return mentioned
    
    def _extract_commodities(self, content: str) -> List[str]:
        """Extract commodity mentions"""
        commodities = [
            'gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel',
            'zinc', 'lead', 'iron ore', 'aluminum', 'uranium', 'lithium',
            'cobalt', 'rare earth', 'molybdenum'
        ]
        
        mentioned = []
        content_lower = content.lower()
        
        for commodity in commodities:
            if commodity in content_lower:
                mentioned.append(commodity)
        
        return mentioned
    
    def _extract_financial_keywords(self, content: str) -> List[str]:
        """Extract financial keywords"""
        keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'ebitda', 'cash flow',
            'quarterly', 'guidance', 'dividend', 'acquisition', 'merger',
            'financing', 'investment'
        ]
        
        found = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword in content_lower:
                found.append(keyword)
        
        return found
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.unified_scraper.cleanup()

# Convenience function
async def scrape_mining_news() -> List[Dict[str, Any]]:
    """Convenience function to scrape all mining news"""
    scraper = MiningNewsScraper()
    try:
        return await scraper.scrape_all_news()
    finally:
        await scraper.cleanup()

# Example usage
if __name__ == "__main__":
    async def main():
        print("🗞️ Mining News Scraper")
        print("=" * 40)
        
        news_data = await scrape_mining_news()
        
        print(f"Scraped {len(news_data)} news sources")
        
        for item in news_data:
            print(f"\n📰 {item['source']} - {item['page_type']}")
            print(f"   Content: {item['word_count']:,} words")
            print(f"   Scraper: {item['scraper_used']}")
            print(f"   Companies: {len(item['companies_mentioned'])}")
            print(f"   Commodities: {len(item['commodities_mentioned'])}")
    
    asyncio.run(main())