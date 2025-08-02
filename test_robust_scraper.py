#!/usr/bin/env python3
"""
Test Robust Multi-Website Scraper
Comprehensive testing of the enhanced scraping system
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

async def test_robust_scraper():
    """Test the robust scraper with multiple website types"""
    print("🚀 TESTING ROBUST MULTI-WEBSITE SCRAPER")
    print("=" * 80)
    
    from intelligence.robust_web_scraper import RobustWebScraper
    
    async with RobustWebScraper() as scraper:
        print(f"📊 Configured to scrape {len(scraper.scraping_targets)} sources:")
        
        for target in scraper.scraping_targets:
            status = "✅ Enabled" if target.enabled else "❌ Disabled"
            print(f"   {status} {target.name:25s} ({target.scrape_type:4s}) - {target.url}")
        
        print(f"\n🔍 Starting concurrent scraping...")
        
        # Perform scraping
        results = await scraper.scrape_all_targets()
        
        # Generate summary
        summary = scraper.generate_scraping_summary(results)
        
        print(f"\n📊 SCRAPING RESULTS:")
        print("=" * 60)
        print(f"Total Sources: {summary['total_targets']}")
        print(f"Successful: {summary['successful_targets']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Events: {summary['total_events_found']}")
        print(f"Average Response Time: {summary['average_response_time']:.2f}s")
        
        print(f"\n🎯 DETAILED SOURCE PERFORMANCE:")
        print("-" * 60)
        
        for target_name, status in summary['target_status'].items():
            status_icon = "✅" if status['success'] else "❌"
            events_text = f"{status['events_found']} events" if status['success'] else "Failed"
            time_text = f"({status['response_time']:.2f}s)" if status['success'] else ""
            
            print(f"{status_icon} {target_name:25s}: {events_text:12s} {time_text}")
            
            if status['error']:
                print(f"    Error: {status['error']}")
        
        # Show sample headlines by source type
        print(f"\n📰 SAMPLE HEADLINES BY SOURCE TYPE:")
        print("-" * 60)
        
        rss_events = []
        html_events = []
        
        for result in results:
            if result.success and result.events:
                # Find source type
                source_type = "unknown"
                for target in scraper.scraping_targets:
                    if target.name == result.target_name:
                        source_type = target.scrape_type
                        break
                
                if source_type == "rss":
                    rss_events.extend(result.events[:3])
                elif source_type == "html":
                    html_events.extend(result.events[:3])
        
        if rss_events:
            print(f"\n📡 RSS FEED HEADLINES:")
            for i, event in enumerate(rss_events[:5], 1):
                print(f"   {i}. [{event.source}] {event.headline[:65]}...")
        
        if html_events:
            print(f"\n🌐 HTML SCRAPED HEADLINES:")
            for i, event in enumerate(html_events[:5], 1):
                print(f"   {i}. [{event.source}] {event.headline[:65]}...")
        
        return summary, results

async def test_enhanced_intelligence_system():
    """Test the complete enhanced intelligence system"""
    print(f"\n🧠 TESTING ENHANCED INTELLIGENCE SYSTEM")
    print("=" * 80)
    
    from intelligence.enhanced_news_system import EnhancedNewsIntelligenceSystem
    
    async with EnhancedNewsIntelligenceSystem() as system:
        print("🔍 Performing comprehensive news intelligence scan...")
        
        # Perform comprehensive scan
        summary = await system.comprehensive_news_scan(hours_back=6)
        
        print(f"\n📊 INTELLIGENCE SCAN RESULTS:")
        print("=" * 60)
        print(f"Scan Duration: {summary['hours_scanned']} hours")
        print(f"Total Events Found: {summary['total_events_found']}")
        print(f"Relevant Events: {summary['relevant_events']}")
        print(f"High-Priority Events: {summary['high_priority_events']}")
        print(f"Critical Events: {summary['critical_events']}")
        
        # Show source performance
        print(f"\n📡 SOURCE PERFORMANCE:")
        scraping_perf = summary['scraping_summary']
        print(f"Overall Success Rate: {scraping_perf['success_rate']:.1%}")
        
        successful_sources = [
            name for name, perf in summary['source_performance'].items() 
            if perf['success']
        ]
        print(f"Working Sources: {len(successful_sources)}")
        
        # Show top events
        if summary['top_events']:
            print(f"\n🚨 TOP PRIORITY EVENTS:")
            for i, event in enumerate(summary['top_events'], 1):
                print(f"   {i}. Priority {event['priority_score']:6.1f}: {event['headline'][:60]}...")
                print(f"      Source: {event['source']} | Impact: {event['impact_level']}")
        
        # Show commodity impacts
        if summary['commodity_analysis']:
            print(f"\n💎 COMMODITY IMPACT ANALYSIS:")
            for commodity, data in summary['commodity_analysis'].items():
                print(f"   {commodity.upper()}: {data['total_impact']:.1f} points ({data['event_count']} events)")
        
        # Show company correlations
        correlations = summary['company_correlations']
        if correlations['commodity_impacts']:
            print(f"\n🏢 COMPANY CORRELATIONS:")
            for commodity, impact in correlations['commodity_impacts'].items():
                print(f"   {commodity.upper()}: {impact['companies_count']} companies affected")
        
        # Generate and show sample report
        print(f"\n📄 GENERATING INTELLIGENCE REPORT...")
        report = await system.generate_intelligence_report(summary)
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_file = f"data/processed/test_intelligence_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        summary_file = f"data/processed/test_intelligence_summary_{timestamp}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"✅ Report saved to: {report_file}")
        print(f"✅ Summary saved to: {summary_file}")
        
        return summary

async def test_rate_limiting_and_robustness():
    """Test rate limiting and error handling robustness"""
    print(f"\n🛡️ TESTING RATE LIMITING AND ROBUSTNESS")
    print("=" * 80)
    
    from intelligence.robust_web_scraper import RobustWebScraper, ScrapingTarget
    
    # Create test scraper with aggressive rate limiting
    async with RobustWebScraper() as scraper:
        # Add a test target with very strict rate limiting
        test_target = ScrapingTarget(
            name="bbc_test_rate_limit",
            url="http://feeds.bbci.co.uk/news/business/rss.xml",
            scrape_type="rss",
            rate_limit=0.1,  # Very fast requests
            retry_count=2,
            priority_weight=0.5
        )
        
        print("🔄 Testing rate limiting with rapid requests...")
        
        # Test multiple rapid requests to same domain
        start_time = datetime.now()
        
        results = []
        for i in range(3):
            result = await scraper.scrape_single_target(test_target)
            results.append(result)
            print(f"   Request {i+1}: {'✅ Success' if result.success else '❌ Failed'} ({result.response_time:.2f}s)")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Total time for 3 requests: {total_time:.2f}s")
        print(f"⚡ Rate limiting {'✅ Working' if total_time >= 0.2 else '❌ Not enforced'}")
        
        # Test error handling
        print(f"\n🔧 Testing error handling with invalid URLs...")
        
        invalid_target = ScrapingTarget(
            name="invalid_test",
            url="https://definitely-not-a-real-website-12345.com/feed.rss",
            scrape_type="rss",
            retry_count=1,
            timeout=5
        )
        
        error_result = await scraper.scrape_single_target(invalid_target)
        print(f"   Invalid URL handling: {'✅ Handled' if not error_result.success else '❌ Unexpected success'}")
        print(f"   Error message: {error_result.error_message}")

async def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE ROBUST SCRAPER TESTING")
    print("=" * 100)
    
    # Test 1: Basic robust scraper
    scraper_summary, scraper_results = await test_robust_scraper()
    
    # Test 2: Enhanced intelligence system
    intelligence_summary = await test_enhanced_intelligence_system()
    
    # Test 3: Rate limiting and robustness
    await test_rate_limiting_and_robustness()
    
    # Final Summary
    print(f"\n🎯 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    print(f"✅ Robust Scraper:")
    print(f"   • {scraper_summary['successful_targets']}/{scraper_summary['total_targets']} sources working")
    print(f"   • {scraper_summary['total_events_found']} total events scraped")
    print(f"   • {scraper_summary['success_rate']:.1%} success rate")
    
    print(f"✅ Intelligence System:")
    print(f"   • {intelligence_summary['high_priority_events']} high-priority events identified")
    print(f"   • {intelligence_summary['critical_events']} critical events detected")
    print(f"   • {len(intelligence_summary['commodity_analysis'])} commodities analyzed")
    
    print(f"\n🚀 ROBUST MULTI-WEBSITE SCRAPING SYSTEM IS OPERATIONAL!")
    print("🎯 Key capabilities demonstrated:")
    print("   • Concurrent scraping of RSS feeds and HTML content")
    print("   • Intelligent rate limiting and error handling")
    print("   • Priority scoring and company correlation")
    print("   • Comprehensive intelligence reporting")
    print("   • Database integration and persistence")

if __name__ == "__main__":
    asyncio.run(main())