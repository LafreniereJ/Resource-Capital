#!/usr/bin/env python3
"""
Scraper Factory
Central orchestrator for all web scraping operations
Routes requests to appropriate specialized scrapers
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from .unified_scraper import UnifiedScraper, ScrapingStrategy
from .mining_news_scraper import MiningNewsScraper
from .financial_data_scraper import FinancialDataScraper
from .scraper_intelligence import ScraperIntelligence
from utils.scraper_config import load_scraper_config

class ScraperFactory:
    """Central factory for all scraping operations"""
    
    def __init__(self):
        self.config_manager = load_scraper_config()
        self.intelligence = ScraperIntelligence()
        
        # Initialize specialized scrapers
        self.unified_scraper = UnifiedScraper(self.config_manager, self.intelligence)
        self.news_scraper = MiningNewsScraper()
        self.financial_scraper = FinancialDataScraper()
        
        # Cache for performance
        self._target_cache = {}
    
    async def scrape_all_sources(self) -> Dict[str, Any]:
        """Scrape all configured sources using appropriate specialized scrapers"""
        
        print("🚀 Starting comprehensive scraping of all sources...")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'mining_news': [],
            'financial_data': [],
            'errors': [],
            'summary': {}
        }
        
        try:
            # Scrape mining news
            print("\n📰 Scraping mining news sources...")
            news_results = await self.news_scraper.scrape_all_news()
            results['mining_news'] = news_results
            print(f"✅ Scraped {len(news_results)} news sources")
            
        except Exception as e:
            error_msg = f"Mining news scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        try:
            # Scrape financial data
            print("\n💰 Scraping financial data sources...")
            financial_results = await self.financial_scraper.scrape_all_financial_data()
            results['financial_data'] = financial_results
            print(f"✅ Scraped {len(financial_results)} financial sources")
            
        except Exception as e:
            error_msg = f"Financial data scraping failed: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_summary(results)
        
        return results
    
    async def scrape_specific_targets(self, target_names: List[str]) -> List[Dict[str, Any]]:
        """Scrape specific targets by name"""
        
        if not self.config_manager:
            return []
        
        results = []
        
        for target_name in target_names:
            target = self.config_manager.get_target_by_name(target_name)
            if not target:
                print(f"❌ Target '{target_name}' not found in configuration")
                continue
            
            if not target.enabled:
                print(f"⚠️ Target '{target_name}' is disabled")
                continue
            
            print(f"🎯 Scraping specific target: {target_name}")
            
            try:
                target_results = await self._scrape_target_with_strategy(target)
                results.extend(target_results)
                
            except Exception as e:
                print(f"❌ Error scraping {target_name}: {str(e)}")
                continue
        
        return results
    
    async def scrape_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Scrape all targets in a specific category"""
        
        if category.lower() == 'news' or category.lower() == 'mining_industry_news':
            return await self.news_scraper.scrape_all_news()
        
        elif category.lower() == 'financial' or category.lower() == 'commodity_data':
            return await self.financial_scraper.scrape_all_financial_data()
        
        else:
            # Use unified scraper for other categories
            if not self.config_manager:
                return []
            
            targets = self.config_manager.get_enabled_targets(category=category)
            results = []
            
            for target in targets:
                try:
                    target_results = await self._scrape_target_with_strategy(target)
                    results.extend(target_results)
                except Exception as e:
                    print(f"❌ Error scraping {target.name}: {str(e)}")
                    continue
            
            return results
    
    async def scrape_single_url(self, url: str, target_name: str = None) -> Optional[Dict[str, Any]]:
        """Scrape a single URL with intelligent strategy selection"""
        
        target_config = None
        if target_name and self.config_manager:
            target = self.config_manager.get_target_by_name(target_name)
            if target:
                target_config = target.__dict__
        
        strategy = ScrapingStrategy()
        
        # Use intelligence to determine optimal scraper order
        if self.intelligence:
            optimal_order = self.intelligence.get_optimal_scraper_order(url)
            if optimal_order:
                strategy.primary = optimal_order[0]
                strategy.fallbacks = optimal_order[1:]
        
        try:
            result = await self.unified_scraper.scrape(
                url=url,
                target_config=target_config,
                strategy=strategy
            )
            
            if result.success:
                return {
                    'url': result.url,
                    'title': result.title,
                    'content': result.content,
                    'word_count': result.word_count,
                    'scraper_used': result.scraper_used,
                    'response_time': result.response_time,
                    'scraped_at': result.timestamp.isoformat(),
                    'metadata': result.metadata
                }
            else:
                return {
                    'url': url,
                    'success': False,
                    'error': result.error_message
                }
                
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    async def get_scraper_intelligence_report(self) -> Dict[str, Any]:
        """Get intelligence report from the learning system"""
        
        return self.intelligence.get_intelligence_report()
    
    async def get_optimal_scraper_for_url(self, url: str) -> List[str]:
        """Get optimal scraper order for a specific URL based on learning"""
        
        return self.intelligence.get_optimal_scraper_order(url)
    
    async def _scrape_target_with_strategy(self, target) -> List[Dict[str, Any]]:
        """Scrape a target using its configured strategy"""
        
        results = []
        
        for page_config in target.target_pages:
            url = page_config['url']
            page_type = page_config['type']
            
            # Configure strategy based on target configuration
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
                    results.append({
                        'target_name': target.name,
                        'page_type': page_type,
                        'url': result.url,
                        'title': result.title,
                        'content': result.content,
                        'word_count': result.word_count,
                        'scraper_used': result.scraper_used,
                        'response_time': result.response_time,
                        'scraped_at': result.timestamp.isoformat(),
                        'metadata': result.metadata
                    })
                    
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
            
            # Rate limiting
            await asyncio.sleep(target.rate_limit)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of scraping results"""
        
        summary = {
            'total_sources_scraped': len(results['mining_news']) + len(results['financial_data']),
            'mining_news_sources': len(results['mining_news']),
            'financial_data_sources': len(results['financial_data']),
            'total_errors': len(results['errors']),
            'success_rate': 0.0,
            'scrapers_used': {},
            'total_content_words': 0,
            'avg_response_time': 0.0
        }
        
        # Calculate statistics
        all_results = results['mining_news'] + results['financial_data']
        
        if all_results:
            # Count scrapers used
            for item in all_results:
                scraper = item.get('scraper_used', 'unknown')
                summary['scrapers_used'][scraper] = summary['scrapers_used'].get(scraper, 0) + 1
            
            # Calculate totals
            summary['total_content_words'] = sum(item.get('word_count', 0) for item in all_results)
            
            response_times = [item.get('response_time', 0) for item in all_results if item.get('response_time')]
            if response_times:
                summary['avg_response_time'] = sum(response_times) / len(response_times)
            
            # Calculate success rate
            total_attempted = len(all_results) + len(results['errors'])
            if total_attempted > 0:
                summary['success_rate'] = (len(all_results) / total_attempted) * 100
        
        return summary
    
    async def cleanup(self):
        """Cleanup all resources"""
        await self.unified_scraper.cleanup()
        await self.news_scraper.cleanup()
        await self.financial_scraper.cleanup()

# Convenience functions for easy access
async def scrape_all_mining_sources() -> Dict[str, Any]:
    """Convenience function to scrape all mining-related sources"""
    factory = ScraperFactory()
    try:
        return await factory.scrape_all_sources()
    finally:
        await factory.cleanup()

async def scrape_mining_news() -> List[Dict[str, Any]]:
    """Convenience function to scrape mining news only"""
    factory = ScraperFactory()
    try:
        return await factory.scrape_by_category('news')
    finally:
        await factory.cleanup()

async def scrape_financial_data() -> List[Dict[str, Any]]:
    """Convenience function to scrape financial data only"""
    factory = ScraperFactory()
    try:
        return await factory.scrape_by_category('financial')
    finally:
        await factory.cleanup()

async def get_intelligence_report() -> Dict[str, Any]:
    """Convenience function to get scraper intelligence report"""
    factory = ScraperFactory()
    try:
        return await factory.get_scraper_intelligence_report()
    finally:
        await factory.cleanup()

# Example usage
if __name__ == "__main__":
    async def main():
        print("🏭 Scraper Factory - Central Scraping Orchestrator")
        print("=" * 60)
        
        factory = ScraperFactory()
        
        try:
            # Test comprehensive scraping
            print("\n🚀 Testing comprehensive scraping...")
            all_results = await factory.scrape_all_sources()
            
            print(f"\n📊 SCRAPING SUMMARY:")
            print(f"   Mining News Sources: {all_results['summary']['mining_news_sources']}")
            print(f"   Financial Data Sources: {all_results['summary']['financial_data_sources']}")
            print(f"   Total Content Words: {all_results['summary']['total_content_words']:,}")
            print(f"   Success Rate: {all_results['summary']['success_rate']:.1f}%")
            print(f"   Scrapers Used: {all_results['summary']['scrapers_used']}")
            
            if all_results['errors']:
                print(f"   Errors: {len(all_results['errors'])}")
            
            # Test intelligence report
            print(f"\n🧠 Getting intelligence report...")
            intelligence_report = await factory.get_scraper_intelligence_report()
            
            if intelligence_report['overall']['total_attempts'] > 0:
                print(f"   Learning Data: {intelligence_report['overall']['total_attempts']} attempts recorded")
                print(f"   Overall Success Rate: {intelligence_report['overall']['success_rate']:.1f}%")
                print(f"   Best Performing Scraper: {max(intelligence_report['scrapers'].items(), key=lambda x: x[1]['success_rate'])[0] if intelligence_report['scrapers'] else 'N/A'}")
            
        finally:
            await factory.cleanup()
    
    asyncio.run(main())