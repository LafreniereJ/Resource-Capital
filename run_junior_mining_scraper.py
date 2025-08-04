#!/usr/bin/env python3
"""
Junior Mining Network Scraper Execution Script
Scrapes the requested Junior Mining Network sites for August 4, 2025
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scrapers.specialized.junior_mining_network_scraper import JuniorMiningNetworkScraper

async def main():
    """Run the Junior Mining Network scraper"""
    
    print("🏗️ Junior Mining Network Intelligence Scraper")
    print("=" * 60)
    print("Target Sites:")
    print("1. https://www.juniorminingnetwork.com/")
    print("2. https://www.juniorminingnetwork.com/heat-map.html")
    print("3. https://www.juniorminingnetwork.com/market-data.html")
    print("=" * 60)
    print()
    
    # Initialize scraper with specific output directory
    scraper = JuniorMiningNetworkScraper(data_dir="reports/2025-08-04")
    
    try:
        # Execute the scraping
        results = await scraper.scrape_all_junior_mining_sites()
        
        # Display final results
        print("\n" + "=" * 60)
        print("🎯 SCRAPING COMPLETE - FINAL RESULTS")
        print("=" * 60)
        
        perf_summary = results['performance_summary']
        
        print(f"✅ Sites Successful: {perf_summary['sites_successful']}/{perf_summary['sites_attempted']}")
        print(f"📊 Success Rate: {perf_summary['success_rate']:.1f}%")
        print(f"🏢 Companies Found: {perf_summary['total_companies_found']}")
        print(f"📰 News Items: {perf_summary['total_news_items']}")
        print(f"🏆 Data Quality Score: {perf_summary['data_quality_score']}/100")
        
        if perf_summary.get('scraping_duration_seconds'):
            print(f"⏱️ Total Duration: {perf_summary['scraping_duration_seconds']:.1f} seconds")
        
        if perf_summary.get('average_site_duration'):
            print(f"📈 Avg Site Duration: {perf_summary['average_site_duration']:.1f} seconds")
        
        print()
        
        # Show top companies found
        if results['consolidated_data']['companies']:
            print("🏢 TOP COMPANIES DISCOVERED:")
            for i, (symbol, company) in enumerate(list(results['consolidated_data']['companies'].items())[:5]):
                name = company.get('name', 'Unknown')
                sources = len(company.get('data_sources', []))
                print(f"   {i+1}. {name} ({symbol}) - Found in {sources} source(s)")
        
        # Show recent news
        if results['consolidated_data']['news_items']:
            print("\n📰 RECENT NEWS HEADLINES:")
            for i, news in enumerate(results['consolidated_data']['news_items'][:3]):
                headline = news.get('headline', 'No headline')[:80]
                relevance = news.get('relevance_score', 0)
                print(f"   {i+1}. {headline}... (relevance: {relevance})")
        
        # Show any errors
        if results.get('errors'):
            print(f"\n⚠️ ERRORS ENCOUNTERED ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   • {error}")
        
        print("\n💾 Output files created:")
        print("   • reports/2025-08-04/mining_companies_data.json")
        print("   • reports/2025-08-04/mining_companies_summary.txt")
        print("   • logs/scraper_performance/junior_mining_network_session_*.json")
        
        print(f"\n✅ Junior Mining Network scraping completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup resources
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())