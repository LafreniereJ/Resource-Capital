#!/usr/bin/env python3
"""
Test Crawl4AI on Configuration-Defined Websites
Tests the scrapers against the targets defined in scraper_targets.json
"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from src.utils.scraper_config import load_scraper_config
import time

class ConfigScraperTester:
    def __init__(self):
        self.config_manager = None
        self.test_results = []
        
    def load_config(self):
        """Load the scraper configuration"""
        print("Loading scraper configuration...")
        self.config_manager = load_scraper_config()
        if not self.config_manager:
            print("❌ Failed to load configuration")
            return False
        
        summary = self.config_manager.get_config_summary()
        print(f"✅ Loaded {summary['total_targets']} targets from config")
        return True
    
    async def test_single_target(self, crawler, target):
        """Test a single scraper target"""
        print(f"\n{'='*60}")
        print(f"Testing: {target.name}")
        print(f"Base URL: {target.base_url}")
        print(f"Priority: {target.priority} | Rate Limit: {target.rate_limit}s")
        print(f"{'='*60}")
        
        test_result = {
            'target_name': target.name,
            'base_url': target.base_url,
            'priority': target.priority,
            'test_timestamp': datetime.now().isoformat(),
            'pages_tested': 0,
            'pages_successful': 0,
            'total_content_length': 0,
            'keywords_found': {},
            'errors': [],
            'page_results': []
        }
        
        # Test each target page
        for i, page_config in enumerate(target.target_pages):
            page_url = page_config['url']
            page_type = page_config['type']
            
            print(f"\n📄 Testing page {i+1}/{len(target.target_pages)}: {page_type}")
            print(f"   URL: {page_url}")
            
            page_result = {
                'url': page_url,
                'type': page_type,
                'status': 'failed',
                'content_length': 0,
                'word_count': 0,
                'relevance_score': 0,
                'keywords_found': [],
                'error': None
            }
            
            try:
                # Add custom headers if specified
                crawler_kwargs = {}
                if target.headers:
                    crawler_kwargs['headers'] = target.headers
                
                # Scrape the page
                start_time = time.time()
                result = await crawler.arun(
                    url=page_url,
                    word_count_threshold=50,
                    **crawler_kwargs
                )
                scrape_time = time.time() - start_time
                
                if result.markdown and len(result.markdown) > 100:
                    content = result.markdown
                    page_result['status'] = 'success'
                    page_result['content_length'] = len(content)
                    page_result['word_count'] = len(content.split())
                    
                    # Calculate relevance score using config
                    relevance_score = self.config_manager.calculate_relevance_score(content)
                    page_result['relevance_score'] = relevance_score
                    
                    # Find keywords
                    keywords_found = self.find_keywords_in_content(content, target.keywords)
                    page_result['keywords_found'] = keywords_found
                    
                    # Update totals
                    test_result['pages_successful'] += 1
                    test_result['total_content_length'] += len(content)
                    
                    # Merge keywords
                    for category, keywords in keywords_found.items():
                        if category not in test_result['keywords_found']:
                            test_result['keywords_found'][category] = set()
                        test_result['keywords_found'][category].update(keywords)
                    
                    print(f"   ✅ Success ({scrape_time:.1f}s)")
                    print(f"      Content: {len(content):,} chars, {len(content.split()):,} words")
                    print(f"      Relevance: {relevance_score}/100")
                    print(f"      Keywords: {sum(len(kw) for kw in keywords_found.values())} found")
                    
                    # Show sample content
                    if len(content) > 200:
                        sample = content[:200].replace('\n', ' ').strip()
                        print(f"      Sample: {sample}...")
                    
                else:
                    page_result['error'] = "Insufficient content returned"
                    print(f"   ❌ Failed: Insufficient content ({len(result.markdown) if result.markdown else 0} chars)")
                
            except Exception as e:
                error_msg = str(e)
                page_result['error'] = error_msg
                test_result['errors'].append(f"{page_type}: {error_msg}")
                print(f"   ❌ Error: {error_msg}")
            
            test_result['pages_tested'] += 1
            test_result['page_results'].append(page_result)
            
            # Rate limiting
            await asyncio.sleep(target.rate_limit)
        
        # Convert sets to lists for JSON serialization
        for category in test_result['keywords_found']:
            test_result['keywords_found'][category] = list(test_result['keywords_found'][category])
        
        # Calculate success rate
        success_rate = (test_result['pages_successful'] / test_result['pages_tested']) * 100 if test_result['pages_tested'] > 0 else 0
        test_result['success_rate'] = success_rate
        
        print(f"\n📊 {target.name} Summary:")
        print(f"   Success Rate: {success_rate:.1f}% ({test_result['pages_successful']}/{test_result['pages_tested']})")
        print(f"   Total Content: {test_result['total_content_length']:,} characters")
        print(f"   Keywords Found: {sum(len(kw) for kw in test_result['keywords_found'].values())}")
        if test_result['errors']:
            print(f"   Errors: {len(test_result['errors'])}")
        
        return test_result
    
    def find_keywords_in_content(self, content, target_keywords):
        """Find target keywords in content"""
        content_lower = content.lower()
        found_keywords = {}
        
        for category, keywords in target_keywords.items():
            found_in_category = []
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    found_in_category.append(keyword)
            
            if found_in_category:
                found_keywords[category] = found_in_category
        
        return found_keywords
    
    async def run_tests(self, target_names=None, max_targets=None):
        """Run tests on all or specified targets"""
        if not self.config_manager:
            print("❌ Configuration not loaded")
            return False
        
        # Get targets to test
        all_targets = self.config_manager.get_enabled_targets()
        
        if target_names:
            targets_to_test = [self.config_manager.get_target_by_name(name) for name in target_names]
            targets_to_test = [t for t in targets_to_test if t is not None]
        else:
            targets_to_test = all_targets
        
        if max_targets:
            targets_to_test = targets_to_test[:max_targets]
        
        if not targets_to_test:
            print("❌ No targets to test")
            return False
        
        print(f"\n🚀 Starting tests on {len(targets_to_test)} targets...")
        print(f"Targets: {[t.name for t in targets_to_test]}")
        
        # Run tests
        async with AsyncWebCrawler(headless=True) as crawler:
            for target in targets_to_test:
                test_result = await self.test_single_target(crawler, target)
                self.test_results.append(test_result)
        
        return True
    
    def generate_summary_report(self):
        """Generate overall test summary"""
        if not self.test_results:
            print("❌ No test results to summarize")
            return
        
        print(f"\n{'='*80}")
        print("📋 OVERALL TEST SUMMARY")
        print(f"{'='*80}")
        
        total_targets = len(self.test_results)
        total_pages = sum(r['pages_tested'] for r in self.test_results)
        total_successful = sum(r['pages_successful'] for r in self.test_results)
        total_content = sum(r['total_content_length'] for r in self.test_results)
        
        overall_success_rate = (total_successful / total_pages) * 100 if total_pages > 0 else 0
        
        print(f"Targets Tested: {total_targets}")
        print(f"Pages Tested: {total_pages}")
        print(f"Pages Successful: {total_successful}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Total Content Scraped: {total_content:,} characters")
        
        # Target-by-target breakdown
        print(f"\n📊 TARGET BREAKDOWN:")
        print("-" * 60)
        for result in self.test_results:
            status_icon = "✅" if result['success_rate'] >= 75 else "⚠️" if result['success_rate'] >= 50 else "❌"
            print(f"{status_icon} {result['target_name']}: {result['success_rate']:.1f}% "
                  f"({result['pages_successful']}/{result['pages_tested']}) "
                  f"- {result['total_content_length']:,} chars")
            
            if result['errors']:
                for error in result['errors'][:2]:  # Show first 2 errors
                    print(f"    ⚠️  {error}")
        
        # Best performing targets
        best_targets = sorted(self.test_results, key=lambda x: x['success_rate'], reverse=True)
        print(f"\n🏆 BEST PERFORMING TARGETS:")
        print("-" * 40)
        for result in best_targets[:3]:
            print(f"1. {result['target_name']}: {result['success_rate']:.1f}%")
            total_keywords = sum(len(kw) for kw in result['keywords_found'].values())
            print(f"   Keywords found: {total_keywords}")
            print(f"   Content volume: {result['total_content_length']:,} chars")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"config_scraper_test_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Overall assessment
        if overall_success_rate >= 75:
            print(f"\n🎉 EXCELLENT: Configuration targets are working well!")
        elif overall_success_rate >= 50:
            print(f"\n👍 GOOD: Most targets working, some issues to address")
        else:
            print(f"\n⚠️  NEEDS WORK: Configuration targets need adjustment")

async def main():
    """Main test execution"""
    tester = ConfigScraperTester()
    
    print("🧪 Config-Based Scraper Testing")
    print("=" * 50)
    
    # Load configuration
    if not tester.load_config():
        return False
    
    try:
        # Test high priority targets first
        high_priority_targets = ['Reuters', 'Northern Miner', 'Mining.com']
        
        print(f"\n🎯 Testing high-priority targets: {high_priority_targets}")
        success = await tester.run_tests(target_names=high_priority_targets)
        
        if success:
            tester.generate_summary_report()
            return True
        else:
            print("❌ Tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Config scraper testing completed!")
    else:
        print("\n❌ Config scraper testing failed!")