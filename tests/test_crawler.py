#!/usr/bin/env python3
"""
Test Crawler for TSX Mining Companies
Tests the scraping functionality on collected companies
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
import re

class CrawlerTester:
    def __init__(self, db_path="mining_companies.db"):
        self.db_path = db_path
        self.test_results = []
        
    def get_test_companies(self, limit=5):
        """Get a sample of companies for testing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, website, investor_relations_url, news_url 
            FROM companies 
            WHERE website IS NOT NULL AND website != ''
            ORDER BY market_cap DESC
            LIMIT ?
        ''', (limit,))
        
        companies = cursor.fetchall()
        conn.close()
        
        return [
            {
                'symbol': row[0],
                'name': row[1], 
                'website': row[2],
                'ir_url': row[3],
                'news_url': row[4]
            }
            for row in companies
        ]
    
    async def test_single_company(self, crawler, company):
        """Test scraping a single company"""
        print(f"\nTesting {company['symbol']} - {company['name']}")
        print("-" * 50)
        
        test_result = {
            'symbol': company['symbol'],
            'name': company['name'],
            'website_status': 'failed',
            'ir_status': 'failed', 
            'news_status': 'failed',
            'content_found': False,
            'news_items': [],
            'financial_keywords': [],
            'project_keywords': [],
            'error_messages': []
        }
        
        # Test main website
        try:
            print(f"Testing main website: {company['website']}")
            result = await crawler.arun(
                url=company['website'],
                word_count_threshold=50
            )
            
            if result.markdown and len(result.markdown) > 100:
                test_result['website_status'] = 'success'
                test_result['content_found'] = True
                
                # Extract basic info
                content = result.markdown.lower()
                test_result['financial_keywords'] = self.extract_financial_keywords(content)
                test_result['project_keywords'] = self.extract_project_keywords(content)
                
                print(f"✓ Main website accessible ({len(result.markdown)} chars)")
                print(f"  Financial keywords: {len(test_result['financial_keywords'])}")
                print(f"  Project keywords: {len(test_result['project_keywords'])}")
            else:
                print("✗ Main website - insufficient content")
                
        except Exception as e:
            print(f"✗ Main website error: {str(e)}")
            test_result['error_messages'].append(f"Website: {str(e)}")
        
        # Test IR page if available
        if company['ir_url']:
            try:
                print(f"Testing IR page: {company['ir_url']}")
                result = await crawler.arun(
                    url=company['ir_url'],
                    word_count_threshold=50
                )
                
                if result.markdown and len(result.markdown) > 100:
                    test_result['ir_status'] = 'success'
                    content = result.markdown.lower()
                    
                    # Look for investor-specific content
                    ir_keywords = ['earnings', 'financial', 'investor', 'annual report', 'quarterly']
                    ir_content = sum(1 for keyword in ir_keywords if keyword in content)
                    
                    print(f"✓ IR page accessible ({len(result.markdown)} chars, {ir_content} IR keywords)")
                else:
                    print("✗ IR page - insufficient content")
                    
            except Exception as e:
                print(f"✗ IR page error: {str(e)}")
                test_result['error_messages'].append(f"IR: {str(e)}")
        
        # Test news page if available  
        if company['news_url']:
            try:
                print(f"Testing news page: {company['news_url']}")
                result = await crawler.arun(
                    url=company['news_url'],
                    word_count_threshold=50
                )
                
                if result.markdown and len(result.markdown) > 100:
                    test_result['news_status'] = 'success'
                    
                    # Extract potential news items
                    news_items = self.extract_news_items(result.markdown)
                    test_result['news_items'] = news_items
                    
                    print(f"✓ News page accessible ({len(result.markdown)} chars, {len(news_items)} news items)")
                else:
                    print("✗ News page - insufficient content")
                    
            except Exception as e:
                print(f"✗ News page error: {str(e)}")
                test_result['error_messages'].append(f"News: {str(e)}")
        
        # Add delay between companies
        await asyncio.sleep(2)
        
        return test_result
    
    def extract_financial_keywords(self, content):
        """Extract financial-related keywords"""
        financial_keywords = [
            'earnings', 'revenue', 'profit', 'ebitda', 'cash flow',
            'quarterly results', 'guidance', 'dividend', 'debt',
            'financing', 'acquisition', 'merger', 'share price'
        ]
        
        found = []
        for keyword in financial_keywords:
            if keyword in content:
                found.append(keyword)
        
        return found
    
    def extract_project_keywords(self, content):
        """Extract project-related keywords"""
        project_keywords = [
            'mine', 'mining', 'exploration', 'drilling', 'production',
            'resource', 'reserve', 'deposit', 'ore grade', 'tonnage',
            'mill', 'processing', 'expansion', 'development'
        ]
        
        found = []
        for keyword in project_keywords:
            if keyword in content:
                found.append(keyword)
        
        return found
    
    def extract_news_items(self, content):
        """Extract potential news items from content"""
        news_items = []
        
        # Look for date patterns and nearby text
        date_patterns = [
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})'
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in date_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    # Get surrounding context
                    context_start = max(0, i-1)
                    context_end = min(len(lines), i+2)
                    context = ' '.join(lines[context_start:context_end]).strip()
                    
                    if len(context) > 50 and len(context) < 300:
                        news_items.append({
                            'date': matches[0],
                            'content': context[:200] + '...' if len(context) > 200 else context
                        })
        
        return news_items[:5]  # Limit to 5 items
    
    async def run_test(self, num_companies=5):
        """Run the full test suite"""
        print("TSX Mining Company Crawler Test")
        print("=" * 50)
        
        # Get test companies
        companies = self.get_test_companies(num_companies)
        
        if not companies:
            print("No companies found in database!")
            return False
        
        print(f"Testing {len(companies)} companies:")
        for company in companies:
            print(f"• {company['symbol']}: {company['name']}")
        
        # Run tests
        async with AsyncWebCrawler(headless=True) as crawler:
            for company in companies:
                test_result = await self.test_single_company(crawler, company)
                self.test_results.append(test_result)
        
        # Generate summary
        self.generate_test_summary()
        
        return True
    
    def generate_test_summary(self):
        """Generate and display test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_companies = len(self.test_results)
        successful_websites = sum(1 for r in self.test_results if r['website_status'] == 'success')
        successful_ir = sum(1 for r in self.test_results if r['ir_status'] == 'success')
        successful_news = sum(1 for r in self.test_results if r['news_status'] == 'success')
        
        print(f"Companies tested: {total_companies}")
        print(f"Successful website scrapes: {successful_websites}/{total_companies}")
        print(f"Successful IR page scrapes: {successful_ir}/{total_companies}")
        print(f"Successful news page scrapes: {successful_news}/{total_companies}")
        print()
        
        # Show results per company
        print("DETAILED RESULTS:")
        print("-" * 30)
        for result in self.test_results:
            print(f"\n{result['symbol']} - {result['name']}")
            print(f"  Website: {result['website_status']}")
            print(f"  IR Page: {result['ir_status']}")
            print(f"  News: {result['news_status']}")
            print(f"  Financial keywords: {len(result['financial_keywords'])}")
            print(f"  Project keywords: {len(result['project_keywords'])}")
            print(f"  News items found: {len(result['news_items'])}")
            
            if result['error_messages']:
                print(f"  Errors: {'; '.join(result['error_messages'])}")
        
        # Show sample content
        successful_results = [r for r in self.test_results if r['website_status'] == 'success']
        if successful_results:
            print(f"\nSAMPLE CONTENT FROM {successful_results[0]['symbol']}:")
            print("-" * 40)
            result = successful_results[0]
            
            if result['financial_keywords']:
                print(f"Financial keywords: {', '.join(result['financial_keywords'][:5])}")
            
            if result['project_keywords']:
                print(f"Project keywords: {', '.join(result['project_keywords'][:5])}")
            
            if result['news_items']:
                print(f"Sample news item:")
                news = result['news_items'][0]
                print(f"  Date: {news['date']}")
                print(f"  Content: {news['content'][:150]}...")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"crawler_test_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Overall assessment
        success_rate = successful_websites / total_companies * 100
        print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✓ Crawler is working well!")
        elif success_rate >= 60:
            print("⚠ Crawler working but some issues detected")
        else:
            print("✗ Crawler needs improvement")

async def main():
    """Main test execution"""
    tester = CrawlerTester()
    
    try:
        success = await tester.run_test(num_companies=5)
        
        if success:
            print("\nCrawler test completed!")
        else:
            print("\nCrawler test failed!")
            
    except Exception as e:
        print(f"Test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())