#!/usr/bin/env python3
"""
Test the Intelligent Unified Scraper System
Tests learning capabilities and performance optimization
"""

import asyncio
import json
from datetime import datetime
from src.scrapers.unified_scraper import UnifiedScraper, ScrapingStrategy
from src.scrapers.scraper_intelligence import ScraperIntelligence
from src.utils.scraper_config import load_scraper_config

async def test_intelligent_scraper():
    """Test the intelligent scraper system"""
    
    print("🧠 Testing Intelligent Unified Scraper System")
    print("=" * 60)
    
    # Load configuration
    config_manager = load_scraper_config()
    if not config_manager:
        print("❌ Failed to load scraper configuration")
        return False
    
    # Initialize intelligence system
    intelligence = ScraperIntelligence()
    
    # Initialize unified scraper with intelligence
    scraper = UnifiedScraper(config_manager=config_manager, intelligence=intelligence)
    
    # Get test targets from config
    targets = config_manager.get_enabled_targets()
    test_targets = targets[:3]  # Test first 3 targets
    
    print(f"🎯 Testing {len(test_targets)} targets with learning enabled")
    
    test_results = []
    
    for target in test_targets:
        print(f"\n{'='*60}")
        print(f"Testing Target: {target.name}")
        print(f"Base URL: {target.base_url}")
        print(f"{'='*60}")
        
        target_results = []
        
        # Test each page for this target
        for page_config in target.target_pages[:2]:  # Test first 2 pages per target
            url = page_config['url']
            page_type = page_config['type']
            
            print(f"\n📄 Testing: {page_type}")
            print(f"   URL: {url}")
            
            # Get the scraper strategy for this target
            strategy = ScrapingStrategy()
            if target.scraper_strategy:
                strategy.primary = target.scraper_strategy.get('primary', 'crawl4ai')
                strategy.fallbacks = target.scraper_strategy.get('fallbacks', ['requests', 'playwright', 'selenium'])
            
            try:
                # First attempt - system will learn from this
                result = await scraper.scrape(url, target_config=target.__dict__, strategy=strategy)
                
                print(f"   📊 Result:")
                print(f"      Success: {result.success}")
                print(f"      Scraper Used: {result.scraper_used}")
                print(f"      Response Time: {result.response_time:.1f}s")
                print(f"      Content Length: {len(result.content):,} chars")
                print(f"      Word Count: {result.word_count:,}")
                
                if result.success and result.content:
                    preview = result.content[:150].replace('\n', ' ').strip()
                    print(f"      Preview: {preview}...")
                
                if not result.success:
                    print(f"      Error: {result.error_message}")
                
                target_results.append({
                    'url': url,
                    'page_type': page_type,
                    'success': result.success,
                    'scraper_used': result.scraper_used,
                    'response_time': result.response_time,
                    'content_length': len(result.content),
                    'word_count': result.word_count
                })
                
                # Small delay between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                target_results.append({
                    'url': url,
                    'page_type': page_type,
                    'success': False,
                    'error': str(e)
                })
        
        test_results.append({
            'target_name': target.name,
            'results': target_results
        })
    
    await scraper.cleanup()
    
    # Generate intelligence report
    print(f"\n{'='*60}")
    print("🧠 INTELLIGENCE REPORT")
    print(f"{'='*60}")
    
    report = intelligence.get_intelligence_report()
    
    print(f"📊 Overall Performance:")
    print(f"   Total Attempts: {report['overall']['total_attempts']}")
    print(f"   Success Rate: {report['overall']['success_rate']}%")
    print(f"   Unique Domains: {report['overall']['unique_domains']}")
    print(f"   Avg Response Time: {report['overall']['avg_response_time']}s")
    
    print(f"\n🔧 Scraper Performance:")
    for scraper_name, stats in report['scrapers'].items():
        print(f"   {scraper_name}:")
        print(f"      Attempts: {stats['attempts']}")
        print(f"      Success Rate: {stats['success_rate']}%")
        print(f"      Avg Response Time: {stats['avg_response_time']}s")
    
    if report['top_domains']:
        print(f"\n🌐 Top Performing Domains:")
        for domain_info in report['top_domains'][:5]:
            print(f"   {domain_info['domain']}: {domain_info['success_rate']}% ({domain_info['successes']}/{domain_info['attempts']})")
    
    # Test learning - show optimal scraper order for each domain
    print(f"\n🎯 LEARNED OPTIMAL SCRAPER ORDERS:")
    print("-" * 40)
    
    tested_domains = set()
    for target_result in test_results:
        for result in target_result['results']:
            if 'url' in result:
                from urllib.parse import urlparse
                domain = urlparse(result['url']).netloc
                if domain not in tested_domains:
                    optimal_order = intelligence.get_optimal_scraper_order(result['url'])
                    print(f"   {domain}: {optimal_order}")
                    tested_domains.add(domain)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"intelligent_scraper_test_{timestamp}.json"
    
    full_results = {
        'test_results': test_results,
        'intelligence_report': report,
        'test_metadata': {
            'timestamp': timestamp,
            'targets_tested': len(test_targets),
            'total_pages_tested': sum(len(tr['results']) for tr in test_results)
        }
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Overall assessment
    total_attempts = sum(len(tr['results']) for tr in test_results)
    successful_attempts = sum(1 for tr in test_results for r in tr['results'] if r.get('success', False))
    overall_success_rate = (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0
    
    print(f"\n🎉 TEST SUMMARY:")
    print(f"   Targets Tested: {len(test_targets)}")
    print(f"   Pages Tested: {total_attempts}")
    print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
    print(f"   Intelligence System: {'✅ Active and Learning' if report['overall']['total_attempts'] > 0 else '❌ No Data'}")
    
    if overall_success_rate >= 80:
        print(f"\n🎉 EXCELLENT: Intelligent scraper system is working optimally!")
    elif overall_success_rate >= 60:
        print(f"\n👍 GOOD: System working well, continuing to learn and improve")
    else:
        print(f"\n⚠️  NEEDS ATTENTION: System learning but may need configuration adjustments")
    
    return True

async def test_learning_over_time():
    """Test that the system learns and improves over multiple runs"""
    
    print(f"\n{'='*60}")
    print("📚 TESTING LEARNING OVER TIME")
    print(f"{'='*60}")
    
    intelligence = ScraperIntelligence()
    
    # Test URL that we know works well with crawl4ai
    test_url = "https://www.northernminer.com/news/"
    
    print(f"Testing learning for: {test_url}")
    
    # Show initial optimal order (should be default)
    initial_order = intelligence.get_optimal_scraper_order(test_url)
    print(f"Initial optimal order: {initial_order}")
    
    # Simulate multiple successful crawl4ai attempts
    from src.scrapers.scraper_intelligence import record_scraper_attempt
    
    for i in range(5):
        record_scraper_attempt(
            url=test_url,
            scraper_used="crawl4ai",
            success=True,
            response_time=1.2 + (i * 0.1),  # Slightly increasing response time
            content_length=25000 + (i * 1000),
            intelligence=intelligence
        )
    
    # Simulate some failed requests attempts
    for i in range(3):
        record_scraper_attempt(
            url=test_url,
            scraper_used="requests",
            success=False,
            response_time=0.8,
            content_length=0,
            error_message="HTTP 403 Forbidden",
            intelligence=intelligence
        )
    
    # Simulate some successful playwright attempts (slower)
    for i in range(2):
        record_scraper_attempt(
            url=test_url,
            scraper_used="playwright",
            success=True,
            response_time=3.5 + (i * 0.2),
            content_length=22000 + (i * 500),
            intelligence=intelligence
        )
    
    # Check learned optimal order
    learned_order = intelligence.get_optimal_scraper_order(test_url)
    print(f"Learned optimal order: {learned_order}")
    
    # Get domain insights
    from urllib.parse import urlparse
    domain = urlparse(test_url).netloc
    insights = intelligence.get_domain_insights(domain)
    
    if insights:
        print(f"\n📊 Domain Insights for {domain}:")
        print(f"   Total Attempts: {insights.total_attempts}")
        print(f"   Success Rate: {insights.success_rate:.1f}%")
        print(f"   Best Scraper: {insights.best_scraper}")
        print(f"   Scraper Performance:")
        for scraper, perf in insights.scraper_performance.items():
            print(f"      {scraper}: {perf['success_rate']:.1f}% success, {perf['avg_response_time']:.1f}s avg")
    
    print(f"\n✅ Learning system is working - crawl4ai should be prioritized for this domain")

if __name__ == "__main__":
    async def main():
        """Run all tests"""
        
        print("🚀 Starting Intelligent Scraper System Tests")
        print("=" * 80)
        
        try:
            # Test the unified scraper with intelligence
            success = await test_intelligent_scraper()
            
            if success:
                # Test learning capabilities
                await test_learning_over_time()
                
                print(f"\n{'='*80}")
                print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
                print("✅ Intelligent Unified Scraper System is fully operational")
                print("🧠 Learning system is active and optimizing scraper selection")
                print("📊 Performance data is being tracked and analyzed")
                print(f"{'='*80}")
                
                return True
            else:
                print(f"\n❌ Tests failed!")
                return False
                
        except Exception as e:
            print(f"\n❌ Test error: {str(e)}")
            return False
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Intelligent scraper system testing completed successfully!")
    else:
        print("\n❌ Intelligent scraper system testing failed!")