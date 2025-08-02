#!/usr/bin/env python3
"""
TSX Mining Company Collector
Collects all TSX/TSXV listed mining companies and their websites
"""

import asyncio
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
import yfinance as yf
from crawl4ai import AsyncWebCrawler
import time
import re

class TSXMiningCollector:
    def __init__(self):
        self.db_path = "mining_companies.db"
        self.companies = []
        self.mining_sectors = [
            'Basic Materials', 'Metals & Mining', 'Gold', 'Silver', 'Copper',
            'Mining', 'Precious Metals', 'Industrial Metals', 'Coal',
            'Materials', 'Energy', 'Oil & Gas', 'Uranium'
        ]
        
    def setup_database(self):
        """Create database tables for storing company information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                exchange TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                website TEXT,
                investor_relations_url TEXT,
                news_url TEXT,
                description TEXT,
                country TEXT,
                currency TEXT,
                employees INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # News/updates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                title TEXT,
                content TEXT,
                url TEXT,
                published_date TEXT,
                scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_type TEXT,
                relevance_score INTEGER,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # LinkedIn posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS linkedin_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                post_content TEXT,
                post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                engagement_score INTEGER DEFAULT 0,
                source_news_ids TEXT,
                posted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database setup completed")

    async def get_tsx_companies_from_api(self):
        """Get TSX/TSXV companies from various sources"""
        companies = []
        
        # Known Canadian mining companies (starter list)
        known_mining_companies = [
            'ABX.TO', 'NEM.TO', 'K.TO', 'AEM.TO', 'FNV.TO', 'FM.TO', 'LUN.TO',
            'HBM.TO', 'ELD.TO', 'CG.TO', 'IMG.TO', 'KL.TO', 'OSK.TO', 'AUY.TO',
            'TECK.TO', 'SU.TO', 'CNQ.TO', 'IMO.TO', 'CVE.TO', 'TOU.TO',
            'B2G.TO', 'TXG.TO', 'SEA.TO', 'PVG.TO', 'AGI.TO', 'CXB.TO',
            'NFLD.TO', 'MAG.TO', 'PMET.TO', 'FORT.TO', 'NGD.TO', 'AR.TO'
        ]
        
        # Add TSXV symbols
        tsxv_symbols = [
            'NFLD.V', 'MAG.V', 'PMET.V', 'FORT.V', 'NGD.V', 'AR.V',
            'AMK.V', 'TUD.V', 'DIAM.V', 'SBB.V', 'STGO.V', 'VGCX.V'
        ]
        
        all_symbols = known_mining_companies + tsxv_symbols
        
        print(f"Collecting data for {len(all_symbols)} known mining companies...")
        
        for symbol in all_symbols:
            try:
                print(f"Getting data for {symbol}...")
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info and 'shortName' in info:
                    company_data = {
                        'symbol': symbol,
                        'name': info.get('shortName', ''),
                        'exchange': 'TSX' if '.TO' in symbol else 'TSXV',
                        'sector': info.get('sector', ''),
                        'industry': info.get('industry', ''),
                        'market_cap': info.get('marketCap', 0),
                        'website': info.get('website', ''),
                        'description': info.get('longBusinessSummary', ''),
                        'country': info.get('country', 'Canada'),
                        'currency': info.get('currency', 'CAD'),
                        'employees': info.get('fullTimeEmployees', 0)
                    }
                    
                    # Check if it's mining related
                    if self.is_mining_company(company_data):
                        companies.append(company_data)
                        print(f"Added: {company_data['name']} ({symbol})")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error getting data for {symbol}: {str(e)}")
                continue
        
        return companies

    async def scrape_tsx_directory(self):
        """Scrape TSX website for comprehensive company list"""
        print("Scraping TSX directory for additional companies...")
        
        additional_companies = []
        
        async with AsyncWebCrawler(headless=True) as crawler:
            try:
                # TSX listed companies page
                tsx_url = "https://www.tsx.com/listings/listing-with-us/listed-company-directory"
                result = await crawler.arun(url=tsx_url, word_count_threshold=10)
                
                # Extract company listings from the page
                content = result.markdown.lower()
                
                # Look for mining-related companies in the content
                mining_patterns = [
                    r'([A-Z]{1,5}\.TO).*(?:mining|gold|silver|copper|nickel|uranium|coal|oil|gas)',
                    r'([A-Z]{1,5}\.V).*(?:mining|gold|silver|copper|nickel|uranium|coal|oil|gas)'
                ]
                
                for pattern in mining_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for symbol in matches:
                        if symbol not in [c['symbol'] for c in self.companies]:
                            additional_companies.append({'symbol': symbol, 'source': 'tsx_directory'})
                
            except Exception as e:
                print(f"Error scraping TSX directory: {str(e)}")
        
        return additional_companies

    def is_mining_company(self, company_data):
        """Determine if a company is mining-related"""
        text_to_check = (
            f"{company_data.get('name', '')} "
            f"{company_data.get('sector', '')} "
            f"{company_data.get('industry', '')} "
            f"{company_data.get('description', '')}"
        ).lower()
        
        mining_keywords = [
            'mining', 'mine', 'gold', 'silver', 'copper', 'nickel', 'zinc',
            'platinum', 'palladium', 'uranium', 'coal', 'iron ore', 'lithium',
            'rare earth', 'precious metals', 'base metals', 'exploration',
            'drilling', 'ore', 'mineral', 'extraction', 'smelting', 'refining',
            'oil', 'gas', 'petroleum', 'energy', 'resources'
        ]
        
        return any(keyword in text_to_check for keyword in mining_keywords)

    async def find_company_websites(self, companies):
        """Find and validate company websites and IR pages"""
        print("Finding company websites and investor relations pages...")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for company in companies:
                try:
                    if not company.get('website'):
                        # Search for company website
                        search_query = f"{company['name']} investor relations site:tsx.com OR site:sedar.com"
                        # This would typically use a search API
                        continue
                    
                    website = company['website']
                    if website:
                        # Find investor relations page
                        ir_urls = await self.find_investor_relations_page(crawler, website)
                        company['investor_relations_url'] = ir_urls.get('ir_page', '')
                        company['news_url'] = ir_urls.get('news_page', '')
                        
                        print(f"Found IR page for {company['name']}: {company['investor_relations_url']}")
                    
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error finding website for {company['name']}: {str(e)}")
                    continue
        
        return companies

    async def find_investor_relations_page(self, crawler, website):
        """Find investor relations and news pages on company website"""
        ir_urls = {'ir_page': '', 'news_page': ''}
        
        try:
            result = await crawler.arun(url=website, word_count_threshold=5)
            
            links = getattr(result, 'links', {})
            if isinstance(links, dict):
                all_links = links.get('internal', []) + links.get('external', [])
            else:
                all_links = []
            
            for link in all_links:
                href = link.get('href', '').lower()
                text = link.get('text', '').lower()
                
                # Look for investor relations page
                if any(term in href or term in text for term in ['investor', 'ir', 'shareholder']):
                    if not ir_urls['ir_page']:
                        ir_urls['ir_page'] = href if href.startswith('http') else f"{website.rstrip('/')}{href}"
                
                # Look for news page
                if any(term in href or term in text for term in ['news', 'press', 'release', 'announcement']):
                    if not ir_urls['news_page']:
                        ir_urls['news_page'] = href if href.startswith('http') else f"{website.rstrip('/')}{href}"
        
        except Exception as e:
            print(f"Error finding IR pages for {website}: {str(e)}")
        
        return ir_urls

    def save_companies_to_db(self, companies):
        """Save companies to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for company in companies:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO companies 
                    (symbol, name, exchange, sector, industry, market_cap, website, 
                     investor_relations_url, news_url, description, country, currency, employees)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company['symbol'],
                    company['name'],
                    company['exchange'],
                    company.get('sector', ''),
                    company.get('industry', ''),
                    company.get('market_cap', 0),
                    company.get('website', ''),
                    company.get('investor_relations_url', ''),
                    company.get('news_url', ''),
                    company.get('description', ''),
                    company.get('country', 'Canada'),
                    company.get('currency', 'CAD'),
                    company.get('employees', 0)
                ))
            except Exception as e:
                print(f"Error saving {company.get('symbol', 'unknown')}: {str(e)}")
        
        conn.commit()
        conn.close()
        print(f"Saved {len(companies)} companies to database")

    def generate_company_report(self):
        """Generate report of collected companies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM companies')
        total_companies = cursor.fetchone()[0]
        
        cursor.execute('SELECT exchange, COUNT(*) FROM companies GROUP BY exchange')
        exchange_counts = cursor.fetchall()
        
        cursor.execute('SELECT sector, COUNT(*) FROM companies GROUP BY sector ORDER BY COUNT(*) DESC')
        sector_counts = cursor.fetchall()
        
        cursor.execute('SELECT symbol, name, market_cap FROM companies WHERE market_cap > 0 ORDER BY market_cap DESC LIMIT 10')
        top_companies = cursor.fetchall()
        
        conn.close()
        
        report = []
        report.append("TSX MINING COMPANIES COLLECTION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total companies collected: {total_companies}")
        report.append("")
        
        report.append("BY EXCHANGE:")
        for exchange, count in exchange_counts:
            report.append(f"• {exchange}: {count} companies")
        report.append("")
        
        report.append("BY SECTOR (Top 10):")
        for sector, count in sector_counts[:10]:
            report.append(f"• {sector or 'Unknown'}: {count} companies")
        report.append("")
        
        report.append("TOP COMPANIES BY MARKET CAP:")
        for symbol, name, market_cap in top_companies:
            if market_cap:
                market_cap_b = market_cap / 1e9
                report.append(f"• {symbol}: {name} (${market_cap_b:.1f}B)")
        
        return "\n".join(report)

async def main():
    """Main execution function"""
    collector = TSXMiningCollector()
    
    print("TSX Mining Company Collector")
    print("=" * 40)
    
    # Setup database
    collector.setup_database()
    
    try:
        # Get companies from APIs
        companies = await collector.get_tsx_companies_from_api()
        print(f"Found {len(companies)} companies from API")
        
        # Scrape additional companies from TSX directory
        additional = await collector.scrape_tsx_directory()
        print(f"Found {len(additional)} additional companies from directory")
        
        # Find websites and IR pages
        companies = await collector.find_company_websites(companies)
        
        # Save to database
        collector.save_companies_to_db(companies)
        
        # Generate report
        report = collector.generate_company_report()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tsx_mining_companies_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print("\n" + report)
        print(f"\nReport saved to: {report_file}")
        print(f"Database created: {collector.db_path}")
        
        return True
        
    except Exception as e:
        print(f"Error during collection: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\nTSX mining company collection completed successfully!")
    else:
        print("\nCollection failed. Check error messages above.")