#!/usr/bin/env python3
"""
Northern Miner News Scraper
Scrapes Canadian mining industry news and updates from northernminer.com
"""

import asyncio
import json
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler

class NorthernMinerScraper:
    def __init__(self):
        self.base_url = "https://www.northernminer.com"
        self.data = {}
        
    async def scrape_page(self, crawler, url, page_name):
        """Scrape a specific page"""
        print(f"Scraping {page_name}: {url}")
        
        try:
            result = await crawler.arun(
                url=url,
                word_count_threshold=10
            )
            
            return {
                'url': url,
                'title': getattr(result, 'title', ''),
                'content': result.markdown,
                'links': getattr(result, 'links', {}),
                'images': getattr(result, 'images', []),
                'metadata': getattr(result, 'metadata', {})
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    async def discover_canadian_mining_content(self, crawler):
        """Discover and scrape Canadian mining content"""
        print("Discovering Northern Miner content...")
        
        # Key pages to scrape
        important_pages = {
            'home': self.base_url,
            'news': f"{self.base_url}/news/",
            'companies': f"{self.base_url}/companies/",
            'markets': f"{self.base_url}/markets/",
            'mining': f"{self.base_url}/mining/",
            'exploration': f"{self.base_url}/exploration/",
            'junior_mining': f"{self.base_url}/junior-mining/"
        }
        
        # Get main page to find more links
        try:
            main_result = await crawler.arun(
                url=self.base_url,
                word_count_threshold=5
            )
            
            # Extract article links from main page
            links = getattr(main_result, 'links', {})
            if isinstance(links, dict):
                all_links = links.get('internal', []) + links.get('external', [])
            else:
                all_links = []
            
            # Look for Canadian mining company mentions and recent news
            canadian_indicators = [
                'canada', 'canadian', 'toronto', 'vancouver', 'tsx', 'tsxv',
                'ontario', 'quebec', 'british columbia', 'alberta', 'manitoba',
                'saskatchewan', 'newfoundland', 'northwest territories', 'yukon'
            ]
            
            article_count = 0
            for link in all_links:
                if article_count >= 20:  # Limit to prevent too many requests
                    break
                    
                href = link.get('href', '').lower()
                text = link.get('text', '').lower()
                
                # Check if link contains Canadian mining content
                if any(indicator in href or indicator in text for indicator in canadian_indicators):
                    if '/news/' in href or '/companies/' in href or '/markets/' in href:
                        full_url = href if href.startswith('http') else f"{self.base_url.rstrip('/')}{href}"
                        page_name = f"article_{article_count}"
                        important_pages[page_name] = full_url
                        article_count += 1
        
        except Exception as e:
            print(f"Error discovering content: {str(e)}")
        
        return important_pages

    async def scrape_all(self):
        """Main scraping function"""
        print("Starting Northern Miner scraping for Canadian mining companies...")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            
            # Discover important pages
            pages = await self.discover_canadian_mining_content(crawler)
            print(f"Found {len(pages)} pages to scrape")
            
            # Scrape each page
            for page_name, url in pages.items():
                page_data = await self.scrape_page(crawler, url, page_name)
                if page_data:
                    self.data[page_name] = page_data
                
                # Add delay to be respectful
                await asyncio.sleep(1)
        
        return self.data

    def extract_canadian_mining_info(self):
        """Extract Canadian mining specific information"""
        extracted_info = {
            'company_news': [],
            'market_updates': [],
            'project_developments': [],
            'financial_announcements': [],
            'exploration_updates': [],
            'production_reports': [],
            'canadian_companies_mentioned': set(),
            'stock_symbols': set(),
            'commodity_prices': [],
            'dates_found': []
        }
        
        # Canadian mining companies (partial list)
        canadian_companies = [
            'barrick', 'newmont', 'kinross', 'agnico eagle', 'franco nevada',
            'shopify', 'canadian national railway', 'magna international',
            'first quantum', 'lundin mining', 'hudbay minerals', 'eldorado gold',
            'centerra gold', 'iamgold', 'kirkland lake', 'detour gold',
            'osisko', 'yamana', 'goldcorp', 'teck resources', 'cenovus',
            'suncor', 'canadian natural resources', 'imperial oil'
        ]
        
        # Keywords for different types of updates
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'guidance', 'forecast',
            'quarterly results', 'financial results', 'dividend', 'debt',
            'financing', 'investment', 'capital', 'cash flow', 'ebitda'
        ]
        
        project_keywords = [
            'mine', 'mining', 'project', 'operation', 'production', 'exploration',
            'development', 'expansion', 'construction', 'resource', 'reserve',
            'drilling', 'deposit', 'ore', 'grade', 'tonnage', 'mill', 'plant'
        ]
        
        commodity_keywords = [
            'gold', 'silver', 'copper', 'nickel', 'zinc', 'lead', 'platinum',
            'palladium', 'uranium', 'iron ore', 'coal', 'oil', 'gas'
        ]
        
        # Process all scraped content
        for page_name, page_data in self.data.items():
            if not isinstance(page_data, dict):
                continue
                
            content = page_data.get('content', '').lower()
            
            # Extract dates
            date_patterns = [
                r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{4}-\d{1,2}-\d{1,2}\b',
                r'\bq[1-4]\s+\d{4}\b'
            ]
            
            for pattern in date_patterns:
                dates = re.findall(pattern, content, re.IGNORECASE)
                extracted_info['dates_found'].extend(dates)
            
            # Check for Canadian companies
            for company in canadian_companies:
                if company.lower() in content:
                    extracted_info['canadian_companies_mentioned'].add(company)
            
            # Extract stock symbols (TSX format)
            tsx_symbols = re.findall(r'\b[A-Z]{1,5}\.TO\b|\bTSX:\s*([A-Z]{1,5})\b|\bTSXV:\s*([A-Z]{1,5})\b', content)
            for symbol_match in tsx_symbols:
                if isinstance(symbol_match, tuple):
                    for symbol in symbol_match:
                        if symbol:
                            extracted_info['stock_symbols'].add(symbol)
                else:
                    extracted_info['stock_symbols'].add(symbol_match)
            
            # Categorize content by keywords
            paragraphs = content.split('\n')
            for para in paragraphs:
                para = para.strip()
                if len(para) < 50:
                    continue
                
                # Financial announcements
                if any(keyword in para for keyword in financial_keywords):
                    extracted_info['financial_announcements'].append({
                        'content': para[:300],
                        'source_page': page_name,
                        'url': page_data.get('url', '')
                    })
                
                # Project developments
                if any(keyword in para for keyword in project_keywords):
                    extracted_info['project_developments'].append({
                        'content': para[:300],
                        'source_page': page_name,
                        'url': page_data.get('url', '')
                    })
                
                # Market/commodity updates
                if any(keyword in para for keyword in commodity_keywords):
                    extracted_info['commodity_prices'].append({
                        'content': para[:300],
                        'source_page': page_name,
                        'url': page_data.get('url', '')
                    })
        
        # Convert sets to lists for JSON serialization
        extracted_info['canadian_companies_mentioned'] = list(extracted_info['canadian_companies_mentioned'])
        extracted_info['stock_symbols'] = list(extracted_info['stock_symbols'])
        
        return extracted_info

    def save_data(self, filename=None):
        """Save scraped data"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"northern_miner_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        print(f"Raw data saved to {filename}")
        return filename

    def save_extracted_info(self, extracted_info, filename=None):
        """Save extracted Canadian mining information"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"canadian_mining_news_{timestamp}.json"
            report_filename = f"canadian_mining_report_{timestamp}.txt"
        else:
            json_filename = f"{filename}.json"
            report_filename = f"{filename}_report.txt"
        
        # Save JSON
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(extracted_info, f, indent=2, ensure_ascii=False)
        
        # Generate and save report
        report = self.generate_report(extracted_info)
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return json_filename, report_filename

    def generate_report(self, extracted_info):
        """Generate a readable report"""
        report = []
        report.append("CANADIAN MINING INDUSTRY NEWS SUMMARY")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Source: Northern Miner (northernminer.com)")
        report.append("")
        
        # Companies mentioned
        if extracted_info['canadian_companies_mentioned']:
            report.append("CANADIAN COMPANIES MENTIONED:")
            report.append("-" * 30)
            for company in sorted(extracted_info['canadian_companies_mentioned']):
                report.append(f"• {company.title()}")
            report.append("")
        
        # Stock symbols
        if extracted_info['stock_symbols']:
            report.append("STOCK SYMBOLS FOUND:")
            report.append("-" * 20)
            for symbol in sorted(extracted_info['stock_symbols']):
                report.append(f"• {symbol}")
            report.append("")
        
        # Financial announcements
        if extracted_info['financial_announcements']:
            report.append("FINANCIAL ANNOUNCEMENTS:")
            report.append("-" * 25)
            for item in extracted_info['financial_announcements'][:10]:
                report.append(f"• {item['content']}")
                report.append(f"  Source: {item['url']}")
                report.append("")
        
        # Project developments
        if extracted_info['project_developments']:
            report.append("PROJECT DEVELOPMENTS:")
            report.append("-" * 21)
            for item in extracted_info['project_developments'][:10]:
                report.append(f"• {item['content']}")
                report.append(f"  Source: {item['url']}")
                report.append("")
        
        # Commodity updates
        if extracted_info['commodity_prices']:
            report.append("COMMODITY & MARKET UPDATES:")
            report.append("-" * 27)
            for item in extracted_info['commodity_prices'][:10]:
                report.append(f"• {item['content']}")
                report.append(f"  Source: {item['url']}")
                report.append("")
        
        return "\n".join(report)

async def main():
    """Main execution function"""
    scraper = NorthernMinerScraper()
    
    try:
        # Scrape the website
        print("Scraping Northern Miner for Canadian mining news...")
        data = await scraper.scrape_all()
        
        # Save raw data
        raw_filename = scraper.save_data()
        
        # Extract Canadian mining specific information
        print("Extracting Canadian mining information...")
        extracted_info = scraper.extract_canadian_mining_info()
        
        # Save extracted information
        json_file, report_file = scraper.save_extracted_info(extracted_info)
        
        # Display summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Pages scraped: {len(data)}")
        print(f"Canadian companies found: {len(extracted_info['canadian_companies_mentioned'])}")
        print(f"Stock symbols found: {len(extracted_info['stock_symbols'])}")
        print(f"Financial announcements: {len(extracted_info['financial_announcements'])}")
        print(f"Project developments: {len(extracted_info['project_developments'])}")
        print(f"Commodity updates: {len(extracted_info['commodity_prices'])}")
        print(f"\nFiles created:")
        print(f"• Raw data: {raw_filename}")
        print(f"• Extracted data: {json_file}")
        print(f"• Report: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the scraper
    success = asyncio.run(main())
    
    if success:
        print("\nScraping completed successfully!")
    else:
        print("\nScraping failed. Check the error messages above.")