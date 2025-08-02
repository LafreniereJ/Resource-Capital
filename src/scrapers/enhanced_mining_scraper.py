#!/usr/bin/env python3
"""
Enhanced Mining News Scraper
Follows article links and scrapes full content from Northern Miner and other mining news sites
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from crawl4ai import AsyncWebCrawler
import time

class EnhancedMiningScraper:
    def __init__(self, max_articles=50, days_back=30):
        self.base_urls = {
            'northern_miner': 'https://www.northernminer.com',
            'mining_com': 'https://www.mining.com',
            'kitco': 'https://www.kitco.com/news/'
        }
        self.max_articles = max_articles
        self.days_back = days_back
        self.articles = []
        self.failed_urls = []
        
        # Keywords for Canadian mining content
        self.canadian_keywords = [
            'canada', 'canadian', 'toronto', 'vancouver', 'tsx', 'tsxv',
            'ontario', 'quebec', 'british columbia', 'alberta', 'manitoba',
            'saskatchewan', 'newfoundland', 'northwest territories', 'yukon',
            'cad', 'canadian dollar'
        ]
        
        # Mining companies to track
        self.mining_companies = [
            'barrick gold', 'newmont', 'kinross', 'agnico eagle', 'franco nevada',
            'first quantum', 'lundin mining', 'hudbay minerals', 'eldorado gold',
            'centerra gold', 'iamgold', 'kirkland lake', 'detour gold',
            'osisko', 'yamana', 'goldcorp', 'teck resources', 'magna mining',
            'endeavour mining', 'b2gold', 'torex gold', 'seabridge gold',
            'pretium resources', 'alacer gold', 'alamos gold', 'calibre mining'
        ]
        
        # Financial keywords
        self.financial_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'ebitda', 'cash flow',
            'quarterly results', 'annual results', 'guidance', 'forecast',
            'dividend', 'share buyback', 'financing', 'debt', 'equity',
            'acquisition', 'merger', 'takeover', 'ipo', 'listing'
        ]
        
        # Project keywords
        self.project_keywords = [
            'mine', 'mining', 'project', 'operation', 'production', 'exploration',
            'development', 'expansion', 'construction', 'resource estimate',
            'reserve', 'drilling', 'deposit', 'ore grade', 'tonnage',
            'mill', 'processing plant', 'feasibility study', 'environmental approval'
        ]

    async def discover_article_links(self, crawler, base_url, site_name):
        """Discover article links from main pages"""
        print(f"Discovering articles from {site_name}...")
        
        article_links = []
        
        try:
            # Get main news page
            result = await crawler.arun(url=base_url, word_count_threshold=5)
            
            # Extract links
            links = getattr(result, 'links', {})
            if isinstance(links, dict):
                all_links = links.get('internal', []) + links.get('external', [])
            else:
                all_links = []
            
            # Filter for article links
            for link in all_links:
                href = link.get('href', '')
                text = link.get('text', '').lower()
                
                if not href:
                    continue
                
                # Make absolute URL
                if href.startswith('/'):
                    full_url = urljoin(base_url, href)
                elif not href.startswith('http'):
                    continue
                else:
                    full_url = href
                
                # Filter for article patterns
                article_patterns = [
                    '/news/', '/article/', '/story/', '/press-release/',
                    '/mining/', '/exploration/', '/companies/', '/markets/'
                ]
                
                if any(pattern in href.lower() for pattern in article_patterns):
                    # Check if it mentions Canadian content or mining companies
                    content_relevant = (
                        any(keyword in text for keyword in self.canadian_keywords) or
                        any(company in text for company in self.mining_companies) or
                        any(keyword in text for keyword in self.financial_keywords + self.project_keywords)
                    )
                    
                    if content_relevant or 'canada' in href.lower():
                        article_links.append({
                            'url': full_url,
                            'title': link.get('text', ''),
                            'source': site_name
                        })
                        
                        if len(article_links) >= self.max_articles:
                            break
            
        except Exception as e:
            print(f"Error discovering articles from {site_name}: {str(e)}")
        
        print(f"Found {len(article_links)} potential articles from {site_name}")
        return article_links

    async def scrape_article(self, crawler, article_info):
        """Scrape full content of an individual article"""
        url = article_info['url']
        print(f"Scraping article: {url}")
        
        try:
            result = await crawler.arun(
                url=url,
                word_count_threshold=100
            )
            
            content = result.markdown
            
            # Extract article metadata
            article_data = {
                'url': url,
                'title': article_info.get('title', ''),
                'source': article_info.get('source', ''),
                'content': content,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(content.split()),
                'metadata': getattr(result, 'metadata', {})
            }
            
            # Extract dates from content
            article_data['dates_mentioned'] = self.extract_dates(content)
            
            # Extract financial information
            article_data['financial_info'] = self.extract_financial_info(content)
            
            # Extract company mentions
            article_data['companies_mentioned'] = self.extract_companies(content)
            
            # Extract project information
            article_data['project_info'] = self.extract_project_info(content)
            
            # Calculate relevance score
            article_data['relevance_score'] = self.calculate_relevance_score(content)
            
            return article_data
            
        except Exception as e:
            print(f"Error scraping article {url}: {str(e)}")
            self.failed_urls.append(url)
            return None

    def extract_dates(self, content):
        """Extract dates from article content"""
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',
            r'\bQ[1-4]\s+\d{4}\b',
            r'\b\d{4}\s+Q[1-4]\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates

    def extract_financial_info(self, content):
        """Extract financial information from content"""
        financial_data = []
        
        # Look for financial numbers
        money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?\s*(?:million|billion|M|B)',
            r'(?:revenue|profit|loss|ebitda|cash flow)[^$]*\$[\d,]+(?:\.\d{2})?',
            r'(?:earnings|guidance)[^$]*\$[\d,]+(?:\.\d{2})?'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            financial_data.extend(matches)
        
        # Look for percentage changes
        percent_patterns = [
            r'(?:up|down|increased|decreased|rose|fell)\s+(?:by\s+)?(\d+(?:\.\d+)?%)',
            r'(\d+(?:\.\d+)?%)\s+(?:increase|decrease|growth|decline)'
        ]
        
        for pattern in percent_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            financial_data.extend(matches)
        
        return financial_data

    def extract_companies(self, content):
        """Extract mentioned mining companies"""
        mentioned = []
        content_lower = content.lower()
        
        for company in self.mining_companies:
            if company.lower() in content_lower:
                mentioned.append(company)
        
        return mentioned

    def extract_project_info(self, content):
        """Extract project-related information"""
        project_data = []
        
        # Look for project names and locations
        project_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:mine|project|operation|deposit))',
            r'(?:located in|in)\s+([A-Z][a-zA-Z\s]+,\s*(?:Canada|Ontario|Quebec|British Columbia|Alberta))',
            r'(\d+(?:,\d{3})*)\s*(?:tonnes|tons|ounces|pounds)\s*(?:of|per)',
            r'grade\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*(?:g/t|oz/t|%)'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            project_data.extend(matches)
        
        return project_data

    def calculate_relevance_score(self, content):
        """Calculate relevance score for Canadian mining content"""
        score = 0
        content_lower = content.lower()
        
        # Canadian relevance
        for keyword in self.canadian_keywords:
            score += content_lower.count(keyword.lower()) * 2
        
        # Company mentions
        for company in self.mining_companies:
            if company.lower() in content_lower:
                score += 5
        
        # Financial keywords
        for keyword in self.financial_keywords:
            score += content_lower.count(keyword.lower()) * 3
        
        # Project keywords
        for keyword in self.project_keywords:
            score += content_lower.count(keyword.lower()) * 2
        
        return min(score, 100)  # Cap at 100

    async def scrape_all_sources(self):
        """Scrape articles from all sources"""
        print("Starting enhanced mining news scraping...")
        
        all_article_links = []
        
        async with AsyncWebCrawler(headless=True) as crawler:
            
            # Discover articles from each source
            for source_name, base_url in self.base_urls.items():
                links = await self.discover_article_links(crawler, base_url, source_name)
                all_article_links.extend(links)
                await asyncio.sleep(1)  # Rate limiting
            
            print(f"Total articles to scrape: {len(all_article_links)}")
            
            # Scrape individual articles
            for i, article_info in enumerate(all_article_links):
                print(f"Progress: {i+1}/{len(all_article_links)}")
                
                article_data = await self.scrape_article(crawler, article_info)
                if article_data:
                    self.articles.append(article_data)
                
                # Rate limiting - be respectful
                await asyncio.sleep(2)
                
                # Progress update every 10 articles
                if (i + 1) % 10 == 0:
                    print(f"Scraped {len(self.articles)} articles successfully, {len(self.failed_urls)} failed")
        
        return self.articles

    def filter_and_rank_articles(self):
        """Filter articles by relevance and recency"""
        # Sort by relevance score
        self.articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Filter for high relevance (score > 10)
        high_relevance = [article for article in self.articles if article.get('relevance_score', 0) > 10]
        
        return high_relevance

    def generate_comprehensive_report(self):
        """Generate detailed report of findings"""
        high_relevance_articles = self.filter_and_rank_articles()
        
        report = []
        report.append("COMPREHENSIVE CANADIAN MINING NEWS ANALYSIS")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total articles scraped: {len(self.articles)}")
        report.append(f"High relevance articles: {len(high_relevance_articles)}")
        report.append(f"Failed URLs: {len(self.failed_urls)}")
        report.append("")
        
        # Top articles by relevance
        report.append("TOP ARTICLES BY RELEVANCE:")
        report.append("-" * 30)
        for i, article in enumerate(high_relevance_articles[:10]):
            report.append(f"{i+1}. {article['title']}")
            report.append(f"   Score: {article.get('relevance_score', 0)} | Source: {article['source']}")
            report.append(f"   URL: {article['url']}")
            if article.get('companies_mentioned'):
                report.append(f"   Companies: {', '.join(article['companies_mentioned'])}")
            if article.get('financial_info'):
                report.append(f"   Financial: {', '.join(article['financial_info'][:3])}")
            report.append("")
        
        # Company mentions summary
        all_companies = {}
        for article in self.articles:
            for company in article.get('companies_mentioned', []):
                all_companies[company] = all_companies.get(company, 0) + 1
        
        if all_companies:
            report.append("COMPANIES MENTIONED (Top 10):")
            report.append("-" * 25)
            sorted_companies = sorted(all_companies.items(), key=lambda x: x[1], reverse=True)
            for company, count in sorted_companies[:10]:
                report.append(f"• {company}: {count} mentions")
            report.append("")
        
        # Recent financial news
        financial_articles = [a for a in high_relevance_articles if a.get('financial_info')][:5]
        if financial_articles:
            report.append("RECENT FINANCIAL NEWS:")
            report.append("-" * 22)
            for article in financial_articles:
                report.append(f"• {article['title']}")
                report.append(f"  {', '.join(article['financial_info'][:2])}")
                report.append(f"  {article['url']}")
                report.append("")
        
        return "\n".join(report)

    def save_results(self, filename_prefix=None):
        """Save all results to files"""
        if filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = f"enhanced_mining_news_{timestamp}"
        
        # Save full articles data
        articles_file = f"{filename_prefix}_articles.json"
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
        
        # Save high relevance articles only
        high_relevance = self.filter_and_rank_articles()
        relevant_file = f"{filename_prefix}_relevant.json"
        with open(relevant_file, 'w', encoding='utf-8') as f:
            json.dump(high_relevance, f, indent=2, ensure_ascii=False)
        
        # Save comprehensive report
        report = self.generate_comprehensive_report()
        report_file = f"{filename_prefix}_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save summary stats
        summary = {
            'total_articles': len(self.articles),
            'high_relevance_articles': len(high_relevance),
            'failed_urls': len(self.failed_urls),
            'sources_scraped': list(self.base_urls.keys()),
            'scraping_completed': datetime.now().isoformat()
        }
        
        summary_file = f"{filename_prefix}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return {
            'articles': articles_file,
            'relevant': relevant_file,
            'report': report_file,
            'summary': summary_file
        }

async def main():
    """Main execution function"""
    print("Enhanced Mining News Scraper")
    print("=" * 40)
    
    # Initialize scraper (limit to 30 articles for demo)
    scraper = EnhancedMiningScraper(max_articles=30, days_back=30)
    
    try:
        # Scrape all sources
        articles = await scraper.scrape_all_sources()
        
        # Save results
        files = scraper.save_results()
        
        # Display summary
        print("\n" + "="*50)
        print("SCRAPING COMPLETED")
        print("="*50)
        print(f"Total articles scraped: {len(articles)}")
        print(f"Failed URLs: {len(scraper.failed_urls)}")
        
        high_relevance = scraper.filter_and_rank_articles()
        print(f"High relevance articles: {len(high_relevance)}")
        
        print(f"\nFiles created:")
        for file_type, filename in files.items():
            print(f"• {file_type}: {filename}")
        
        # Show top 3 articles
        if high_relevance:
            print(f"\nTOP 3 MOST RELEVANT ARTICLES:")
            print("-" * 35)
            for i, article in enumerate(high_relevance[:3]):
                print(f"{i+1}. {article['title'][:60]}...")
                print(f"   Relevance: {article.get('relevance_score', 0)} | Companies: {len(article.get('companies_mentioned', []))}")
                print(f"   URL: {article['url']}")
                print()
        
        return True
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("Enhanced scraping completed successfully!")
        print("Check the generated files for detailed analysis.")
    else:
        print("Enhanced scraping failed. Check error messages above.")