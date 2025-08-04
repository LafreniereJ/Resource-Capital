#!/usr/bin/env python3
"""
Mining Companies Scraper
Specialized scraper for company-specific data and corporate information

Focuses on:
- TSX/TSXV listed mining companies
- Company financial statements and reports
- Production data and reserves information
- Management changes and corporate announcements
- SEC/SEDAR filings
- Investor relations updates
- Stock performance metrics
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


class MiningCompaniesScraper:
    """Specialized scraper for mining company data"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data/companies")
        self.intelligence = ScraperIntelligence()
        self.unified_scraper = UnifiedScraper(intelligence=self.intelligence)
        
        # Ensure data directories exist
        self._setup_data_directories()
        
        # Company data sources configuration
        self.company_sources = {
            "tsx_company_profiles": {
                "base_url": "https://www.tsx.com",
                "endpoints": {
                    "company_directory": "/listings/listing-with-us/company-directory",
                    "company_profile": "/en/listings/current-listed-companies",
                },
                "selectors": {
                    "company_name": [".company-name", ".listing-name", "h1"],
                    "ticker": [".ticker", ".symbol", ".stock-symbol"],
                    "sector": [".sector", ".industry", ".classification"],
                    "market_cap": [".market-cap", ".capitalization"],
                    "listing_date": [".listing-date", ".ipo-date"]
                }
            },
            "yahoo_finance": {
                "base_url": "https://finance.yahoo.com",
                "profile_template": "/quote/{ticker}.TO",  # Canadian companies
                "us_template": "/quote/{ticker}",
                "selectors": {
                    "price": ["[data-field='regularMarketPrice']", ".Fw\\(b\\).Fz\\(36px\\)"],
                    "change": ["[data-field='regularMarketChange']"],
                    "volume": ["[data-field='regularMarketVolume']"],
                    "market_cap": ["[data-testid='MARKET_CAP-value']"],
                    "pe_ratio": ["[data-testid='PE_RATIO-value']"],
                    "dividend_yield": ["[data-testid='DIVIDEND_AND_YIELD-value']"],
                    "52_week_range": ["[data-testid='FIFTY_TWO_WK_RANGE-value']"]
                }
            },
            "sedar_filings": {
                "base_url": "https://www.sedar.com",
                "endpoints": {
                    "search": "/search/search_form_pc.htm",
                    "company_filings": "/FindCompanyDocuments.do"
                },
                "selectors": {
                    "filing_date": [".filing-date", ".date"],
                    "filing_type": [".filing-type", ".document-type"],
                    "document_link": [".document-link", "a[href*='.pdf']"]
                }
            },
            "sec_edgar": {
                "base_url": "https://www.sec.gov",
                "endpoints": {
                    "company_search": "/edgar/searchedgar/companysearch.html",
                    "company_filings": "/cgi-bin/browse-edgar"
                },
                "selectors": {
                    "filing_date": [".filing-date"],
                    "form_type": [".form-type"],
                    "document_link": ["a[href*='Archives']"]
                }
            },
            "company_websites": {
                # Will be populated dynamically based on company data
                "common_paths": {
                    "investor_relations": ["/investors", "/investor-relations", "/ir"],
                    "news": ["/news", "/press-releases", "/media"],
                    "operations": ["/operations", "/projects", "/properties"],
                    "financials": ["/financials", "/reports", "/annual-reports"]
                },
                "selectors": {
                    "press_release": [".press-release", ".news-item", ".announcement"],
                    "financial_data": [".financial-table", ".earnings", ".revenue"],
                    "production_data": [".production", ".output", ".reserves"],
                    "project_update": [".project-update", ".development", ".exploration"]
                }
            }
        }
        
        # Key company data points we track
        self.tracked_metrics = {
            "financial": [
                "revenue", "net_income", "cash_flow", "debt", "working_capital",
                "market_cap", "enterprise_value", "pe_ratio", "book_value"
            ],
            "operational": [
                "production_volume", "reserves", "resources", "grade",
                "all_in_sustaining_cost", "cash_cost", "recovery_rate"
            ],
            "corporate": [
                "management_changes", "board_appointments", "merger_acquisition",
                "partnership", "joint_venture", "financing", "dividend"
            ],
            "projects": [
                "exploration_results", "feasibility_study", "environmental_approval",
                "construction_update", "commissioning", "expansion"
            ]
        }
        
        # Load company universe (TSX/TSXV mining companies)
        self.company_universe = self._load_company_universe()
    
    def _setup_data_directories(self):
        """Create necessary data directories"""
        base_dirs = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "historical"
        ]
        
        for directory in base_dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_company_universe(self) -> List[Dict[str, Any]]:
        """Load known mining companies from existing data"""
        
        companies = []
        
        # Try to load from existing company database
        company_files = [
            "data/raw/mining-companies-listed-on-tsx-and-tsxv-2025-07-18-en.xlsx",
            "data/processed/enhanced_canadian_mining_companies.xlsx",
            "data/processed/canadian_mining_companies_filtered.xlsx"
        ]
        
        for file_path in company_files:
            try:
                if Path(file_path).exists():
                    df = pd.read_excel(file_path)
                    for _, row in df.iterrows():
                        company = {
                            'name': row.get('Company Name', row.get('Name', '')),
                            'ticker': row.get('Symbol', row.get('Ticker', '')),
                            'exchange': row.get('Exchange', 'TSX'),
                            'sector': row.get('Sector', row.get('Industry', 'Mining')),
                            'market_cap': row.get('Market Cap', None)
                        }
                        if company['name'] and company['ticker']:
                            companies.append(company)
                    break  # Use first available file
            except Exception as e:
                print(f"Could not load company data from {file_path}: {str(e)}")
                continue
        
        # If no files found, add some major mining companies as defaults
        if not companies:
            companies = [
                {'name': 'Barrick Gold Corporation', 'ticker': 'ABX', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'Newmont Corporation', 'ticker': 'NGT', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'Agnico Eagle Mines Limited', 'ticker': 'AEM', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'Franco-Nevada Corporation', 'ticker': 'FNV', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'Canadian National Railway Company', 'ticker': 'CNR', 'exchange': 'TSX', 'sector': 'Transportation'},
                {'name': 'Teck Resources Limited', 'ticker': 'TECK.B', 'exchange': 'TSX', 'sector': 'Diversified Mining'},
                {'name': 'First Quantum Minerals Ltd.', 'ticker': 'FM', 'exchange': 'TSX', 'sector': 'Copper'},
                {'name': 'Kinross Gold Corporation', 'ticker': 'K', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'B2Gold Corp.', 'ticker': 'BTO', 'exchange': 'TSX', 'sector': 'Gold'},
                {'name': 'Yamana Gold Inc.', 'ticker': 'YRI', 'exchange': 'TSX', 'sector': 'Gold'}
            ]
        
        print(f"📊 Loaded {len(companies)} companies for tracking")
        return companies[:20]  # Limit to first 20 for testing
    
    async def scrape_all_companies_data(self) -> Dict[str, Any]:
        """Scrape data for all companies in our universe"""
        
        print("🏢 Starting comprehensive mining companies data scraping...")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'companies_data': {},
            'market_overview': {},
            'sector_analysis': {},
            'errors': [],
            'summary': {}
        }
        
        # Scrape individual company data
        for company in self.company_universe:
            try:
                print(f"🏗️ Scraping data for {company['name']} ({company['ticker']})...")
                company_data = await self._scrape_company_data(company)
                results['companies_data'][company['ticker']] = company_data
                
                # Rate limiting between companies
                await asyncio.sleep(3)
                
            except Exception as e:
                error_msg = f"Error scraping {company['name']}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
        
        # Scrape sector overview
        try:
            print("📊 Scraping mining sector overview...")
            sector_data = await self._scrape_sector_overview()
            results['sector_analysis'] = sector_data
            
        except Exception as e:
            error_msg = f"Error scraping sector overview: {str(e)}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        # Generate summary
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_companies_summary(results)
        
        # Save results
        await self._save_companies_data(results)
        
        return results
    
    async def _scrape_company_data(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape comprehensive data for a specific company"""
        
        company_data = {
            'company_info': company,
            'scraped_at': datetime.now().isoformat(),
            'stock_data': {},
            'financial_data': {},
            'operational_data': {},
            'news_updates': {},
            'filings': {}
        }
        
        ticker = company['ticker']
        
        # Create company-specific directory
        company_dir = self.data_dir / ticker
        company_dir.mkdir(exist_ok=True)
        (company_dir / datetime.now().strftime("%Y-%m")).mkdir(exist_ok=True)
        
        # Scrape stock data from Yahoo Finance
        try:
            stock_data = await self._scrape_stock_data(ticker)
            company_data['stock_data'] = stock_data
        except Exception as e:
            print(f"  ❌ Failed to scrape stock data: {str(e)}")
        
        # Try to find and scrape company website
        try:
            website_data = await self._scrape_company_website(company)
            company_data['website_data'] = website_data
        except Exception as e:
            print(f"  ❌ Failed to scrape company website: {str(e)}")
        
        # Scrape recent filings (if available)
        try:
            filings_data = await self._scrape_company_filings(company)
            company_data['filings'] = filings_data
        except Exception as e:
            print(f"  ❌ Failed to scrape filings: {str(e)}")
        
        return company_data
    
    async def _scrape_stock_data(self, ticker: str) -> Dict[str, Any]:
        """Scrape stock market data for a company"""
        
        # Try Canadian ticker first (.TO), then US if needed
        urls_to_try = [
            f"https://finance.yahoo.com/quote/{ticker}.TO",
            f"https://finance.yahoo.com/quote/{ticker}"
        ]
        
        for url in urls_to_try:
            try:
                strategy = ScrapingStrategy()
                strategy.primary = 'playwright'  # Yahoo Finance is JS-heavy
                strategy.fallbacks = ['crawl4ai']
                
                result = await self.unified_scraper.scrape(url=url, strategy=strategy)
                
                if result.success:
                    stock_data = self._extract_stock_metrics(result.content, ticker)
                    stock_data['url'] = url
                    stock_data['scraped_at'] = result.timestamp.isoformat()
                    stock_data['scraper_used'] = result.scraper_used
                    return stock_data
                
            except Exception as e:
                print(f"    Failed to scrape {url}: {str(e)}")
                continue
        
        return {'error': 'Could not scrape stock data from any source'}
    
    async def _scrape_company_website(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to scrape company's official website"""
        
        # Try to construct likely website URLs
        company_name = company['name'].lower()
        possible_domains = []
        
        # Extract key words from company name
        name_words = re.findall(r'\b\w+\b', company_name)
        name_words = [word for word in name_words if word not in ['corporation', 'corp', 'limited', 'ltd', 'inc', 'company', 'co']]
        
        if name_words:
            main_word = name_words[0]
            possible_domains = [
                f"https://www.{main_word}.com",
                f"https://www.{main_word}mining.com",
                f"https://www.{main_word}gold.com" if 'gold' in company_name else f"https://www.{main_word}.com",
                f"https://{main_word}.com"
            ]
        
        website_data = {
            'domains_tried': possible_domains,
            'successful_scrapes': {},
            'failed_attempts': []
        }
        
        for domain in possible_domains[:2]:  # Limit attempts
            try:
                strategy = ScrapingStrategy()
                strategy.primary = 'crawl4ai'
                strategy.fallbacks = ['requests', 'playwright']
                
                result = await self.unified_scraper.scrape(url=domain, strategy=strategy)
                
                if result.success and result.word_count > 100:
                    # Extract relevant company information
                    extracted_info = self._extract_company_info(result.content, company)
                    website_data['successful_scrapes'][domain] = {
                        'content_length': len(result.content),
                        'word_count': result.word_count,
                        'title': result.title,
                        'extracted_info': extracted_info,
                        'scraped_at': result.timestamp.isoformat()
                    }
                    break  # Stop after first successful scrape
                    
            except Exception as e:
                website_data['failed_attempts'].append({
                    'domain': domain,
                    'error': str(e)
                })
                continue
        
        return website_data
    
    async def _scrape_company_filings(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape recent regulatory filings for the company"""
        
        filings_data = {
            'sedar_filings': {},
            'sec_filings': {},
            'search_attempts': []
        }
        
        # For Canadian companies, try SEDAR
        if company.get('exchange') in ['TSX', 'TSXV']:
            try:
                # SEDAR search is complex and often requires specific company codes
                # For now, we'll note the attempt and implement specific logic later
                filings_data['search_attempts'].append({
                    'system': 'SEDAR',
                    'status': 'attempted',
                    'note': 'SEDAR search requires company-specific implementation'
                })
            except Exception as e:
                filings_data['search_attempts'].append({
                    'system': 'SEDAR',
                    'status': 'failed',
                    'error': str(e)
                })
        
        return filings_data
    
    async def _scrape_sector_overview(self) -> Dict[str, Any]:
        """Scrape general mining sector overview data"""
        
        sector_data = {
            'scraped_at': datetime.now().isoformat(),
            'tsx_mining_stats': {},
            'sector_performance': {},
            'market_trends': {}
        }
        
        # Scrape TSX mining sector overview
        try:
            tsx_url = "https://www.tsx.com/listings/listing-with-us/sector-and-product-profiles/mining"
            
            strategy = ScrapingStrategy()
            strategy.primary = 'playwright'
            strategy.fallbacks = ['crawl4ai', 'requests']
            
            result = await self.unified_scraper.scrape(url=tsx_url, strategy=strategy)
            
            if result.success:
                sector_stats = self._extract_sector_statistics(result.content)
                sector_data['tsx_mining_stats'] = {
                    'url': tsx_url,
                    'scraped_at': result.timestamp.isoformat(),
                    'statistics': sector_stats
                }
        
        except Exception as e:
            print(f"Failed to scrape TSX sector data: {str(e)}")
        
        return sector_data
    
    def _extract_stock_metrics(self, content: str, ticker: str) -> Dict[str, Any]:
        """Extract stock metrics from Yahoo Finance content"""
        
        metrics = {
            'ticker': ticker,
            'price': None,
            'change': None,
            'change_percent': None,
            'volume': None,
            'market_cap': None,
            'pe_ratio': None,
            '52_week_range': None
        }
        
        # Define extraction patterns
        patterns = {
            'price': [
                r'regularMarketPrice.*?(\d+\.\d{2})',
                r'"price":(\d+\.\d{2})',
                r'(\d+\.\d{2})\s*USD'
            ],
            'change': [
                r'regularMarketChange.*?([+-]?\d+\.\d{2})',
                r'"change":([+-]?\d+\.\d{2})'
            ],
            'volume': [
                r'regularMarketVolume.*?(\d+(?:,\d{3})*)',
                r'"volume":(\d+)'
            ],
            'market_cap': [
                r'marketCap.*?(\d+\.?\d*[BMK]?)',
                r'Market Cap.*?(\d+\.?\d*[BMK]?)'
            ]
        }
        
        for metric, metric_patterns in patterns.items():
            for pattern in metric_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        value = match.group(1).replace(',', '')
                        if metric in ['price', 'change']:
                            metrics[metric] = float(value)
                        elif metric == 'volume':
                            metrics[metric] = int(value)
                        else:
                            metrics[metric] = value
                        break
                    except (ValueError, IndexError):
                        continue
        
        return metrics
    
    def _extract_company_info(self, content: str, company: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant company information from website content"""
        
        info = {
            'company_description': None,
            'operations': [],
            'recent_news': [],
            'financial_highlights': {},
            'contact_info': {}
        }
        
        # Look for company description
        desc_patterns = [
            r'(?:about|company|who we are|overview).*?([^.]{100,500}\.[^.]*\.)',
            r'<meta name="description" content="([^"]+)"'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                info['company_description'] = match.group(1).strip()
                break
        
        # Look for operations/projects
        operations_keywords = ['mine', 'project', 'operation', 'facility', 'property', 'deposit']
        for keyword in operations_keywords:
            pattern = rf'{keyword}[^.]*?([A-Z][^.]*{keyword}[^.]*\.)'
            matches = re.findall(pattern, content, re.IGNORECASE)
            info['operations'].extend(matches[:3])  # Limit to 3 per keyword
        
        # Look for financial figures
        financial_patterns = {
            'revenue': r'revenue.*?\$?(\d+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?)',
            'production': r'production.*?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:ounces|tonnes|tons|oz)',
            'reserves': r'reserves.*?(\d+(?:\.\d+)?(?:\s*(?:million|billion|M|B))?)\s*(?:ounces|tonnes|tons|oz)'
        }
        
        for metric, pattern in financial_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                info['financial_highlights'][metric] = matches[0]
        
        return info
    
    def _extract_sector_statistics(self, content: str) -> Dict[str, Any]:
        """Extract mining sector statistics from TSX content"""
        
        stats = {
            'total_mining_companies': None,
            'market_cap_total': None,
            'recent_listings': [],
            'top_companies': []
        }
        
        # Look for sector statistics
        stats_patterns = {
            'total_companies': r'(\d+)\s*(?:mining|companies|issuers)',
            'market_cap': r'market cap.*?\$?(\d+(?:\.\d+)?(?:\s*(?:billion|trillion|B|T))?)'
        }
        
        for stat, pattern in stats_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                stats[stat] = match.group(1)
        
        return stats
    
    def _generate_companies_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for scraped companies data"""
        
        summary = {
            'total_companies_attempted': len(self.company_universe),
            'successful_company_scrapes': 0,
            'companies_with_stock_data': 0,
            'companies_with_website_data': 0,
            'total_errors': len(results['errors']),
            'scraping_duration': None
        }
        
        # Count successful scrapes
        companies_data = results.get('companies_data', {})
        for ticker, company_data in companies_data.items():
            summary['successful_company_scrapes'] += 1
            
            if company_data.get('stock_data', {}).get('price'):
                summary['companies_with_stock_data'] += 1
            
            if company_data.get('website_data', {}).get('successful_scrapes'):
                summary['companies_with_website_data'] += 1
        
        # Calculate scraping duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_duration'] = (end - start).total_seconds()
        
        return summary
    
    async def _save_companies_data(self, results: Dict[str, Any]):
        """Save scraped companies data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive results
        raw_file = self.data_dir / "raw" / f"companies_data_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save individual company files
        for ticker, company_data in results.get('companies_data', {}).items():
            company_dir = self.data_dir / ticker
            monthly_dir = company_dir / datetime.now().strftime("%Y-%m")
            
            company_file = monthly_dir / f"{ticker}_{timestamp}.json"
            with open(company_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Companies data saved to:")
        print(f"   Comprehensive: {raw_file}")
        print(f"   Individual companies: data/companies/[TICKER]/")
    
    async def get_company_history(self, ticker: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical data for a specific company"""
        
        company_dir = self.data_dir / ticker
        if not company_dir.exists():
            return []
        
        history = []
        
        # Look through historical files
        for days_back in range(days):
            date = datetime.now() - timedelta(days=days_back)
            date_str = date.strftime("%Y-%m")
            monthly_dir = company_dir / date_str
            
            if monthly_dir.exists():
                for file_path in monthly_dir.glob(f"{ticker}_*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        stock_data = data.get('stock_data', {})
                        if stock_data.get('price'):
                            history.append({
                                'date': data.get('scraped_at'),
                                'price': stock_data['price'],
                                'change': stock_data.get('change'),
                                'volume': stock_data.get('volume'),
                                'market_cap': stock_data.get('market_cap')
                            })
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return sorted(history, key=lambda x: x['date'])
    
    async def cleanup(self):
        """Cleanup scraper resources"""
        await self.unified_scraper.cleanup()


# Convenience functions
async def scrape_all_mining_companies() -> Dict[str, Any]:
    """Convenience function to scrape all mining companies data"""
    scraper = MiningCompaniesScraper()
    try:
        return await scraper.scrape_all_companies_data()
    finally:
        await scraper.cleanup()


async def get_company_historical_data(ticker: str, days: int = 30) -> List[Dict[str, Any]]:
    """Convenience function to get historical data for a company"""
    scraper = MiningCompaniesScraper()
    try:
        return await scraper.get_company_history(ticker, days)
    finally:
        await scraper.cleanup()


# Example usage
if __name__ == "__main__":
    async def main():
        print("🏢 Mining Companies Scraper - Corporate Intelligence")
        print("=" * 60)
        
        scraper = MiningCompaniesScraper()
        
        try:
            # Test comprehensive companies scraping
            print("\n🚀 Testing comprehensive companies data scraping...")
            results = await scraper.scrape_all_companies_data()
            
            print(f"\n📊 COMPANIES DATA SUMMARY:")
            print(f"   Companies Attempted: {results['summary']['total_companies_attempted']}")
            print(f"   Successful Scrapes: {results['summary']['successful_company_scrapes']}")
            print(f"   Companies with Stock Data: {results['summary']['companies_with_stock_data']}")
            print(f"   Companies with Website Data: {results['summary']['companies_with_website_data']}")
            print(f"   Total Errors: {results['summary']['total_errors']}")
            print(f"   Scraping Duration: {results['summary']['scraping_duration']:.1f}s")
            
            # Show sample company data
            if results['companies_data']:
                print(f"\n🏗️ SAMPLE COMPANY DATA:")
                for ticker, company_data in list(results['companies_data'].items())[:3]:
                    company_name = company_data.get('company_info', {}).get('name', ticker)
                    stock_price = company_data.get('stock_data', {}).get('price', 'N/A')
                    print(f"   {company_name} ({ticker}): ${stock_price}")
            
        finally:
            await scraper.cleanup()
    
    asyncio.run(main())