#!/usr/bin/env python3
"""
Robust Commodity Price Scraper
Extracts real-time commodity prices from multiple reliable sources
Built for mining intelligence operations with anti-bot protection

Author: Mining Intelligence System
Date: 2025-08-04
"""

import requests
import json
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import re
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CommodityPrice:
    """Data structure for commodity price information"""
    name: str
    price: float
    currency: str
    change_absolute: Optional[float] = None
    change_percentage: Optional[str] = None
    last_update: Optional[str] = None
    market_trend: Optional[str] = None
    source: str = ""
    raw_data: Optional[Dict] = None

class RobustCommodityScraper:
    """
    Anti-fragile commodity price scraper with multiple fallback strategies
    Implements comprehensive bot protection countermeasures
    """
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.session = requests.Session()
        self.setup_session()
        
        # Critical mining commodities to track
        self.target_commodities = {
            'precious_metals': ['gold', 'silver', 'platinum', 'palladium'],
            'base_metals': ['copper', 'nickel', 'zinc', 'aluminum'],
            'battery_metals': ['lithium', 'cobalt'],
            'energy_metals': ['uranium']
        }
        
        # Price extraction results
        self.extracted_prices = {}
        self.errors = []
        self.performance_log = []
        
    def setup_session(self):
        """Configure session with anti-bot protection measures"""
        # Randomize user agent
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Set session timeout and retries
        self.session.timeout = 30
        
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Implement random delays to appear more human-like"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting {delay:.2f} seconds before next request...")
        time.sleep(delay)
        
    def safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make safe HTTP requests with retry logic and error handling
        """
        for attempt in range(max_retries):
            try:
                # Randomize user agent for each request
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                logger.info(f"Requesting: {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"Successfully fetched {url} - Content length: {len(response.content)}")
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url} - Bot detection possible")
                    if attempt < max_retries - 1:
                        self.random_delay(3.0, 8.0)  # Longer delay for bot detection
                elif response.status_code == 429:
                    logger.warning(f"429 Rate Limited for {url}")
                    if attempt < max_retries - 1:
                        self.random_delay(10.0, 20.0)  # Much longer delay for rate limiting
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout requesting {url}")
                if attempt < max_retries - 1:
                    self.random_delay(2.0, 5.0)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception for {url}: {e}")
                if attempt < max_retries - 1:
                    self.random_delay(2.0, 5.0)
                    
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
        
    def extract_kitco_precious_metals(self) -> Dict[str, CommodityPrice]:
        """Extract precious metals prices from Kitco.com"""
        start_time = time.time()
        url = "https://www.kitco.com/market/"
        
        try:
            response = self.safe_request(url)
            if not response:
                raise Exception("Failed to fetch Kitco page")
                
            content = response.text
            prices = {}
            
            # Look for JSON data containing live prices
            json_pattern = r'window\.__PRELOADED_STATE__\s*=\s*({.*?});'
            json_match = re.search(json_pattern, content, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Navigate through the data structure to find price information
                    if 'market' in data and 'metals' in data['market']:
                        metals_data = data['market']['metals']
                        
                        for metal_key, metal_data in metals_data.items():
                            if metal_key.lower() in ['gold', 'silver', 'platinum', 'palladium']:
                                if 'price' in metal_data and 'change' in metal_data:
                                    prices[metal_key.lower()] = CommodityPrice(
                                        name=metal_key.capitalize(),
                                        price=float(metal_data['price']),
                                        currency='USD',
                                        change_absolute=metal_data.get('change'),
                                        change_percentage=metal_data.get('changePercent'),
                                        last_update=datetime.now(timezone.utc).isoformat(),
                                        source='kitco_precious',
                                        raw_data=metal_data
                                    )
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Kitco JSON data")
            
            # Fallback: Look for price data in HTML tables or spans
            if not prices:
                # Pattern for price extraction from HTML
                price_patterns = [
                    r'gold.*?(\$[\d,]+\.?\d*)',
                    r'silver.*?(\$[\d,]+\.?\d*)',
                    r'platinum.*?(\$[\d,]+\.?\d*)',
                    r'palladium.*?(\$[\d,]+\.?\d*)'
                ]
                
                for metal in ['gold', 'silver', 'platinum', 'palladium']:
                    pattern = rf'{metal}.*?(\$[\d,]+\.?\d*)'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        price_str = matches[0].replace('$', '').replace(',', '')
                        try:
                            price = float(price_str)
                            prices[metal] = CommodityPrice(
                                name=metal.capitalize(),
                                price=price,
                                currency='USD',
                                last_update=datetime.now(timezone.utc).isoformat(),
                                source='kitco_precious'
                            )
                        except ValueError:
                            logger.warning(f"Could not parse price: {price_str}")
            
            response_time = time.time() - start_time
            self.performance_log.append({
                'site': 'kitco_precious',
                'success': len(prices) > 0,
                'response_time': response_time,
                'commodities_found': len(prices),
                'error': None if prices else 'No prices extracted'
            })
            
            logger.info(f"Kitco precious metals: Found {len(prices)} prices in {response_time:.2f}s")
            return prices
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Kitco precious metals extraction failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.performance_log.append({
                'site': 'kitco_precious',
                'success': False,
                'response_time': response_time,
                'commodities_found': 0,
                'error': str(e)
            })
            return {}
    
    def extract_trading_economics_prices(self) -> Dict[str, CommodityPrice]:
        """Extract commodity prices from Trading Economics"""
        start_time = time.time()
        url = "https://tradingeconomics.com/commodities"
        
        try:
            response = self.safe_request(url)
            if not response:
                raise Exception("Failed to fetch Trading Economics page")
                
            content = response.text
            prices = {}
            
            # Look for the commodities data table or JSON
            # Trading Economics often loads data via AJAX, so we look for embedded JSON
            json_patterns = [
                r'var\s+commoditiesData\s*=\s*(\[.*?\]);',
                r'window\.commodities\s*=\s*(\[.*?\]);',
                r'"commodities":\s*(\[.*?\])'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        for item in data:
                            if isinstance(item, dict):
                                name = item.get('name', '').lower()
                                symbol = item.get('symbol', '').lower()
                                
                                # Check if this is one of our target commodities
                                commodity_name = None
                                for category, commodities in self.target_commodities.items():
                                    for commodity in commodities:
                                        if commodity in name or commodity in symbol:
                                            commodity_name = commodity
                                            break
                                    if commodity_name:
                                        break
                                
                                if commodity_name and 'last' in item:
                                    prices[commodity_name] = CommodityPrice(
                                        name=commodity_name.capitalize(),
                                        price=float(item['last']),
                                        currency=item.get('currency', 'USD'),
                                        change_absolute=item.get('change'),
                                        change_percentage=item.get('changePercent'),
                                        last_update=datetime.now(timezone.utc).isoformat(),
                                        source='trading_economics',
                                        raw_data=item
                                    )
                        break
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse Trading Economics JSON: {e}")
                        continue
            
            # Fallback: Extract from HTML table structure
            if not prices:
                # Look for table rows with commodity data
                table_pattern = r'<tr[^>]*>.*?</tr>'
                rows = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
                
                for row in rows:
                    for category, commodities in self.target_commodities.items():
                        for commodity in commodities:
                            if commodity.lower() in row.lower():
                                # Extract price from the row
                                price_match = re.search(r'([\d,]+\.?\d*)', row)
                                if price_match:
                                    try:
                                        price = float(price_match.group(1).replace(',', ''))
                                        prices[commodity] = CommodityPrice(
                                            name=commodity.capitalize(),
                                            price=price,
                                            currency='USD',
                                            last_update=datetime.now(timezone.utc).isoformat(),
                                            source='trading_economics'
                                        )
                                    except ValueError:
                                        continue
            
            response_time = time.time() - start_time
            self.performance_log.append({
                'site': 'trading_economics',
                'success': len(prices) > 0,
                'response_time': response_time,
                'commodities_found': len(prices),
                'error': None if prices else 'No prices extracted'
            })
            
            logger.info(f"Trading Economics: Found {len(prices)} prices in {response_time:.2f}s")
            return prices
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Trading Economics extraction failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.performance_log.append({
                'site': 'trading_economics',
                'success': False,
                'response_time': response_time,
                'commodities_found': 0,
                'error': str(e)
            })
            return {}
    
    def extract_daily_metal_price(self) -> Dict[str, CommodityPrice]:
        """Extract metal prices from Daily Metal Price"""
        start_time = time.time()
        url = "https://www.dailymetalprice.com/"
        
        try:
            response = self.safe_request(url)
            if not response:
                raise Exception("Failed to fetch Daily Metal Price page")
                
            content = response.text
            prices = {}
            
            # Look for price tables or structured data
            # This site typically shows prices in tables
            table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
            
            for row in table_rows:
                for category, commodities in self.target_commodities.items():
                    for commodity in commodities:
                        if commodity.lower() in row.lower():
                            # Extract price and change information
                            price_patterns = [
                                r'\$?([\d,]+\.?\d*)',
                                r'([\d,]+\.?\d*)\s*USD',
                                r'Price:\s*([\d,]+\.?\d*)'
                            ]
                            
                            for pattern in price_patterns:
                                price_match = re.search(pattern, row)
                                if price_match:
                                    try:
                                        price = float(price_match.group(1).replace(',', ''))
                                        
                                        # Try to extract change information
                                        change_match = re.search(r'([+-]?[\d.]+)%', row)
                                        change_percentage = change_match.group(1) + '%' if change_match else None
                                        
                                        prices[commodity] = CommodityPrice(
                                            name=commodity.capitalize(),
                                            price=price,
                                            currency='USD',
                                            change_percentage=change_percentage,
                                            last_update=datetime.now(timezone.utc).isoformat(),
                                            source='daily_metal_price'
                                        )
                                        break
                                    except ValueError:
                                        continue
                            if commodity in prices:
                                break
                    if commodity in prices:
                        break
            
            response_time = time.time() - start_time
            self.performance_log.append({
                'site': 'daily_metal_price',
                'success': len(prices) > 0,
                'response_time': response_time,
                'commodities_found': len(prices),
                'error': None if prices else 'No prices extracted'
            })
            
            logger.info(f"Daily Metal Price: Found {len(prices)} prices in {response_time:.2f}s")
            return prices
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Daily Metal Price extraction failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.performance_log.append({
                'site': 'daily_metal_price',
                'success': False,
                'response_time': response_time,
                'commodities_found': 0,
                'error': str(e)
            })
            return {}
    
    def extract_lme_prices(self) -> Dict[str, CommodityPrice]:
        """Attempt to extract LME official pricing data"""
        start_time = time.time()
        # LME has an API but it requires authentication
        # We'll try to get public data from their website
        url = "https://www.lme.com/en/metals/non-ferrous"
        
        try:
            response = self.safe_request(url)
            if not response:
                raise Exception("Failed to fetch LME page")
                
            content = response.text
            prices = {}
            
            # LME data is often loaded via JavaScript, look for embedded data
            lme_metals = ['copper', 'nickel', 'zinc', 'aluminum']
            
            for metal in lme_metals:
                # Look for price data patterns specific to LME
                patterns = [
                    rf'{metal}.*?(\d+\.?\d*)',
                    rf'"{metal}".*?"price":\s*"?(\d+\.?\d*)"?',
                    rf'{metal.upper()}.*?(\d+\.?\d*)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        try:
                            price = float(matches[0])
                            # LME prices are typically in USD per tonne
                            prices[metal] = CommodityPrice(
                                name=metal.capitalize(),
                                price=price,
                                currency='USD/tonne',
                                last_update=datetime.now(timezone.utc).isoformat(),
                                source='lme_official'
                            )
                            break
                        except ValueError:
                            continue
            
            response_time = time.time() - start_time
            self.performance_log.append({
                'site': 'lme_official',
                'success': len(prices) > 0,
                'response_time': response_time,
                'commodities_found': len(prices),
                'error': None if prices else 'LME data requires API access'
            })
            
            logger.info(f"LME Official: Found {len(prices)} prices in {response_time:.2f}s")
            return prices
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"LME extraction failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.performance_log.append({
                'site': 'lme_official',
                'success': False,
                'response_time': response_time,
                'commodities_found': 0,
                'error': str(e)
            })
            return {}
    
    def run_comprehensive_scrape(self) -> Dict:
        """Execute comprehensive commodity price scraping from all sources"""
        start_time = datetime.now(timezone.utc)
        logger.info("Starting comprehensive commodity price scraping...")
        
        all_sources = {}
        
        # 1. Kitco Precious Metals
        logger.info("Extracting Kitco precious metals prices...")
        kitco_precious = self.extract_kitco_precious_metals()
        if kitco_precious:
            all_sources['kitco_precious'] = kitco_precious
        self.random_delay()
        
        # 2. Trading Economics
        logger.info("Extracting Trading Economics commodity prices...")
        trading_economics = self.extract_trading_economics_prices()
        if trading_economics:
            all_sources['trading_economics'] = trading_economics
        self.random_delay()
        
        # 3. Daily Metal Price
        logger.info("Extracting Daily Metal Price data...")
        daily_metal = self.extract_daily_metal_price()
        if daily_metal:
            all_sources['daily_metal_price'] = daily_metal
        self.random_delay()
        
        # 4. LME Official (if accessible)
        logger.info("Attempting LME official data extraction...")
        lme_data = self.extract_lme_prices()
        if lme_data:
            all_sources['lme_official'] = lme_data
        
        # Convert CommodityPrice objects to dictionaries for JSON serialization
        serializable_sources = {}
        for source_name, commodities in all_sources.items():
            serializable_sources[source_name] = {}
            for commodity_name, commodity_obj in commodities.items():
                serializable_sources[source_name][commodity_name] = asdict(commodity_obj)
        
        # Consolidate and analyze results
        consolidated = self.consolidate_prices(all_sources)
        
        end_time = datetime.now(timezone.utc)
        
        return {
            'scraping_started': start_time.isoformat(),
            'scraping_completed': end_time.isoformat(),
            'total_duration': (end_time - start_time).total_seconds(),
            'sources_scraped': serializable_sources,
            'consolidated_prices': consolidated,
            'performance_log': self.performance_log,
            'errors': self.errors,
            'summary': {
                'sources_attempted': len(self.performance_log),
                'sources_successful': sum(1 for log in self.performance_log if log['success']),
                'unique_commodities': len(consolidated),
                'total_data_points': sum(len(source) for source in serializable_sources.values())
            }
        }
    
    def consolidate_prices(self, all_sources: Dict) -> Dict:
        """Consolidate prices from multiple sources and calculate consensus"""
        consolidated = {}
        
        # Get all unique commodities
        all_commodities = set()
        for source_data in all_sources.values():
            all_commodities.update(source_data.keys())
        
        for commodity in all_commodities:
            commodity_data = {}
            prices = []
            changes = []
            sources_count = 0
            
            for source_name, source_data in all_sources.items():
                if commodity in source_data:
                    price_obj = source_data[commodity]
                    commodity_data[source_name] = {
                        'price': price_obj.price,
                        'currency': price_obj.currency,
                        'change_absolute': price_obj.change_absolute,
                        'change_percentage': price_obj.change_percentage,
                        'last_update': price_obj.last_update,
                        'source': price_obj.source
                    }
                    prices.append(price_obj.price)
                    if price_obj.change_absolute:
                        changes.append(price_obj.change_absolute)
                    sources_count += 1
            
            # Calculate consensus metrics
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                price_variance = max_price - min_price if len(prices) > 1 else 0
                
                commodity_data['consensus'] = {
                    'average_price': round(avg_price, 2),
                    'price_range': f"${min_price:.2f} - ${max_price:.2f}",
                    'price_variance': round(price_variance, 2),
                    'sources_count': sources_count,
                    'confidence': 'high' if sources_count >= 3 else 'medium' if sources_count >= 2 else 'low'
                }
                
                if changes:
                    avg_change = sum(changes) / len(changes)
                    commodity_data['consensus']['average_change'] = round(avg_change, 2)
            
            consolidated[commodity] = commodity_data
        
        return consolidated

def main():
    """Main execution function"""
    scraper = RobustCommodityScraper()
    
    # Run comprehensive scraping
    results = scraper.run_comprehensive_scrape()
    
    # Save results to JSON file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'commodity_prices_real_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Scraping completed. Results saved to {output_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("COMMODITY PRICE SCRAPING SUMMARY")
    print("="*80)
    print(f"Total Duration: {results['total_duration']:.2f} seconds")
    print(f"Sources Attempted: {results['summary']['sources_attempted']}")
    print(f"Sources Successful: {results['summary']['sources_successful']}")
    print(f"Unique Commodities: {results['summary']['unique_commodities']}")
    print(f"Total Data Points: {results['summary']['total_data_points']}")
    
    if results['consolidated_prices']:
        print("\nCONSOLIDATED PRICES:")
        print("-" * 40)
        for commodity, data in results['consolidated_prices'].items():
            if 'consensus' in data:
                consensus = data['consensus']
                print(f"{commodity.upper():12} | ${consensus['average_price']:>8.2f} | "
                      f"{consensus['price_range']:>15} | "
                      f"Sources: {consensus['sources_count']} | "
                      f"Confidence: {consensus['confidence'].upper()}")
    
    if results['errors']:
        print(f"\nERRORS ENCOUNTERED: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    return results

if __name__ == "__main__":
    main()