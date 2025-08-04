#!/usr/bin/env python3
"""
Economic Data Scraper
Specialized scraper for economic indicators affecting the mining sector

Focuses on:
- Canadian economic indicators (GDP, inflation, employment, interest rates)
- Mining production statistics
- Currency exchange rates
- Federal Reserve economic data
- Bank of Canada policy data
- Statistics Canada mining sector data
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

from ..unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult
from ..scraper_intelligence import ScraperIntelligence


class EconomicDataScraper:
    """Specialized scraper for economic indicators affecting mining"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/economic_indicators")
        self.intelligence = ScraperIntelligence()
        self.unified_scraper = UnifiedScraper(intelligence=self.intelligence)
        
        # Ensure data directories exist
        self._setup_data_directories()
        
        # Economic data sources configuration
        self.economic_sources = {
            "trading_economics_canada": {
                "base_url": "https://tradingeconomics.com",
                "endpoints": {
                    "overview": "/canada/indicators",
                    "gdp": "/canada/gdp",
                    "inflation": "/canada/inflation-cpi",
                    "employment": "/canada/unemployment-rate",
                    "interest_rate": "/canada/interest-rate",
                    "mining_production": "/canada/mining-production",
                    "industrial_production": "/canada/industrial-production",
                    "manufacturing": "/canada/manufacturing-production",
                    "exports": "/canada/exports",
                    "imports": "/canada/imports",
                    "current_account": "/canada/current-account"
                },
                "selectors": {
                    "current_value": [".te-indicator-value", ".indicator-value", ".current-value"],
                    "change": [".te-change", ".indicator-change", ".change-value"],
                    "chart_data": [".chart-container", ".te-chart", "[data-chart]"],
                    "forecast": [".forecast-value", ".te-forecast", ".outlook"]
                }
            },
            "bank_of_canada": {
                "base_url": "https://www.bankofcanada.ca",
                "endpoints": {
                    "key_interest_rate": "/core-functions/monetary-policy/key-interest-rate/",
                    "exchange_rates": "/rates/exchange/",
                    "commodity_price_index": "/rates/price-indexes/cpi/",
                    "monetary_policy": "/core-functions/monetary-policy/"
                },
                "selectors": {
                    "rate": [".rate-value", ".current-rate", ".key-rate"],
                    "date": [".rate-date", ".last-updated", ".date"],
                    "announcement": [".announcement", ".policy-statement"]
                }
            },
            "statistics_canada": {
                "base_url": "https://www.statcan.gc.ca",
                "endpoints": {
                    "mining_overview": "/eng/subjects-start/mining_and_energy",
                    "gdp": "/eng/subjects-start/gross_domestic_product_gdp",
                    "employment": "/eng/subjects-start/labour",
                    "manufacturing": "/eng/subjects-start/manufacturing_and_construction",
                    "international_trade": "/eng/subjects-start/international_trade"
                },
                "selectors": {
                    "statistics": [".stats-item", ".indicator", ".data-point"],
                    "tables": [".data-table", ".stats-table", "table"],
                    "charts": [".chart", ".visualization", ".stats-chart"]
                }
            },
            "fed_economic_data": {
                "base_url": "https://fred.stlouisfed.org",
                "endpoints": {
                    "us_gdp": "/series/GDP",
                    "us_inflation": "/series/CPIAUCSL",
                    "us_unemployment": "/series/UNRATE", 
                    "us_interest_rate": "/series/FEDFUNDS",
                    "us_dollar_index": "/series/DTWEXBGS",
                    "commodity_index": "/series/PPIACO"
                },
                "selectors": {
                    "value": [".series-meta-observation-value", ".pager-data", "#graph-container"],
                    "date": [".series-meta-observation-date", ".observation-date"],
                    "chart": ["#graph-container", ".highcharts-container"]
                }
            },
            "oecd": {
                "base_url": "https://data.oecd.org",
                "endpoints": {
                    "canada_indicators": "/canada",
                    "commodity_markets": "/oecd/agriculture-and-food/commodity-markets",
                    "mining_indicators": "/oecd/industry-and-services/steel-market"
                },
                "selectors": {
                    "indicator_value": [".indicator-value", ".data-value"],
                    "trend": [".trend-indicator", ".direction"],
                    "chart": [".chart-container", ".oecd-chart"]
                }
            }
        }
        
        # Key indicators we track
        self.key_indicators = {
            "canadian_indicators": [
                "gdp_growth", "inflation_rate", "unemployment_rate", "interest_rate",
                "mining_production", "manufacturing_production", "exports", "imports"
            ],
            "us_indicators": [
                "gdp_growth", "inflation_rate", "unemployment_rate", "fed_funds_rate", 
                "dollar_index"
            ],
            "mining_specific": [
                "mining_production_index", "commodity_price_index", "resource_sector_employment",
                "mining_investment", "exploration_spending"
            ]
        }
    
    def _setup_data_directories(self):
        """Create necessary data directories"""
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "historical", 
            self.data_dir / datetime.now().strftime("%Y-%m")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def scrape_all_economic_data(self) -> Dict[str, Any]:
        """Scrape all configured economic data sources"""
        
        print("📊 Starting comprehensive economic data scraping...")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'canadian_indicators': {},
            'us_indicators': {},
            'central_bank_data': {},
            'mining_specific_data': {},
            'international_data': {},
            'errors': [],
            'summary': {}
        }
        
        # Scrape Canadian indicators
        try:
            print("🍁 Scraping Canadian economic indicators...")
            canadian_data = await self._scrape_source_data("trading_economics_canada")
            results['canadian_indicators'] = canadian_data
            
        except Exception as e:
            error_msg = f"Error scraping Canadian indicators: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Scrape Bank of Canada data
        try:
            print("🏦 Scraping Bank of Canada data...")
            boc_data = await self._scrape_source_data("bank_of_canada")
            results['central_bank_data']['bank_of_canada'] = boc_data
            
        except Exception as e:
            error_msg = f"Error scraping Bank of Canada: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Scrape Statistics Canada
        try:
            print("📈 Scraping Statistics Canada...")
            statcan_data = await self._scrape_source_data("statistics_canada")
            results['mining_specific_data']['statistics_canada'] = statcan_data
            
        except Exception as e:
            error_msg = f"Error scraping Statistics Canada: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Scrape US Federal Reserve data
        try:
            print("🇺🇸 Scraping US Federal Reserve economic data...")
            fed_data = await self._scrape_source_data("fed_economic_data")
            results['us_indicators'] = fed_data
            
        except Exception as e:
            error_msg = f"Error scraping Federal Reserve data: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Scrape OECD data
        try:
            print("🌍 Scraping OECD international data...")
            oecd_data = await self._scrape_source_data("oecd")
            results['international_data']['oecd'] = oecd_data
            
        except Exception as e:
            error_msg = f"Error scraping OECD data: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_economic_summary(results)
        
        # Save results
        await self._save_economic_data(results)
        
        return results
    
    async def _scrape_source_data(self, source_name: str) -> Dict[str, Any]:
        """Scrape data from a specific economic source"""
        
        source_config = self.economic_sources[source_name]
        source_data = {
            'source': source_name,
            'scraped_at': datetime.now().isoformat(),
            'indicators': {},
            'raw_data': {}
        }
        
        # Scrape each endpoint for this source
        for endpoint_name, endpoint_path in source_config['endpoints'].items():
            try:
                url = source_config['base_url'] + endpoint_path
                
                print(f"  📊 Scraping {endpoint_name} from {source_name}...")
                
                # Configure scraping strategy based on source
                strategy = ScrapingStrategy()
                if source_name in ['trading_economics_canada', 'fed_economic_data']:
                    strategy.primary = 'playwright'  # These are JS-heavy
                    strategy.fallbacks = ['crawl4ai', 'requests']
                else:
                    strategy.primary = 'crawl4ai'
                    strategy.fallbacks = ['playwright', 'requests']
                
                # Scrape the endpoint
                result = await self.unified_scraper.scrape(
                    url=url,
                    strategy=strategy
                )
                
                if result.success:
                    # Extract economic indicators from content
                    extracted_data = self._extract_economic_indicators(
                        result.content,
                        source_config['selectors'],
                        source_name,
                        endpoint_name
                    )
                    
                    source_data['indicators'][endpoint_name] = {
                        'url': url,
                        'scraped_at': result.timestamp.isoformat(),
                        'scraper_used': result.scraper_used,
                        'response_time': result.response_time,
                        'data': extracted_data
                    }
                    
                    # Store raw content for later analysis
                    source_data['raw_data'][endpoint_name] = {
                        'content_length': len(result.content),
                        'word_count': result.word_count,
                        'title': result.title
                    }
                
                # Rate limiting
                await asyncio.sleep(3)  # More conservative for government sites
                
            except Exception as e:
                print(f"    ❌ Failed to scrape {endpoint_name}: {str(e)}")
                continue
        
        return source_data
    
    def _extract_economic_indicators(self, content: str, selectors: Dict, source: str, endpoint: str) -> Dict[str, Any]:
        """Extract economic indicators from scraped content"""
        
        extracted = {
            'indicators': {},
            'timestamp': datetime.now().isoformat(),
            'extraction_method': 'regex_patterns'
        }
        
        # Define indicator extraction patterns
        indicator_patterns = {
            'gdp': [
                r'GDP.*?([+-]?\d+\.\d+)%',
                r'Gross Domestic Product.*?(\d+\.\d+)',
                r'(\d+\.\d+)%?\s*GDP'
            ],
            'inflation': [
                r'inflation.*?([+-]?\d+\.\d+)%',
                r'CPI.*?([+-]?\d+\.\d+)%',
                r'Consumer Price Index.*?(\d+\.\d+)'
            ],
            'unemployment': [
                r'unemployment.*?(\d+\.\d+)%',
                r'jobless.*?(\d+\.\d+)%',
                r'(\d+\.\d+)%\s*unemployment'
            ],
            'interest_rate': [
                r'interest rate.*?(\d+\.\d+)%',
                r'policy rate.*?(\d+\.\d+)%',
                r'overnight rate.*?(\d+\.\d+)%',
                r'(\d+\.\d+)%\s*(?:interest|rate)'
            ],
            'mining_production': [
                r'mining production.*?([+-]?\d+\.\d+)%?',
                r'mineral production.*?([+-]?\d+\.\d+)',
                r'(\d+\.\d+).*?mining.*?production'
            ]
        }
        
        # Extract indicators based on endpoint type
        for indicator_type, patterns in indicator_patterns.items():
            if indicator_type in endpoint.lower() or any(term in content.lower() for term in [indicator_type.replace('_', ' ')]):
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        try:
                            # Take the first valid numeric match
                            value = float(matches[0].replace('+', '').replace('%', ''))
                            extracted['indicators'][indicator_type] = {
                                'value': value,
                                'unit': '%' if 'rate' in indicator_type or 'inflation' in indicator_type else 'index',
                                'extracted_from': endpoint,
                                'pattern_used': pattern
                            }
                            break
                        except (ValueError, IndexError):
                            continue
        
        # Extract general numeric data points
        numeric_patterns = [
            r'(\d+\.\d+)%',  # Percentages
            r'\$(\d+(?:,\d{3})*(?:\.\d+)?)',  # Dollar amounts
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:billion|million|thousand)',  # Large numbers
        ]
        
        numeric_data = []
        for pattern in numeric_patterns:
            matches = re.findall(pattern, content)
            numeric_data.extend(matches)
        
        if numeric_data:
            extracted['numeric_data_found'] = len(numeric_data)
            extracted['sample_values'] = numeric_data[:10]  # Store first 10 values
        
        # Extract dates for data currency
        date_patterns = [
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # January 15, 2024
            r'(\d{1,2}/\d{1,2}/\d{4})',    # 01/15/2024
            r'(\d{4}-\d{2}-\d{2})',        # 2024-01-15
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                extracted['data_date'] = match.group(1)
                break
        
        return extracted
    
    def _generate_economic_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for scraped economic data"""
        
        summary = {
            'total_sources_scraped': 0,
            'total_indicators_found': 0,
            'canadian_indicators_count': 0,
            'us_indicators_count': 0,
            'mining_specific_count': 0,
            'successful_extractions': 0,
            'failed_extractions': len(results['errors']),
            'scraping_duration': None
        }
        
        # Count sources and indicators
        data_sections = ['canadian_indicators', 'us_indicators', 'central_bank_data', 
                        'mining_specific_data', 'international_data']
        
        for section in data_sections:
            section_data = results.get(section, {})
            if isinstance(section_data, dict):
                if 'indicators' in section_data:
                    # Direct indicators structure
                    summary['total_sources_scraped'] += 1
                    indicators = section_data.get('indicators', {})
                    for indicator_data in indicators.values():
                        if indicator_data.get('data', {}).get('indicators'):
                            summary['total_indicators_found'] += len(indicator_data['data']['indicators'])
                            summary['successful_extractions'] += 1
                else:
                    # Nested structure (like central_bank_data)
                    for source_name, source_data in section_data.items():
                        if isinstance(source_data, dict) and 'indicators' in source_data:
                            summary['total_sources_scraped'] += 1
                            indicators = source_data.get('indicators', {})
                            for indicator_data in indicators.values():
                                if indicator_data.get('data', {}).get('indicators'):
                                    summary['total_indicators_found'] += len(indicator_data['data']['indicators'])
                                    summary['successful_extractions'] += 1
        
        # Calculate specific counts
        if results.get('canadian_indicators', {}).get('indicators'):
            summary['canadian_indicators_count'] = len(results['canadian_indicators']['indicators'])
        
        if results.get('us_indicators', {}).get('indicators'):
            summary['us_indicators_count'] = len(results['us_indicators']['indicators'])
        
        mining_data = results.get('mining_specific_data', {})
        if mining_data:
            summary['mining_specific_count'] = len(mining_data)
        
        # Calculate scraping duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_duration'] = (end - start).total_seconds()
        
        return summary
    
    async def _save_economic_data(self, results: Dict[str, Any]):
        """Save scraped economic data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        raw_file = self.data_dir / "raw" / f"economic_indicators_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save monthly data
        monthly_dir = self.data_dir / datetime.now().strftime("%Y-%m")
        monthly_file = monthly_dir / f"economic_{timestamp}.json"
        with open(monthly_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Economic data saved to:")
        print(f"   Raw: {raw_file}")
        print(f"   Monthly: {monthly_file}")
    
    async def get_indicator_trend(self, indicator: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get historical trend for a specific economic indicator"""
        
        trend_data = []
        
        # Look through historical files
        for days_back in range(days):
            date = datetime.now() - timedelta(days=days_back)
            date_str = date.strftime("%Y-%m")
            monthly_dir = self.data_dir / date_str
            
            if monthly_dir.exists():
                for file_path in monthly_dir.glob("economic_*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Search for the indicator across all sections
                        for section_name, section_data in data.items():
                            if section_name in ['canadian_indicators', 'us_indicators', 'central_bank_data', 'mining_specific_data']:
                                if self._find_indicator_in_section(section_data, indicator, trend_data, data.get('scraping_started')):
                                    break
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(trend_data, key=lambda x: x['date'])
    
    def _find_indicator_in_section(self, section_data: Dict, indicator: str, trend_data: List, timestamp: str) -> bool:
        """Helper to find indicator value in a data section"""
        
        if isinstance(section_data, dict):
            # Check direct indicators
            if 'indicators' in section_data:
                for endpoint_data in section_data['indicators'].values():
                    indicators = endpoint_data.get('data', {}).get('indicators', {})
                    if indicator in indicators:
                        trend_data.append({
                            'date': timestamp,
                            'value': indicators[indicator]['value'],
                            'unit': indicators[indicator].get('unit', ''),
                            'source': endpoint_data.get('url', 'unknown')
                        })
                        return True
            
            # Check nested structure
            for source_data in section_data.values():
                if isinstance(source_data, dict) and 'indicators' in source_data:
                    for endpoint_data in source_data['indicators'].values():
                        indicators = endpoint_data.get('data', {}).get('indicators', {})
                        if indicator in indicators:
                            trend_data.append({
                                'date': timestamp,
                                'value': indicators[indicator]['value'],
                                'unit': indicators[indicator].get('unit', ''),
                                'source': endpoint_data.get('url', 'unknown')
                            })
                            return True
        
        return False
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        await self.unified_scraper.cleanup()


# Convenience functions
async def scrape_all_economic_indicators() -> Dict[str, Any]:
    """Convenience function to scrape all economic indicators"""
    scraper = EconomicDataScraper()
    try:
        return await scraper.scrape_all_economic_data()
    finally:
        await scraper.cleanup()


async def get_economic_indicator_trend(indicator: str, days: int = 90) -> List[Dict[str, Any]]:
    """Convenience function to get trend for specific indicator"""
    scraper = EconomicDataScraper()
    try:
        return await scraper.get_indicator_trend(indicator, days)
    finally:
        await scraper.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        print("📊 Economic Data Scraper - Mining Sector Intelligence")
        print("=" * 60)
        
        scraper = EconomicDataScraper()
        
        try:
            # Test comprehensive economic data scraping
            print("\n🚀 Testing comprehensive economic data scraping...")
            results = await scraper.scrape_all_economic_data()
            
            print(f"\n📊 ECONOMIC DATA SUMMARY:")
            print(f"   Total Sources: {results['summary']['total_sources_scraped']}")
            print(f"   Total Indicators: {results['summary']['total_indicators_found']}")
            print(f"   Canadian Indicators: {results['summary']['canadian_indicators_count']}")
            print(f"   US Indicators: {results['summary']['us_indicators_count']}")
            print(f"   Mining Specific: {results['summary']['mining_specific_count']}")
            print(f"   Successful Extractions: {results['summary']['successful_extractions']}")
            print(f"   Scraping Duration: {results['summary']['scraping_duration']:.1f}s")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
            
            # Show sample indicators
            if results.get('canadian_indicators', {}).get('indicators'):
                print(f"\n🍁 CANADIAN INDICATORS SAMPLE:")
                for endpoint, data in list(results['canadian_indicators']['indicators'].items())[:3]:
                    indicators = data.get('data', {}).get('indicators', {})
                    if indicators:
                        for indicator, value_data in indicators.items():
                            print(f"   {indicator.replace('_', ' ').title()}: {value_data['value']}{value_data.get('unit', '')}")
            
        finally:
            await scraper.cleanup()
    
    asyncio.run(main())