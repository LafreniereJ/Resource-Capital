#!/usr/bin/env python3
"""
Financial Data Scraper
Specialized scraper for financial and market data sources using unified scraper system
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from .unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from utils.scraper_config import load_scraper_config

class FinancialDataScraper:
    """Specialized scraper for financial and market data"""
    
    def __init__(self):
        self.config_manager = load_scraper_config()
        self.unified_scraper = UnifiedScraper(self.config_manager)
        
        # Financial data targets
        self.financial_targets = [
            'Trading Economics - Commodities',
            'Trading Economics - Canada Indicators'
        ]
    
    async def scrape_all_financial_data(self) -> List[Dict[str, Any]]:
        """Scrape all financial data sources"""
        
        results = []
        
        if not self.config_manager:
            return results
        
        # Get financial targets
        targets = [
            self.config_manager.get_target_by_name(name) 
            for name in self.financial_targets
        ]
        targets = [t for t in targets if t and t.enabled]
        
        for target in targets:
            print(f"Scraping financial data from {target.name}...")
            
            target_results = await self._scrape_target(target)
            results.extend(target_results)
            
            # Rate limiting between targets
            await asyncio.sleep(target.rate_limit)
        
        return results
    
    async def scrape_commodity_prices(self) -> Optional[Dict[str, Any]]:
        """Specifically scrape commodity price data"""
        
        target = self.config_manager.get_target_by_name('Trading Economics - Commodities')
        if not target:
            return None
        
        # Find commodity price pages
        commodity_pages = [
            page for page in target.target_pages 
            if 'commodity' in page.get('type', '').lower()
        ]
        
        results = []
        
        for page_config in commodity_pages:
            url = page_config['url']
            
            strategy = ScrapingStrategy()
            if target.scraper_strategy:
                strategy.primary = target.scraper_strategy.get('primary', 'crawl4ai')
                strategy.fallbacks = target.scraper_strategy.get('fallbacks', ['playwright', 'requests'])
            
            try:
                result = await self.unified_scraper.scrape(
                    url=url,
                    target_config=target.__dict__,
                    strategy=strategy
                )
                
                if result.success:
                    price_data = self._extract_commodity_prices(result)
                    if price_data:
                        results.append(price_data)
                        
            except Exception as e:
                print(f"Error scraping commodity prices from {url}: {str(e)}")
                continue
        
        return {
            'source': 'Trading Economics',
            'data_type': 'commodity_prices',
            'scraped_at': datetime.now().isoformat(),
            'prices': results
        }
    
    async def scrape_canadian_indicators(self) -> Optional[Dict[str, Any]]:
        """Specifically scrape Canadian economic indicators"""
        
        target = self.config_manager.get_target_by_name('Trading Economics - Canada Indicators')
        if not target:
            return None
        
        # Find indicator pages
        indicator_pages = [
            page for page in target.target_pages 
            if 'indicator' in page.get('type', '').lower()
        ]
        
        results = []
        
        for page_config in indicator_pages:
            url = page_config['url']
            
            strategy = ScrapingStrategy()
            if target.scraper_strategy:
                strategy.primary = target.scraper_strategy.get('primary', 'crawl4ai')
                strategy.fallbacks = target.scraper_strategy.get('fallbacks', ['playwright', 'requests'])
            
            try:
                result = await self.unified_scraper.scrape(
                    url=url,
                    target_config=target.__dict__,
                    strategy=strategy
                )
                
                if result.success:
                    indicator_data = self._extract_economic_indicators(result)
                    if indicator_data:
                        results.append(indicator_data)
                        
            except Exception as e:
                print(f"Error scraping indicators from {url}: {str(e)}")
                continue
        
        return {
            'source': 'Trading Economics',
            'data_type': 'canadian_indicators',
            'scraped_at': datetime.now().isoformat(),
            'indicators': results
        }
    
    async def _scrape_target(self, target) -> List[Dict[str, Any]]:
        """Scrape a specific financial target"""
        
        results = []
        
        for page_config in target.target_pages:
            url = page_config['url']
            page_type = page_config['type']
            
            # Configure strategy for financial data scraping
            strategy = ScrapingStrategy()
            if target.scraper_strategy:
                strategy.primary = target.scraper_strategy.get('primary', 'crawl4ai')
                strategy.fallbacks = target.scraper_strategy.get('fallbacks', ['playwright', 'requests'])
            
            try:
                result = await self.unified_scraper.scrape(
                    url=url,
                    target_config=target.__dict__,
                    strategy=strategy
                )
                
                if result.success:
                    # Extract financial-specific information
                    financial_data = self._extract_financial_data(result, target.name, page_type)
                    results.append(financial_data)
                    
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
        
        return results
    
    def _extract_financial_data(self, result: ScrapingResult, source: str, page_type: str) -> Dict[str, Any]:
        """Extract and structure financial data"""
        
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
            
            # Financial-specific extractions
            'prices': self._extract_price_data(result.content),
            'indicators': self._extract_indicators(result.content),
            'percentages': self._extract_percentages(result.content),
            'currencies': self._extract_currencies(result.content)
        }
    
    def _extract_commodity_prices(self, result: ScrapingResult) -> Optional[Dict[str, Any]]:
        """Extract commodity price information"""
        
        content = result.content
        prices = {}
        
        # Look for commodity price patterns
        price_patterns = [
            r'Gold.*?(\$[\d,]+\.?\d*)',
            r'Silver.*?(\$[\d,]+\.?\d*)', 
            r'Copper.*?(\$[\d,]+\.?\d*)',
            r'Platinum.*?(\$[\d,]+\.?\d*)',
            r'Palladium.*?(\$[\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                commodity = pattern.split('.*?')[0]
                prices[commodity.lower()] = matches[0]
        
        if not prices:
            return None
        
        return {
            'url': result.url,
            'prices': prices,
            'extracted_at': result.timestamp.isoformat()
        }
    
    def _extract_economic_indicators(self, result: ScrapingResult) -> Optional[Dict[str, Any]]:
        """Extract economic indicator information"""
        
        content = result.content
        indicators = {}
        
        # Look for indicator patterns
        indicator_patterns = [
            r'GDP.*?(\d+\.?\d*%?)',
            r'Inflation.*?(\d+\.?\d*%)',
            r'Employment.*?(\d+\.?\d*%?)',
            r'Mining Production.*?(\d+\.?\d*%?)',
            r'Interest Rate.*?(\d+\.?\d*%)'
        ]
        
        for pattern in indicator_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                indicator = pattern.split('.*?')[0]
                indicators[indicator.lower().replace(' ', '_')] = matches[0]
        
        if not indicators:
            return None
        
        return {
            'url': result.url,
            'indicators': indicators,
            'extracted_at': result.timestamp.isoformat()
        }
    
    def _extract_price_data(self, content: str) -> List[Dict[str, str]]:
        """Extract price information from content"""
        
        # Look for price patterns
        price_patterns = [
            r'\$[\d,]+\.?\d*(?:\s*(?:million|billion|M|B))?',
            r'(?:CAD|USD)\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:CAD|USD)'
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                prices.append({'value': match.strip(), 'pattern': pattern})
        
        return prices[:10]  # Limit to 10 prices
    
    def _extract_indicators(self, content: str) -> List[str]:
        """Extract economic indicators"""
        
        indicators = [
            'GDP', 'inflation', 'unemployment', 'interest rate', 'CPI',
            'mining production', 'commodity exports', 'trade balance'
        ]
        
        found = []
        content_lower = content.lower()
        
        for indicator in indicators:
            if indicator.lower() in content_lower:
                found.append(indicator)
        
        return found
    
    def _extract_percentages(self, content: str) -> List[str]:
        """Extract percentage values"""
        
        percentage_pattern = r'\d+\.?\d*%'
        matches = re.findall(percentage_pattern, content)
        
        return matches[:20]  # Limit to 20 percentages
    
    def _extract_currencies(self, content: str) -> List[str]:
        """Extract currency mentions"""
        
        currencies = ['CAD', 'USD', 'EUR', 'GBP', 'JPY', 'AUD']
        
        found = []
        for currency in currencies:
            if currency in content:
                found.append(currency)
        
        return found
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.unified_scraper.cleanup()

# Convenience functions
async def scrape_financial_data() -> List[Dict[str, Any]]:
    """Convenience function to scrape all financial data"""
    scraper = FinancialDataScraper()
    try:
        return await scraper.scrape_all_financial_data()
    finally:
        await scraper.cleanup()

async def get_commodity_prices() -> Optional[Dict[str, Any]]:
    """Convenience function to get current commodity prices"""
    scraper = FinancialDataScraper()
    try:
        return await scraper.scrape_commodity_prices()
    finally:
        await scraper.cleanup()

async def get_canadian_indicators() -> Optional[Dict[str, Any]]:
    """Convenience function to get Canadian economic indicators"""
    scraper = FinancialDataScraper()
    try:
        return await scraper.scrape_canadian_indicators()
    finally:
        await scraper.cleanup()

# Example usage
if __name__ == "__main__":
    async def main():
        print("💰 Financial Data Scraper")
        print("=" * 40)
        
        # Test commodity prices
        print("\n📊 Getting commodity prices...")
        commodity_data = await get_commodity_prices()
        if commodity_data:
            print(f"Found {len(commodity_data['prices'])} price sources")
        
        # Test Canadian indicators
        print("\n🇨🇦 Getting Canadian indicators...")
        indicator_data = await get_canadian_indicators()
        if indicator_data:
            print(f"Found {len(indicator_data['indicators'])} indicator sources")
        
        # Test all financial data
        print("\n💹 Getting all financial data...")
        all_data = await scrape_financial_data()
        print(f"Scraped {len(all_data)} financial data sources")
        
        for item in all_data:
            print(f"\n💰 {item['source']} - {item['page_type']}")
            print(f"   Content: {item['word_count']:,} words")
            print(f"   Scraper: {item['scraper_used']}")
            print(f"   Prices found: {len(item['prices'])}")
            print(f"   Indicators: {len(item['indicators'])}")
    
    asyncio.run(main())