#!/usr/bin/env python3
"""
Metal Prices Scraper
Specialized scraper for real-time and historical commodity/metal prices

Focuses on:
- Precious metals (gold, silver, platinum, palladium)
- Base metals (copper, aluminum, zinc, nickel, lead)
- Energy commodities (oil, natural gas)
- Agricultural commodities affecting mining regions
- Currency data affecting commodity prices
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


class MetalPricesScraper:
    """Specialized scraper for metal and commodity prices"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/metal_prices")
        self.intelligence = ScraperIntelligence()
        self.unified_scraper = UnifiedScraper(intelligence=self.intelligence)
        
        # Ensure data directories exist
        self._setup_data_directories()
        
        # Metal price sources configuration - UPDATED FOR AUGUST 4, 2025 TARGET SITES
        self.price_sources = {
            "trading_economics": {
                "base_url": "https://tradingeconomics.com",
                "endpoints": {
                    "commodities_overview": "/commodities",
                    "gold": "/commodity/gold",
                    "silver": "/commodity/silver", 
                    "copper": "/commodity/copper",
                    "platinum": "/commodity/platinum",
                    "palladium": "/commodity/palladium",
                    "aluminum": "/commodity/aluminum",
                    "zinc": "/commodity/zinc",
                    "nickel": "/commodity/nickel",
                    "lithium": "/commodity/lithium",
                    "uranium": "/commodity/uranium",
                    "cobalt": "/commodity/cobalt"
                },
                "selectors": {
                    "price": [".price-current", ".te-price", "[data-symbol] .price", "table.table-hover td:nth-child(2)", ".commodities-table .price"],
                    "change": [".change-percent", ".te-change", ".price-change", "table.table-hover td:nth-child(3)", ".commodities-table .change"],
                    "chart_data": [".chart-container", ".price-chart", ".highcharts-container"],
                    "forecast": [".forecast-data", ".outlook-section", ".forecast-table"],
                    "commodity_table": ["table.table-hover", ".commodities-table", "#commodities-table"]
                }
            },
            "daily_metal_price": {
                "base_url": "https://www.dailymetalprice.com",
                "endpoints": {
                    "overview": "/",
                    "gold": "/gold-price/",
                    "silver": "/silver-price/",
                    "copper": "/copper-price/",
                    "platinum": "/platinum-price/",
                    "palladium": "/palladium-price/",
                    "nickel": "/nickel-price/",
                    "zinc": "/zinc-price/",
                    "lithium": "/lithium-price/"
                },
                "selectors": {
                    "price": [".price-value", ".current-price", ".metal-price", "table.price-table td:nth-child(2)", ".price-display"],
                    "change": [".price-change", ".change-percent", "table.price-table td:nth-child(3)", ".change-value"],
                    "date": [".price-date", ".last-updated"],
                    "price_table": ["table.price-table", ".prices-table", "#metal-prices-table"],
                    "market_data": [".market-info", ".trading-info"]
                }
            },
            "kitco_precious": {
                "base_url": "https://www.kitco.com",
                "endpoints": {
                    "precious_metals_overview": "/price/precious-metals",
                    "gold": "/gold-price-today-usa/",
                    "silver": "/silver-price-today-usa/",
                    "platinum": "/platinum-price-today-usa/",
                    "palladium": "/palladium-price-today-usa/"
                },
                "selectors": {
                    "price": [".price", ".current-price", "#sp-price", ".price-box .price-value", "table.price-table td.price"],
                    "change": [".change", ".price-change", ".change-percent", "table.price-table td.change"],
                    "charts": [".price-chart", ".chart-container", ".highcharts-container"],
                    "bid_ask": [".bid-ask", ".spread-info"],
                    "market_commentary": [".market-commentary", ".price-analysis"]
                }
            },
            "kitco_base": {
                "base_url": "https://www.kitco.com",
                "endpoints": {
                    "base_metals_overview": "/price/base-metals",
                    "copper": "/copper-price/",
                    "nickel": "/nickel-price/",
                    "zinc": "/zinc-price/",
                    "aluminum": "/aluminum-price/"
                },
                "selectors": {
                    "price": [".price", ".current-price", ".metal-price", "table.metals-table td.price", ".price-display"],
                    "change": [".change", ".price-change", ".change-percent", "table.metals-table td.change"],
                    "volume": [".volume-data", ".trading-volume"],
                    "market_data": [".market-info", ".base-metals-info"],
                    "futures": [".futures-data", ".forward-prices"]
                }
            }
        }
        
        # Key mining commodities to focus on
        self.target_commodities = {
            "precious_metals": ["gold", "silver", "platinum", "palladium"],
            "base_metals": ["copper", "nickel", "zinc", "aluminum"],
            "critical_metals": ["lithium", "uranium", "cobalt"]
        }
        
        # Currency data for commodity analysis
        self.currency_sources = {
            "usd_cad": "https://finance.yahoo.com/quote/USDCAD=X",
            "dxy": "https://finance.yahoo.com/quote/DX-Y.NYB"  # Dollar Index
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
    
    async def scrape_target_metal_sites(self) -> Dict[str, Any]:
        """Scrape the 4 specific target sites for August 4, 2025 mining intelligence"""
        
        print("💰 Starting targeted metal prices scraping for mining intelligence...")
        print("🎯 Target Sites: Trading Economics, Daily Metal Price, Kitco Precious, Kitco Base")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'target_date': '2025-08-04',
            'sites_scraped': {},
            'commodity_data': {
                'precious_metals': {},
                'base_metals': {},
                'critical_metals': {}
            },
            'market_analysis': {},
            'performance_log': [],
            'errors': [],
            'summary': {}
        }
        
        # Define the 4 target sites and their scraping strategies
        target_sites = [
            {
                'name': 'trading_economics',
                'display_name': 'Trading Economics Commodities',
                'url': 'https://tradingeconomics.com/commodities',
                'priority_commodities': ['gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lithium', 'uranium', 'cobalt']
            },
            {
                'name': 'daily_metal_price',
                'display_name': 'Daily Metal Price',
                'url': 'https://www.dailymetalprice.com/',
                'priority_commodities': ['gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lithium']
            },
            {
                'name': 'kitco_precious',
                'display_name': 'Kitco Precious Metals',
                'url': 'https://www.kitco.com/price/precious-metals',
                'priority_commodities': ['gold', 'silver', 'platinum', 'palladium']
            },
            {
                'name': 'kitco_base',
                'display_name': 'Kitco Base Metals',
                'url': 'https://www.kitco.com/price/base-metals',
                'priority_commodities': ['copper', 'nickel', 'zinc', 'aluminum']
            }
        ]
        
        # Scrape each target site
        for site_config in target_sites:
            site_start_time = datetime.now()
            print(f"\n🌐 Scraping {site_config['display_name']}...")
            
            try:
                site_data = await self._scrape_target_site(site_config)
                results['sites_scraped'][site_config['name']] = site_data
                
                # Extract commodity data from site
                for commodity in site_config['priority_commodities']:
                    if commodity in site_data.get('commodities', {}):
                        commodity_info = site_data['commodities'][commodity]
                        
                        # Categorize the commodity
                        if commodity in self.target_commodities['precious_metals']:
                            if commodity not in results['commodity_data']['precious_metals']:
                                results['commodity_data']['precious_metals'][commodity] = {}
                            results['commodity_data']['precious_metals'][commodity][site_config['name']] = commodity_info
                        elif commodity in self.target_commodities['base_metals']:
                            if commodity not in results['commodity_data']['base_metals']:
                                results['commodity_data']['base_metals'][commodity] = {}
                            results['commodity_data']['base_metals'][commodity][site_config['name']] = commodity_info
                        elif commodity in self.target_commodities['critical_metals']:
                            if commodity not in results['commodity_data']['critical_metals']:
                                results['commodity_data']['critical_metals'][commodity] = {}
                            results['commodity_data']['critical_metals'][commodity][site_config['name']] = commodity_info
                
                # Log performance
                site_duration = (datetime.now() - site_start_time).total_seconds()
                performance_entry = {
                    'site': site_config['name'],
                    'display_name': site_config['display_name'],
                    'url': site_config['url'],
                    'success': True,
                    'response_time': site_duration,
                    'commodities_found': len(site_data.get('commodities', {})),
                    'scraper_used': site_data.get('scraper_used', 'unknown'),
                    'content_quality': site_data.get('content_quality', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
                results['performance_log'].append(performance_entry)
                
                print(f"✅ {site_config['display_name']}: {len(site_data.get('commodities', {}))} commodities in {site_duration:.1f}s")
                
            except Exception as e:
                error_msg = f"Failed to scrape {site_config['display_name']}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                
                # Log failed performance
                site_duration = (datetime.now() - site_start_time).total_seconds()
                performance_entry = {
                    'site': site_config['name'],
                    'display_name': site_config['display_name'],
                    'url': site_config['url'],
                    'success': False,
                    'response_time': site_duration,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['performance_log'].append(performance_entry)
            
            # Rate limiting between sites
            await asyncio.sleep(3)
        
        # Generate consolidated market analysis
        results['market_analysis'] = self._generate_market_analysis(results)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_target_summary(results)
        
        # Save results to the specific path requested
        await self._save_target_results(results)
        
        return results

    async def scrape_all_metal_prices(self) -> Dict[str, Any]:
        """Scrape all configured metal price sources (legacy method)"""
        
        print("💰 Starting comprehensive metal prices scraping...")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'precious_metals': {},
            'base_metals': {},
            'energy_commodities': {},
            'currency_data': {},
            'errors': [],
            'summary': {}
        }
        
        # Scrape precious metals
        precious_metals = ['gold', 'silver', 'platinum', 'palladium']
        for metal in precious_metals:
            try:
                print(f"🥇 Scraping {metal} prices...")
                metal_data = await self._scrape_metal_data(metal)
                results['precious_metals'][metal] = metal_data
                
            except Exception as e:
                error_msg = f"Error scraping {metal}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Scrape base metals
        base_metals = ['copper', 'aluminum', 'zinc', 'nickel']
        for metal in base_metals:
            try:
                print(f"🔨 Scraping {metal} prices...")
                metal_data = await self._scrape_metal_data(metal)
                results['base_metals'][metal] = metal_data
                
            except Exception as e:
                error_msg = f"Error scraping {metal}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Scrape critical metals
        critical_metals = ['lithium', 'uranium', 'cobalt']
        for metal in critical_metals:
            try:
                print(f"⚡ Scraping {metal} prices...")
                metal_data = await self._scrape_metal_data(metal)
                results['base_metals'][metal] = metal_data
                
            except Exception as e:
                error_msg = f"Error scraping {metal}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_price_summary(results)
        
        # Save results
        await self._save_price_data(results)
        
        return results
    
    async def _scrape_metal_data(self, metal: str) -> Dict[str, Any]:
        """Scrape data for a specific metal from multiple sources"""
        
        metal_data = {
            'metal': metal,
            'scraped_at': datetime.now().isoformat(),
            'sources': {},
            'consolidated_price': None,
            'price_consensus': None
        }
        
        prices_found = []
        
        # Try each source for this metal
        for source_name, source_config in self.price_sources.items():
            if metal in source_config['endpoints']:
                try:
                    url = source_config['base_url'] + source_config['endpoints'][metal]
                    
                    print(f"  📊 Scraping {metal} from {source_name}...")
                    
                    # Configure scraping strategy
                    strategy = ScrapingStrategy()
                    if source_name in ['yahoo_finance', 'lme']:
                        strategy.primary = 'playwright'  # These sites are JS-heavy
                        strategy.fallbacks = ['crawl4ai', 'requests']
                    else:
                        strategy.primary = 'crawl4ai'
                        strategy.fallbacks = ['playwright', 'requests']
                    
                    # Scrape the source
                    result = await self.unified_scraper.scrape(
                        url=url,
                        strategy=strategy
                    )
                    
                    if result.success:
                        # Extract price data from content
                        extracted_data = self._extract_price_data(
                            result.content, 
                            source_config['selectors'],
                            source_name,
                            metal
                        )
                        
                        metal_data['sources'][source_name] = {
                            'url': url,
                            'scraped_at': result.timestamp.isoformat(),
                            'scraper_used': result.scraper_used,
                            'response_time': result.response_time,
                            'data': extracted_data
                        }
                        
                        # Collect prices for consensus
                        if extracted_data.get('price'):
                            try:
                                price_value = float(re.sub(r'[^\d.-]', '', str(extracted_data['price'])))
                                prices_found.append(price_value)
                            except (ValueError, TypeError):
                                pass
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"    ❌ Failed to scrape {metal} from {source_name}: {str(e)}")
                    continue
        
        # Calculate consensus price if multiple sources found
        if prices_found:
            metal_data['consolidated_price'] = {
                'average': sum(prices_found) / len(prices_found),
                'median': sorted(prices_found)[len(prices_found)//2],
                'min': min(prices_found),
                'max': max(prices_found),
                'sources_count': len(prices_found),
                'price_spread': max(prices_found) - min(prices_found) if len(prices_found) > 1 else 0
            }
        
        return metal_data
    
    async def _scrape_target_site(self, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a specific target site for comprehensive commodity data"""
        
        site_data = {
            'site_name': site_config['name'],
            'display_name': site_config['display_name'],
            'url': site_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'commodities': {},
            'market_commentary': [],
            'price_trends': {},
            'content_quality': 'unknown',
            'scraper_used': 'unknown'
        }
        
        try:
            # Configure scraping strategy based on site requirements
            strategy = ScrapingStrategy()
            
            if site_config['name'] in ['kitco_precious', 'kitco_base']:
                # Kitco sites are JavaScript-heavy with dynamic content
                strategy.primary = 'playwright'
                strategy.fallbacks = ['requests']
                strategy.wait_for = '.price, .current-price, table'
                strategy.timeout = 30
            elif site_config['name'] == 'trading_economics':
                # Trading Economics has anti-bot measures
                strategy.primary = 'playwright'
                strategy.fallbacks = ['requests']
                strategy.wait_for = 'table.table-hover, .commodities-table'
                strategy.timeout = 25
            else:
                # Daily Metal Price is simpler
                strategy.primary = 'requests'
                strategy.fallbacks = ['playwright']
                strategy.timeout = 20
            
            print(f"  📡 Using {strategy.primary} scraper for {site_config['display_name']}")
            
            # Scrape the main site
            result = await self.unified_scraper.scrape(
                url=site_config['url'],
                strategy=strategy
            )
            
            if result.success:
                site_data['scraper_used'] = result.scraper_used
                site_data['content_quality'] = 'good' if len(result.content) > 5000 else 'limited'
                
                # Extract commodity data using enhanced patterns
                extracted_commodities = self._extract_site_commodities(
                    result.content, 
                    site_config,
                    self.price_sources[site_config['name']]['selectors']
                )
                
                site_data['commodities'] = extracted_commodities
                
                # Extract market commentary if available
                commentary = self._extract_market_commentary(result.content, site_config['name'])
                site_data['market_commentary'] = commentary
                
                # Extract trend indicators
                trends = self._extract_price_trends(result.content, site_config['name'])
                site_data['price_trends'] = trends
                
                print(f"  ✅ Extracted {len(extracted_commodities)} commodities from {site_config['display_name']}")
                
            else:
                print(f"  ❌ Failed to scrape {site_config['display_name']}: {result.error}")
                site_data['error'] = result.error
                
        except Exception as e:
            print(f"  💥 Exception scraping {site_config['display_name']}: {str(e)}")
            site_data['error'] = str(e)
        
        return site_data
    
    def _extract_site_commodities(self, content: str, site_config: Dict, selectors: Dict) -> Dict[str, Any]:
        """Extract commodity data from site content using advanced patterns"""
        
        commodities = {}
        
        # Enhanced extraction patterns for different site types
        if site_config['name'] == 'trading_economics':
            commodities = self._extract_trading_economics_data(content)
        elif site_config['name'] == 'daily_metal_price':
            commodities = self._extract_daily_metal_price_data(content)
        elif site_config['name'] in ['kitco_precious', 'kitco_base']:
            commodities = self._extract_kitco_data(content, site_config['name'])
        
        return commodities
    
    def _extract_trading_economics_data(self, content: str) -> Dict[str, Any]:
        """Extract commodity data from Trading Economics"""
        
        commodities = {}
        
        # Trading Economics table extraction patterns
        table_patterns = [
            # Table rows with commodity data
            r'<tr[^>]*>.*?<td[^>]*>.*?(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt).*?</td>.*?<td[^>]*>.*?([\d,]+\.?\d*).*?</td>.*?<td[^>]*>.*?([+-]?[\d.]+%?).*?</td>',
            # Alternative patterns for different table layouts
            r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt)[^<]*<[^>]*>.*?([\d,]+\.?\d*)[^<]*<[^>]*>.*?([+-]?[\d.]+%?)'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) >= 3:
                    metal_name = match[0].lower()
                    try:
                        price = float(match[1].replace(',', ''))
                        change = match[2].strip()
                        
                        commodities[metal_name] = {
                            'price': price,
                            'change': change,
                            'unit': 'USD/oz' if metal_name in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/ton',
                            'source': 'trading_economics',
                            'timestamp': datetime.now().isoformat()
                        }
                    except (ValueError, IndexError):
                        continue
        
        return commodities
    
    def _extract_daily_metal_price_data(self, content: str) -> Dict[str, Any]:
        """Extract commodity data from Daily Metal Price"""
        
        commodities = {}
        
        # Daily Metal Price extraction patterns
        price_patterns = [
            # Price table patterns
            r'<tr[^>]*>.*?<td[^>]*>.*?(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium).*?</td>.*?<td[^>]*>.*?\$?([\d,]+\.?\d*).*?</td>.*?<td[^>]*>.*?([+-]?[\d.]+%?).*?</td>',
            # Price display patterns
            r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium)\s+Price.*?\$?([\d,]+\.?\d*).*?([+-]?[\d.]+%?)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) >= 3:
                    metal_name = match[0].lower()
                    try:
                        price = float(match[1].replace(',', ''))
                        change = match[2].strip()
                        
                        commodities[metal_name] = {
                            'price': price,
                            'change': change,
                            'unit': 'USD/oz' if metal_name in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/lb',
                            'source': 'daily_metal_price',
                            'timestamp': datetime.now().isoformat()
                        }
                    except (ValueError, IndexError):
                        continue
        
        return commodities
    
    def _extract_kitco_data(self, content: str, site_type: str) -> Dict[str, Any]:
        """Extract commodity data from Kitco sites"""
        
        commodities = {}
        
        # Kitco extraction patterns
        if site_type == 'kitco_precious':
            metals = ['gold', 'silver', 'platinum', 'palladium']
        else:
            metals = ['copper', 'nickel', 'zinc', 'aluminum']
        
        for metal in metals:
            # Kitco price patterns
            metal_patterns = [
                rf'{metal.title()}.*?(\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%?)',
                rf'<td[^>]*>{metal.title()}</td>.*?<td[^>]*>(\$?[\d,]+\.?\d*)</td>.*?<td[^>]*>([+-]?[\d.]+%?)</td>',
                rf'id="sp-{metal}-price"[^>]*>(\$?[\d,]+\.?\d*)<.*?change[^>]*>([+-]?[\d.]+%?)'
            ]
            
            for pattern in metal_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        price = float(match.group(1).replace('$', '').replace(',', ''))
                        change = match.group(2).strip()
                        
                        commodities[metal] = {
                            'price': price,
                            'change': change,
                            'unit': 'USD/oz' if metal in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/lb',
                            'source': site_type,
                            'timestamp': datetime.now().isoformat()
                        }
                        break
                    except (ValueError, IndexError):
                        continue
        
        return commodities
    
    def _extract_market_commentary(self, content: str, site_name: str) -> List[str]:
        """Extract market commentary and analysis from site content"""
        
        commentary = []
        
        # Commentary extraction patterns by site
        if site_name == 'trading_economics':
            patterns = [
                r'<div[^>]*forecast[^>]*>.*?<p[^>]*>(.*?)</p>',
                r'<div[^>]*analysis[^>]*>.*?<p[^>]*>(.*?)</p>',
                r'outlook.*?<p[^>]*>(.*?)</p>'
            ]
        elif site_name == 'kitco_precious' or site_name == 'kitco_base':
            patterns = [
                r'<div[^>]*commentary[^>]*>.*?<p[^>]*>(.*?)</p>',
                r'<div[^>]*analysis[^>]*>.*?<p[^>]*>(.*?)</p>',
                r'market.*?update.*?<p[^>]*>(.*?)</p>'
            ]
        else:
            patterns = [
                r'<div[^>]*market[^>]*>.*?<p[^>]*>(.*?)</p>',
                r'<div[^>]*news[^>]*>.*?<p[^>]*>(.*?)</p>'
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_text) > 50 and len(clean_text) < 500:
                    commentary.append(clean_text)
        
        return commentary[:3]  # Limit to top 3 commentary pieces
    
    def _extract_price_trends(self, content: str, site_name: str) -> Dict[str, Any]:
        """Extract price trend indicators from content"""
        
        trends = {
            'daily_trends': [],
            'weekly_trends': [],
            'monthly_trends': [],
            'volatility_indicators': []
        }
        
        # Trend extraction patterns
        trend_patterns = [
            r'(up|down|higher|lower|rising|falling|bullish|bearish)\s+([\d.]+%?)',
            r'(gained|lost|increased|decreased)\s+([\d.]+%?)',
            r'([\d.]+%?)\s+(gain|loss|increase|decrease)'
        ]
        
        for pattern in trend_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    direction = match[0].lower()
                    magnitude = match[1] if '%' in match[1] else match[0] if '%' in match[0] else None
                    
                    if magnitude and any(word in direction for word in ['up', 'higher', 'rising', 'bullish', 'gained', 'increased']):
                        trends['daily_trends'].append(f"Positive movement: {magnitude}")
                    elif magnitude and any(word in direction for word in ['down', 'lower', 'falling', 'bearish', 'lost', 'decreased']):
                        trends['daily_trends'].append(f"Negative movement: {magnitude}")
        
        return trends
    
    def _generate_market_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive market analysis from scraped data"""
        
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'price_consensus': {},
            'significant_movements': [],
            'market_sentiment': 'neutral',
            'supply_demand_insights': [],
            'investment_implications': []
        }
        
        # Calculate price consensus for each commodity
        all_commodities = {}
        
        # Collect all commodity data
        for category in ['precious_metals', 'base_metals', 'critical_metals']:
            for commodity, sources in results['commodity_data'][category].items():
                all_commodities[commodity] = sources
        
        # Generate consensus prices
        for commodity, sources in all_commodities.items():
            prices = []
            changes = []
            
            for source_data in sources.values():
                if 'price' in source_data and source_data['price']:
                    prices.append(source_data['price'])
                if 'change' in source_data and source_data['change']:
                    # Extract numeric change
                    change_match = re.search(r'([+-]?[\d.]+)', str(source_data['change']))
                    if change_match:
                        changes.append(float(change_match.group(1)))
            
            if prices:
                analysis['price_consensus'][commodity] = {
                    'average_price': sum(prices) / len(prices),
                    'price_range': f"${min(prices):.2f} - ${max(prices):.2f}",
                    'sources_count': len(prices),
                    'price_spread': max(prices) - min(prices) if len(prices) > 1 else 0,
                    'average_change': sum(changes) / len(changes) if changes else 0
                }
                
                # Identify significant movements
                avg_change = sum(changes) / len(changes) if changes else 0
                if abs(avg_change) > 2.0:  # >2% change is significant
                    direction = "up" if avg_change > 0 else "down"
                    analysis['significant_movements'].append({
                        'commodity': commodity,
                        'direction': direction,
                        'magnitude': abs(avg_change),
                        'impact': 'high' if abs(avg_change) > 5 else 'moderate'
                    })
        
        # Determine overall market sentiment
        if analysis['significant_movements']:
            positive_moves = sum(1 for move in analysis['significant_movements'] if move['direction'] == 'up')
            negative_moves = sum(1 for move in analysis['significant_movements'] if move['direction'] == 'down')
            
            if positive_moves > negative_moves:
                analysis['market_sentiment'] = 'bullish'
            elif negative_moves > positive_moves:
                analysis['market_sentiment'] = 'bearish'
            else:
                analysis['market_sentiment'] = 'mixed'
        
        # Generate investment implications
        for move in analysis['significant_movements']:
            if move['commodity'] in ['gold', 'silver'] and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    f"Rising {move['commodity']} prices may indicate flight to safety or inflation concerns"
                )
            elif move['commodity'] == 'copper' and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    "Copper price increase suggests economic growth expectations"
                )
            elif move['commodity'] in ['lithium', 'cobalt'] and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    f"{move['commodity'].title()} price rise driven by EV and battery demand"
                )
        
        return analysis
    
    def _generate_target_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary for the target scraping session"""
        
        summary = {
            'scraping_session': {
                'target_date': '2025-08-04',
                'sites_attempted': len([entry for entry in results['performance_log']]),
                'sites_successful': len([entry for entry in results['performance_log'] if entry.get('success', False)]),
                'total_duration': None
            },
            'data_quality': {
                'commodities_found': 0,
                'consensus_prices': 0,
                'market_commentary_pieces': 0
            },
            'performance_metrics': {
                'average_response_time': 0.0,
                'fastest_site': None,
                'slowest_site': None,
                'most_data_rich_site': None
            },
            'market_highlights': [],
            'scraping_challenges': []
        }
        
        # Calculate total commodities found
        for category in results['commodity_data'].values():
            for commodity_sources in category.values():
                summary['data_quality']['commodities_found'] += len(commodity_sources)
        
        # Calculate consensus prices
        summary['data_quality']['consensus_prices'] = len(results.get('market_analysis', {}).get('price_consensus', {}))
        
        # Performance metrics
        successful_entries = [entry for entry in results['performance_log'] if entry.get('success', False)]
        if successful_entries:
            response_times = [entry['response_time'] for entry in successful_entries]
            summary['performance_metrics']['average_response_time'] = sum(response_times) / len(response_times)
            
            fastest = min(successful_entries, key=lambda x: x['response_time'])
            slowest = max(successful_entries, key=lambda x: x['response_time'])
            most_data = max(successful_entries, key=lambda x: x.get('commodities_found', 0))
            
            summary['performance_metrics']['fastest_site'] = f"{fastest['display_name']} ({fastest['response_time']:.1f}s)"
            summary['performance_metrics']['slowest_site'] = f"{slowest['display_name']} ({slowest['response_time']:.1f}s)"
            summary['performance_metrics']['most_data_rich_site'] = f"{most_data['display_name']} ({most_data.get('commodities_found', 0)} commodities)"
        
        # Market highlights from analysis
        if 'market_analysis' in results and 'significant_movements' in results['market_analysis']:
            for move in results['market_analysis']['significant_movements']:
                summary['market_highlights'].append(
                    f"{move['commodity'].title()} {move['direction']} {move['magnitude']:.1f}% - {move['impact']} impact"
                )
        
        # Scraping challenges
        summary['scraping_challenges'] = results.get('errors', [])
        
        # Calculate total duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_session']['total_duration'] = (end - start).total_seconds()
        
        return summary
    
    async def _save_target_results(self, results: Dict[str, Any]):
        """Save target scraping results to the specified path"""
        
        # Save to the requested path: reports/2025-08-04/metal_prices_data.json
        target_file = Path("/Projects/Resource Capital/reports/2025-08-04/metal_prices_data.json")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Also save to our standard data directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        standard_file = self.data_dir / "raw" / f"target_metal_prices_{timestamp}.json"
        with open(standard_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Target metal prices data saved to:")
        print(f"   Primary: {target_file}")
        print(f"   Backup: {standard_file}")
    
    async def _scrape_currency_data(self) -> Dict[str, Any]:
        """Scrape relevant currency data for commodity analysis"""
        
        currency_data = {
            'scraped_at': datetime.now().isoformat(),
            'rates': {}
        }
        
        for currency_pair, url in self.currency_sources.items():
            try:
                strategy = ScrapingStrategy()
                strategy.primary = 'playwright'
                strategy.fallbacks = ['crawl4ai', 'requests']
                
                result = await self.unified_scraper.scrape(url=url, strategy=strategy)
                
                if result.success:
                    # Extract currency rate
                    rate_data = self._extract_currency_rate(result.content, currency_pair)
                    currency_data['rates'][currency_pair] = rate_data
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error scraping {currency_pair}: {str(e)}")
                continue
        
        return currency_data
    
    def _extract_price_data(self, content: str, selectors: Dict, source: str, metal: str) -> Dict[str, Any]:
        """Extract price data from scraped content using configured selectors"""
        
        extracted = {
            'price': None,
            'change': None,
            'change_percent': None,
            'volume': None,
            'timestamp': datetime.now().isoformat(),
            'extraction_method': 'regex_patterns'
        }
        
        # Define price extraction patterns for different metals
        price_patterns = {
            'gold': [
                r'\$?([0-9,]+\.?[0-9]*)\s*(?:per\s+ounce|/oz|USD)',
                r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',  # General price pattern
            ],
            'silver': [
                r'\$?([0-9,]+\.?[0-9]*)\s*(?:per\s+ounce|/oz|USD)',
                r'(\d{1,3}(?:\.\d{2})?)',  # Silver typically lower price
            ],
            'copper': [
                r'\$?([0-9,]+\.?[0-9]*)\s*(?:per\s+pound|/lb|per\s+ton)',
                r'(\d+\.\d{3,4})',  # Copper prices often have more decimals
            ]
        }
        
        # Try to extract price using metal-specific patterns
        if metal in price_patterns:
            for pattern in price_patterns[metal]:
                match = re.search(pattern, content)
                if match:
                    try:
                        price_str = match.group(1).replace(',', '')
                        extracted['price'] = float(price_str)
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Try to extract change/percentage
        change_patterns = [
            r'([+-]?\$?[0-9,]+\.?[0-9]*)\s*\(([+-]?[0-9]+\.?[0-9]*%?)\)',
            r'([+-]?[0-9]+\.?[0-9]*%)',
            r'([+-]?\$?[0-9,]+\.?[0-9]*)\s*change'
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    if '%' in match.group():
                        extracted['change_percent'] = match.group().replace('%', '').strip()
                    else:
                        extracted['change'] = match.group(1).replace('$', '').replace(',', '').strip()
                    break
                except (IndexError, AttributeError):
                    continue
        
        return extracted
    
    def _extract_currency_rate(self, content: str, currency_pair: str) -> Dict[str, Any]:
        """Extract currency exchange rate from content"""
        
        rate_data = {
            'pair': currency_pair,
            'rate': None,
            'change': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Currency rate patterns
        rate_patterns = [
            r'(\d+\.\d{4,6})',  # Typical forex rate format
            r'(\d+\.\d{2,4})',  # Alternative format
        ]
        
        for pattern in rate_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    rate_data['rate'] = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        return rate_data
    
    def _generate_price_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for scraped price data"""
        
        summary = {
            'total_metals_scraped': 0,
            'successful_sources': 0,
            'failed_sources': len(results['errors']),
            'metals_with_consensus': 0,
            'average_price_spread': 0.0,
            'scraping_duration': None
        }
        
        # Count successful metals
        all_metals = {**results['precious_metals'], **results['base_metals'], **results['energy_commodities']}
        summary['total_metals_scraped'] = len(all_metals)
        
        # Count successful sources and consensus prices
        spreads = []
        for metal_data in all_metals.values():
            summary['successful_sources'] += len(metal_data.get('sources', {}))
            
            if metal_data.get('consolidated_price'):
                summary['metals_with_consensus'] += 1
                spread = metal_data['consolidated_price'].get('price_spread', 0)
                if spread > 0:
                    spreads.append(spread)
        
        if spreads:
            summary['average_price_spread'] = sum(spreads) / len(spreads)
        
        # Calculate scraping duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_duration'] = (end - start).total_seconds()
        
        return summary
    
    async def _save_price_data(self, results: Dict[str, Any]):
        """Save scraped price data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw data
        raw_file = self.data_dir / "raw" / f"metal_prices_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save monthly data
        monthly_dir = self.data_dir / datetime.now().strftime("%Y-%m")
        monthly_file = monthly_dir / f"prices_{timestamp}.json"
        with open(monthly_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Metal prices data saved to:")
        print(f"   Raw: {raw_file}")
        print(f"   Monthly: {monthly_file}")
    
    async def get_historical_prices(self, metal: str, days: int = 30) -> List[Dict[str, Any]]:
        """Retrieve historical price data for a specific metal"""
        
        historical_data = []
        
        # Look through historical files
        for days_back in range(days):
            date = datetime.now() - timedelta(days=days_back)
            date_str = date.strftime("%Y-%m")
            monthly_dir = self.data_dir / date_str
            
            if monthly_dir.exists():
                for file_path in monthly_dir.glob("prices_*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extract data for specific metal
                        for category in ['precious_metals', 'base_metals', 'energy_commodities']:
                            if metal in data.get(category, {}):
                                metal_data = data[category][metal]
                                if metal_data.get('consolidated_price'):
                                    historical_data.append({
                                        'date': data.get('scraping_started'),
                                        'price': metal_data['consolidated_price']['average'],
                                        'sources_count': metal_data['consolidated_price']['sources_count']
                                    })
                                break
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(historical_data, key=lambda x: x['date'])
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        await self.unified_scraper.cleanup()


# Convenience functions
async def scrape_target_metal_sites() -> Dict[str, Any]:
    """Convenience function to scrape the 4 target metal price sites for August 4, 2025"""
    scraper = MetalPricesScraper()
    try:
        return await scraper.scrape_target_metal_sites()
    finally:
        await scraper.cleanup()

async def scrape_all_metal_prices() -> Dict[str, Any]:
    """Convenience function to scrape all metal prices (legacy)"""
    scraper = MetalPricesScraper()
    try:
        return await scraper.scrape_all_metal_prices()
    finally:
        await scraper.cleanup()


async def get_metal_price_history(metal: str, days: int = 30) -> List[Dict[str, Any]]:
    """Convenience function to get historical prices for a metal"""
    scraper = MetalPricesScraper()
    try:
        return await scraper.get_historical_prices(metal, days)
    finally:
        await scraper.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        print("💰 Metal Prices Scraper - Specialized Price Intelligence")
        print("=" * 60)
        
        scraper = MetalPricesScraper()
        
        try:
            # Test comprehensive price scraping
            print("\n🚀 Testing comprehensive metal price scraping...")
            results = await scraper.scrape_all_metal_prices()
            
            print(f"\n📊 PRICE SCRAPING SUMMARY:")
            print(f"   Total Metals: {results['summary']['total_metals_scraped']}")
            print(f"   Successful Sources: {results['summary']['successful_sources']}")
            print(f"   Metals with Consensus: {results['summary']['metals_with_consensus']}")
            print(f"   Average Price Spread: ${results['summary']['average_price_spread']:.2f}")
            print(f"   Scraping Duration: {results['summary']['scraping_duration']:.1f}s")
            
            if results['errors']:
                print(f"   Errors: {len(results['errors'])}")
            
            # Show sample data
            if results['precious_metals']:
                print(f"\n🥇 PRECIOUS METALS SAMPLE:")
                for metal, data in results['precious_metals'].items():
                    if data.get('consolidated_price'):
                        avg_price = data['consolidated_price']['average']
                        sources = data['consolidated_price']['sources_count']
                        print(f"   {metal.title()}: ${avg_price:.2f} (from {sources} sources)")
            
        finally:
            await scraper.cleanup()
    
    asyncio.run(main())