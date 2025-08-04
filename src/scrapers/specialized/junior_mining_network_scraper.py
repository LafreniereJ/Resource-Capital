#!/usr/bin/env python3
"""
Junior Mining Network Scraper
Specialized scraper for Junior Mining Network websites

Target URLs:
1. Junior Mining Network - https://www.juniorminingnetwork.com/
2. Junior Mining Network Heat Map - https://www.juniorminingnetwork.com/heat-map.html
3. Junior Mining Network Market Data - https://www.juniorminingnetwork.com/market-data.html

Focuses on:
- Junior mining company news and announcements
- Stock performance data and market metrics
- Interactive heat maps showing sector performance
- Company names, stock symbols, and performance metrics
- Market analysis, sector trends, and investment insights
- Merger, acquisition, and partnership news
- Production updates and exploration results
"""

import asyncio
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import unified scraper components
from ..unified_scraper import UnifiedScraper, ScrapingStrategy, ScrapingResult


class JuniorMiningNetworkScraper:
    """Specialized scraper for Junior Mining Network websites"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("reports/2025-08-04")
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Ensure data directories exist
        self._setup_data_directories()
        
        # Initialize unified scraper
        self.unified_scraper = UnifiedScraper()
        
        # Target URLs for Junior Mining Network
        self.target_urls = {
            "main_site": {
                "url": "https://www.juniorminingnetwork.com/",
                "name": "Junior Mining Network Main",
                "description": "Main portal for junior mining company news and insights",
                "expected_content": ["mining companies", "news", "junior miners", "exploration"]
            },
            "heat_map": {
                "url": "https://www.juniorminingnetwork.com/heat-map.html",
                "name": "Junior Mining Network Heat Map",
                "description": "Interactive heat map showing mining sector performance",
                "expected_content": ["heat map", "performance", "stock prices", "sector analysis"]
            },
            "market_data": {
                "url": "https://www.juniorminingnetwork.com/market-data.html",
                "name": "Junior Mining Network Market Data",
                "description": "Market data and performance metrics for junior mining companies",
                "expected_content": ["market data", "stock performance", "financial metrics", "trading data"]
            }
        }
        
        # Data extraction patterns for junior mining companies
        self.extraction_patterns = {
            "company_names": [
                r'([A-Z][A-Za-z\s&]+(?:Mining|Resources|Gold|Silver|Copper|Exploration|Corp|Inc|Ltd))',
                r'<[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</[^>]*>',
                r'<[^>]*title="([^"]*(?:Mining|Resources|Gold|Silver|Copper)[^"]*)"[^>]*>'
            ],
            "stock_symbols": [
                r'\b([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\b',
                r'Symbol:\s*([A-Z]{2,5}(?:\.[A-Z]{1,2})?)',
                r'Ticker:\s*([A-Z]{2,5}(?:\.[A-Z]{1,2})?)',
                r'\(([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\)'
            ],
            "stock_prices": [
                r'\$(\d+\.\d{2,4})',
                r'Price:\s*\$?(\d+\.\d{2,4})',
                r'Last:\s*\$?(\d+\.\d{2,4})',
                r'(\d+\.\d{2,4})\s*(?:CAD|USD)?'
            ],
            "price_changes": [
                r'([+-]?\d+\.\d{2,4})\s*\([+-]?\d+\.\d{1,2}%\)',
                r'Change:\s*([+-]?\d+\.\d{2,4})',
                r'([+-]?\d+\.\d{1,2})%',
                r'([+-]\d+\.\d{2,4})'
            ],
            "market_cap": [
                r'Market Cap:?\s*\$?(\d+(?:\.\d+)?[BMK]?)',
                r'(\d+(?:\.\d+)?)\s*(?:Billion|Million|B|M)',
                r'Cap:\s*\$?(\d+(?:\.\d+)?[BMK]?)'
            ],
            "volume": [
                r'Volume:?\s*(\d+(?:,\d{3})*)',
                r'Vol:\s*(\d+(?:,\d{3})*)',
                r'(\d+(?:,\d{3})*)\s*shares?'
            ],
            "news_headlines": [
                r'<[^>]*class="[^"]*(?:headline|title|news)[^"]*"[^>]*>([^<]+)</[^>]*>',
                r'<h[1-6][^>]*>([^<]*(?:mining|exploration|production|acquisition)[^<]*)</h[1-6]>',
                r'<[^>]*class="[^"]*article[^"]*"[^>]*>[^<]*<[^>]*>([^<]+)</[^>]*>'
            ],
            "dates": [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})'
            ]
        }
        
        # Performance tracking
        self.performance_log = {
            "session_started": datetime.now().isoformat(),
            "sites_attempted": [],
            "extraction_stats": {},
            "errors": [],
            "success_metrics": {}
        }
    
    def _setup_data_directories(self):
        """Create necessary data directories"""
        base_dirs = [
            self.data_dir,
            self.data_dir.parent / "logs",
            Path("logs/scraper_performance")
        ]
        
        for directory in base_dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def scrape_all_junior_mining_sites(self) -> Dict[str, Any]:
        """Scrape all Junior Mining Network target sites"""
        
        print("🏗️ Starting Junior Mining Network comprehensive scraping...")
        print("=" * 70)
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'target_sites': list(self.target_urls.keys()),
            'site_results': {},
            'consolidated_data': {
                'companies': {},
                'market_overview': {},
                'news_items': [],
                'heat_map_data': {},
                'market_metrics': {}
            },
            'performance_summary': {},
            'errors': []
        }
        
        # Scrape each target URL
        for site_key, site_info in self.target_urls.items():
            print(f"\n🎯 Scraping: {site_info['name']}")
            print(f"   URL: {site_info['url']}")
            
            try:
                site_start_time = time.time()
                
                # Create optimized scraping strategy for each site type
                strategy = self._create_scraping_strategy(site_key)
                
                # Perform the scrape
                scrape_result = await self.unified_scraper.scrape(
                    url=site_info['url'], 
                    strategy=strategy
                )
                
                site_duration = time.time() - site_start_time
                
                if scrape_result.success:
                    print(f"   ✅ Successfully scraped ({scrape_result.scraper_used})")
                    print(f"   📄 Content length: {len(scrape_result.content):,} chars")
                    print(f"   ⏱️ Duration: {site_duration:.2f}s")
                    
                    # Extract structured data from the scraped content
                    extracted_data = await self._extract_site_data(
                        site_key, site_info, scrape_result
                    )
                    
                    results['site_results'][site_key] = {
                        'site_info': site_info,
                        'scrape_result': {
                            'success': True,
                            'scraper_used': scrape_result.scraper_used,
                            'content_length': len(scrape_result.content),
                            'word_count': scrape_result.word_count,
                            'title': scrape_result.title,
                            'timestamp': scrape_result.timestamp.isoformat(),
                            'duration': site_duration
                        },
                        'extracted_data': extracted_data
                    }
                    
                    # Merge extracted data into consolidated results
                    await self._merge_extracted_data(results['consolidated_data'], extracted_data)
                    
                    # Track performance metrics
                    self.performance_log['sites_attempted'].append({
                        'site': site_key,
                        'url': site_info['url'],
                        'success': True,
                        'duration': site_duration,
                        'scraper_used': scrape_result.scraper_used,
                        'content_size': len(scrape_result.content)
                    })
                    
                else:
                    error_msg = f"Failed to scrape {site_info['name']}: {scrape_result.error}"
                    print(f"   ❌ {error_msg}")
                    results['errors'].append(error_msg)
                    
                    self.performance_log['sites_attempted'].append({
                        'site': site_key,
                        'url': site_info['url'],
                        'success': False,
                        'error': scrape_result.error,
                        'duration': site_duration
                    })
                
                # Rate limiting between sites
                await asyncio.sleep(2)
                
            except Exception as e:
                error_msg = f"Exception scraping {site_info['name']}: {str(e)}"
                print(f"   💥 {error_msg}")
                results['errors'].append(error_msg)
                
                self.performance_log['errors'].append({
                    'site': site_key,
                    'url': site_info['url'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Generate comprehensive summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['performance_summary'] = self._generate_performance_summary(results)
        
        # Save results
        await self._save_mining_data(results)
        
        # Update performance log
        self.performance_log['session_completed'] = datetime.now().isoformat()
        await self._save_performance_log()
        
        return results
    
    def _create_scraping_strategy(self, site_key: str) -> ScrapingStrategy:
        """Create optimized scraping strategy based on site type"""
        
        if site_key == "heat_map":
            # Heat map likely requires JavaScript for interactive elements
            strategy = ScrapingStrategy(
                primary='playwright',
                fallbacks=['crawl4ai', 'requests'],
                timeout=30,
                retries=2,
                rate_limit=3.0
            )
            
        elif site_key == "market_data":
            # Market data might be dynamically loaded
            strategy = ScrapingStrategy(
                primary='playwright',
                fallbacks=['crawl4ai', 'requests'],
                timeout=30,
                retries=2,
                rate_limit=2.0
            )
            
        else:
            # Main site - start with faster methods
            strategy = ScrapingStrategy(
                primary='crawl4ai',
                fallbacks=['playwright', 'requests'],
                timeout=30,
                retries=2,
                rate_limit=2.0
            )
        
        return strategy
    
    async def _extract_site_data(self, site_key: str, site_info: Dict, scrape_result: ScrapingResult) -> Dict[str, Any]:
        """Extract structured data from scraped site content"""
        
        print(f"   🔍 Extracting data from {site_info['name']}...")
        
        extracted = {
            'site_key': site_key,
            'site_name': site_info['name'],
            'extraction_timestamp': datetime.now().isoformat(),
            'companies_found': [],
            'news_items': [],
            'market_data': {},
            'heat_map_data': {},
            'performance_metrics': {},
            'raw_content_sample': scrape_result.content[:1000] if scrape_result.content else ""
        }
        
        content = scrape_result.content
        
        if not content:
            print(f"   ⚠️ No content available for extraction")
            return extracted
        
        # Parse HTML content for better extraction
        try:
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text()
        except Exception:
            text_content = content
            soup = None
        
        # Extract companies based on site type
        if site_key == "main_site":
            companies = await self._extract_main_site_companies(content, soup)
            news = await self._extract_news_items(content, soup)
            extracted['companies_found'] = companies
            extracted['news_items'] = news
            
        elif site_key == "heat_map":
            heat_map_data = await self._extract_heat_map_data(content, soup)
            companies = await self._extract_heat_map_companies(content, soup)
            extracted['heat_map_data'] = heat_map_data
            extracted['companies_found'] = companies
            
        elif site_key == "market_data":
            market_data = await self._extract_market_data(content, soup)
            companies = await self._extract_market_companies(content, soup)
            extracted['market_data'] = market_data
            extracted['companies_found'] = companies
        
        # Universal extraction patterns
        extracted['stock_symbols'] = self._extract_patterns(text_content, self.extraction_patterns['stock_symbols'])
        extracted['stock_prices'] = self._extract_patterns(text_content, self.extraction_patterns['stock_prices'])
        extracted['price_changes'] = self._extract_patterns(text_content, self.extraction_patterns['price_changes'])
        
        print(f"   📊 Found {len(extracted['companies_found'])} companies")
        print(f"   📈 Found {len(extracted['stock_symbols'])} stock symbols")
        print(f"   📰 Found {len(extracted['news_items'])} news items")
        
        return extracted
    
    async def _extract_main_site_companies(self, content: str, soup: Optional[BeautifulSoup]) -> List[Dict[str, Any]]:
        """Extract company information from main site"""
        
        companies = []
        
        if soup:
            # Look for company listings, articles, or mentions
            company_elements = soup.find_all(['div', 'article', 'section'], 
                                           class_=re.compile(r'company|mining|stock', re.I))
            
            for element in company_elements[:20]:  # Limit to first 20
                company_text = element.get_text(strip=True)
                
                # Extract company name using patterns
                company_names = self._extract_patterns(company_text, self.extraction_patterns['company_names'])
                stock_symbols = self._extract_patterns(company_text, self.extraction_patterns['stock_symbols'])
                
                if company_names or stock_symbols:
                    company = {
                        'name': company_names[0] if company_names else 'Unknown',
                        'symbol': stock_symbols[0] if stock_symbols else None,
                        'source_element': element.name,
                        'raw_text': company_text[:200]
                    }
                    companies.append(company)
        
        # Fallback to text-based extraction
        if not companies:
            company_names = self._extract_patterns(content, self.extraction_patterns['company_names'])
            stock_symbols = self._extract_patterns(content, self.extraction_patterns['stock_symbols'])
            
            # Pair up names and symbols
            for i, name in enumerate(company_names[:10]):
                symbol = stock_symbols[i] if i < len(stock_symbols) else None
                companies.append({
                    'name': name,
                    'symbol': symbol,
                    'source': 'text_extraction'
                })
        
        return companies
    
    async def _extract_heat_map_companies(self, content: str, soup: Optional[BeautifulSoup]) -> List[Dict[str, Any]]:
        """Extract company data from heat map page"""
        
        companies = []
        
        if soup:
            # Look for heat map cells, data elements, or performance indicators
            heat_elements = soup.find_all(['div', 'td', 'span'], 
                                        class_=re.compile(r'heat|map|cell|performance|stock', re.I))
            
            for element in heat_elements:
                element_text = element.get_text(strip=True)
                
                # Extract stock data
                symbols = self._extract_patterns(element_text, self.extraction_patterns['stock_symbols'])
                prices = self._extract_patterns(element_text, self.extraction_patterns['stock_prices'])
                changes = self._extract_patterns(element_text, self.extraction_patterns['price_changes'])
                
                if symbols:
                    company = {
                        'symbol': symbols[0],
                        'price': prices[0] if prices else None,
                        'change': changes[0] if changes else None,
                        'heat_map_position': element.get('style', ''),
                        'raw_text': element_text
                    }
                    companies.append(company)
        
        return companies
    
    async def _extract_market_companies(self, content: str, soup: Optional[BeautifulSoup]) -> List[Dict[str, Any]]:
        """Extract company data from market data page"""
        
        companies = []
        
        if soup:
            # Look for market data tables or listings
            table_elements = soup.find_all(['table', 'tbody', 'tr'])
            
            for table in table_elements:
                rows = table.find_all('tr') if table.name == 'table' else [table]
                
                for row in rows:
                    row_text = row.get_text(strip=True)
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 2:  # Likely a data row
                        # Try to extract structured market data
                        symbols = self._extract_patterns(row_text, self.extraction_patterns['stock_symbols'])
                        prices = self._extract_patterns(row_text, self.extraction_patterns['stock_prices'])
                        volumes = self._extract_patterns(row_text, self.extraction_patterns['volume'])
                        market_caps = self._extract_patterns(row_text, self.extraction_patterns['market_cap'])
                        
                        if symbols:
                            company = {
                                'symbol': symbols[0],
                                'price': prices[0] if prices else None,
                                'volume': volumes[0] if volumes else None,
                                'market_cap': market_caps[0] if market_caps else None,
                                'cells_count': len(cells),
                                'raw_text': row_text[:100]
                            }
                            companies.append(company)
        
        return companies
    
    async def _extract_news_items(self, content: str, soup: Optional[BeautifulSoup]) -> List[Dict[str, Any]]:
        """Extract news items and headlines"""
        
        news_items = []
        
        if soup:
            # Look for news articles, headlines, or press releases
            news_elements = soup.find_all(['article', 'div', 'section'], 
                                        class_=re.compile(r'news|article|press|headline|post', re.I))
            
            for element in news_elements[:15]:
                # Extract headline
                headline_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                headline = headline_elem.get_text(strip=True) if headline_elem else None
                
                # Extract date
                date_elem = element.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
                date_text = date_elem.get_text(strip=True) if date_elem else None
                
                # Extract content snippet
                content_text = element.get_text(strip=True)
                
                if headline or (content_text and len(content_text) > 50):
                    news_item = {
                        'headline': headline or content_text[:100],
                        'date': date_text,
                        'content_snippet': content_text[:300],
                        'element_type': element.name,
                        'relevance_score': self._calculate_mining_relevance(content_text)
                    }
                    news_items.append(news_item)
        
        # Sort by relevance score
        news_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return news_items[:10]  # Return top 10 most relevant
    
    async def _extract_heat_map_data(self, content: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract heat map specific data"""
        
        heat_map_data = {
            'sectors_found': [],
            'performance_indicators': [],
            'color_coding': {},
            'interactive_elements': []
        }
        
        if soup:
            # Look for sector classifications
            sector_elements = soup.find_all(text=re.compile(r'gold|silver|copper|zinc|nickel|iron|coal|oil|gas', re.I))
            heat_map_data['sectors_found'] = list(set(sector_elements[:10]))
            
            # Look for performance indicators
            perf_patterns = [r'(\+?\-?\d+\.\d{1,2}%)', r'(up|down|flat)\s+(\d+\.\d{1,2}%)']
            for pattern in perf_patterns:
                matches = re.findall(pattern, content, re.I)
                heat_map_data['performance_indicators'].extend(matches[:10])
        
        return heat_map_data
    
    async def _extract_market_data(self, content: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract market data and metrics"""
        
        market_data = {
            'market_indices': {},
            'trading_metrics': {},
            'sector_performance': {},
            'volume_leaders': []
        }
        
        # Extract market indices
        index_patterns = [
            r'(TSX|TSXV|S&P|Dow|NASDAQ).*?(\d+(?:,\d{3})*\.\d{2})',
            r'Index.*?(\d+(?:,\d{3})*\.\d{2})'
        ]
        
        for pattern in index_patterns:
            matches = re.findall(pattern, content, re.I)
            for match in matches:
                if len(match) == 2:
                    market_data['market_indices'][match[0]] = match[1]
        
        # Extract trading metrics
        volume_pattern = r'Volume:?\s*(\d+(?:,\d{3})*(?:\.\d+)?[BMK]?)'
        volumes = re.findall(volume_pattern, content, re.I)
        market_data['trading_metrics']['volumes_found'] = volumes[:5]
        
        return market_data
    
    def _extract_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Extract data using regex patterns"""
        
        results = []
        for pattern in patterns:
            try:
                matches = re.findall(pattern, text, re.I)
                if isinstance(matches[0], tuple) if matches else False:
                    # Handle tuple matches (groups)
                    results.extend([match[0] if match else '' for match in matches])
                else:
                    results.extend(matches)
            except (IndexError, TypeError):
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for item in results:
            if item and item not in seen:
                seen.add(item)
                unique_results.append(item)
        
        return unique_results[:10]  # Limit results
    
    def _calculate_mining_relevance(self, text: str) -> int:
        """Calculate relevance score for mining industry content"""
        
        mining_keywords = [
            'mining', 'exploration', 'gold', 'silver', 'copper', 'zinc', 'nickel',
            'iron ore', 'coal', 'production', 'reserves', 'resources', 'drill',
            'assay', 'feasibility', 'deposit', 'ore', 'mine', 'junior miner',
            'merger', 'acquisition', 'financing', 'listing', 'tsx', 'tsxv'
        ]
        
        text_lower = text.lower()
        score = 0
        
        for keyword in mining_keywords:
            count = text_lower.count(keyword)
            if keyword in ['mining', 'gold', 'exploration']:
                score += count * 3  # Higher weight for core terms
            else:
                score += count
        
        return score
    
    async def _merge_extracted_data(self, consolidated: Dict[str, Any], extracted: Dict[str, Any]):
        """Merge extracted data into consolidated results"""
        
        # Merge companies
        for company in extracted.get('companies_found', []):
            symbol = company.get('symbol', company.get('name', 'Unknown'))
            if symbol not in consolidated['companies']:
                consolidated['companies'][symbol] = {
                    'name': company.get('name', 'Unknown'),
                    'symbol': company.get('symbol'),
                    'data_sources': []
                }
            
            # Add source-specific data
            source_data = {
                'source': extracted['site_key'],
                'data': company,
                'timestamp': extracted['extraction_timestamp']
            }
            consolidated['companies'][symbol]['data_sources'].append(source_data)
        
        # Merge news items
        consolidated['news_items'].extend(extracted.get('news_items', []))
        
        # Merge market data
        if extracted.get('market_data'):
            consolidated['market_metrics'][extracted['site_key']] = extracted['market_data']
        
        # Merge heat map data
        if extracted.get('heat_map_data'):
            consolidated['heat_map_data'] = extracted['heat_map_data']
    
    def _generate_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        
        successful_sites = sum(1 for site in results['site_results'].values() 
                             if site['scrape_result']['success'])
        
        total_companies = len(results['consolidated_data']['companies'])
        total_news = len(results['consolidated_data']['news_items'])
        
        # Calculate total scraping time
        scraping_duration = None
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            scraping_duration = (end - start).total_seconds()
        
        summary = {
            'sites_attempted': len(self.target_urls),
            'sites_successful': successful_sites,
            'success_rate': (successful_sites / len(self.target_urls)) * 100,
            'total_companies_found': total_companies,
            'total_news_items': total_news,
            'total_errors': len(results['errors']),
            'scraping_duration_seconds': scraping_duration,
            'average_site_duration': None,
            'data_quality_score': None
        }
        
        # Calculate average site duration
        site_durations = [site['scrape_result']['duration'] 
                         for site in results['site_results'].values() 
                         if site['scrape_result']['success']]
        
        if site_durations:
            summary['average_site_duration'] = sum(site_durations) / len(site_durations)
        
        # Calculate data quality score (0-100)
        quality_score = 0
        if successful_sites > 0:
            quality_score += (successful_sites / len(self.target_urls)) * 40  # 40% for successful scrapes
        if total_companies > 0:
            quality_score += min(total_companies / 20, 1) * 30  # 30% for company data (cap at 20 companies)
        if total_news > 0:
            quality_score += min(total_news / 10, 1) * 20  # 20% for news items (cap at 10 items)
        if len(results['errors']) == 0:
            quality_score += 10  # 10% bonus for no errors
        
        summary['data_quality_score'] = round(quality_score, 1)
        
        return summary
    
    async def _save_mining_data(self, results: Dict[str, Any]):
        """Save mining companies data to specified location"""
        
        # Main results file
        output_file = self.data_dir / "mining_companies_data.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Mining companies data saved to: {output_file}")
        
        # Create summary file
        summary_file = self.data_dir / "mining_companies_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("JUNIOR MINING NETWORK SCRAPING REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Session: {results['scraping_started']} to {results['scraping_completed']}\n")
            f.write(f"Target Sites: {len(self.target_urls)}\n")
            f.write(f"Successful Scrapes: {results['performance_summary']['sites_successful']}\n")
            f.write(f"Success Rate: {results['performance_summary']['success_rate']:.1f}%\n\n")
            
            f.write(f"RESULTS SUMMARY:\n")
            f.write(f"- Companies Found: {results['performance_summary']['total_companies_found']}\n")
            f.write(f"- News Items: {results['performance_summary']['total_news_items']}\n")
            f.write(f"- Data Quality Score: {results['performance_summary']['data_quality_score']}/100\n\n")
            
            if results['consolidated_data']['companies']:
                f.write("TOP COMPANIES FOUND:\n")
                for i, (symbol, company) in enumerate(list(results['consolidated_data']['companies'].items())[:10]):
                    f.write(f"{i+1}. {company['name']} ({symbol})\n")
                f.write("\n")
            
            if results['consolidated_data']['news_items']:
                f.write("RECENT NEWS HEADLINES:\n")
                for i, news in enumerate(results['consolidated_data']['news_items'][:5]):
                    f.write(f"{i+1}. {news['headline']}\n")
                f.write("\n")
            
            if results['errors']:
                f.write("ERRORS ENCOUNTERED:\n")
                for error in results['errors']:
                    f.write(f"- {error}\n")
        
        print(f"📄 Summary report saved to: {summary_file}")
    
    async def _save_performance_log(self):
        """Save performance log for monitoring"""
        
        log_file = Path("logs/scraper_performance") / f"junior_mining_network_session_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.performance_log, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📊 Performance log saved to: {log_file}")
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        await self.unified_scraper.cleanup()


# Convenience function for easy execution
async def scrape_junior_mining_network() -> Dict[str, Any]:
    """Convenience function to scrape Junior Mining Network sites"""
    scraper = JuniorMiningNetworkScraper()
    try:
        return await scraper.scrape_all_junior_mining_sites()
    finally:
        await scraper.cleanup()


# Main execution
if __name__ == "__main__":
    async def main():
        print("🏗️ Junior Mining Network Intelligence Scraper")
        print("Target Sites:")
        print("1. https://www.juniorminingnetwork.com/")
        print("2. https://www.juniorminingnetwork.com/heat-map.html")
        print("3. https://www.juniorminingnetwork.com/market-data.html")
        print("=" * 70)
        
        scraper = JuniorMiningNetworkScraper()
        
        try:
            results = await scraper.scrape_all_junior_mining_sites()
            
            print(f"\n🎯 SCRAPING COMPLETE")
            print(f"✅ Sites Successful: {results['performance_summary']['sites_successful']}/{results['performance_summary']['sites_attempted']}")
            print(f"📊 Companies Found: {results['performance_summary']['total_companies_found']}")
            print(f"📰 News Items: {results['performance_summary']['total_news_items']}")
            print(f"🏆 Data Quality Score: {results['performance_summary']['data_quality_score']}/100")
            print(f"⏱️ Total Duration: {results['performance_summary']['scraping_duration_seconds']:.1f}s")
            
        finally:
            await scraper.cleanup()
    
    asyncio.run(main())