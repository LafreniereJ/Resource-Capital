#!/usr/bin/env python3
"""
Test script for targeted metal prices scraping
For August 4, 2025 mining intelligence collection
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from scrapers.specialized.metal_prices_scraper import scrape_target_metal_sites


async def main():
    """Run the targeted metal prices scraping"""
    
    print("🎯 METAL PRICES INTELLIGENCE SCRAPING - AUGUST 4, 2025")
    print("=" * 60)
    print("Target Sites:")
    print("  1. Trading Economics Commodities")
    print("  2. Daily Metal Price")
    print("  3. Kitco Precious Metals")
    print("  4. Kitco Base Metals")
    print()
    print("Target Commodities: gold, silver, copper, platinum, palladium, nickel, zinc, lithium, uranium, cobalt")
    print("=" * 60)
    
    try:
        # Run the targeted scraping
        results = await scrape_target_metal_sites()
        
        print("\n" + "=" * 60)
        print("📊 SCRAPING COMPLETED - RESULTS SUMMARY")
        print("=" * 60)
        
        # Display summary
        summary = results.get('summary', {})
        scraping_session = summary.get('scraping_session', {})
        data_quality = summary.get('data_quality', {})
        performance_metrics = summary.get('performance_metrics', {})
        
        print(f"🕒 Scraping Duration: {scraping_session.get('total_duration', 0):.1f} seconds")
        print(f"🌐 Sites Attempted: {scraping_session.get('sites_attempted', 0)}")
        print(f"✅ Sites Successful: {scraping_session.get('sites_successful', 0)}")
        print(f"📈 Commodities Found: {data_quality.get('commodities_found', 0)}")
        print(f"🎯 Consensus Prices: {data_quality.get('consensus_prices', 0)}")
        print(f"⚡ Average Response Time: {performance_metrics.get('average_response_time', 0):.1f}s")
        
        if performance_metrics.get('fastest_site'):
            print(f"🏃 Fastest Site: {performance_metrics['fastest_site']}")
        if performance_metrics.get('most_data_rich_site'):
            print(f"📊 Most Data Rich: {performance_metrics['most_data_rich_site']}")
        
        # Display market highlights
        market_highlights = summary.get('market_highlights', [])
        if market_highlights:
            print(f"\n🔥 MARKET HIGHLIGHTS:")
            for highlight in market_highlights:
                print(f"   • {highlight}")
        
        # Display commodity consensus prices
        market_analysis = results.get('market_analysis', {})
        price_consensus = market_analysis.get('price_consensus', {})
        
        if price_consensus:
            print(f"\n💰 COMMODITY PRICE CONSENSUS:")
            for commodity, consensus in price_consensus.items():
                avg_price = consensus.get('average_price', 0)
                avg_change = consensus.get('average_change', 0)
                sources = consensus.get('sources_count', 0)
                change_direction = "↑" if avg_change > 0 else "↓" if avg_change < 0 else "→"
                
                print(f"   {commodity.title()}: ${avg_price:.2f} {change_direction} {avg_change:+.1f}% (from {sources} sources)")
        
        # Market sentiment
        sentiment = market_analysis.get('market_sentiment', 'neutral')
        sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
        print(f"\n{sentiment_emoji} Market Sentiment: {sentiment.title()}")
        
        # Investment implications
        implications = market_analysis.get('investment_implications', [])
        if implications:
            print(f"\n💡 INVESTMENT IMPLICATIONS:")
            for implication in implications:
                print(f"   • {implication}")
        
        # Display errors if any
        errors = results.get('errors', [])
        if errors:
            print(f"\n⚠️  SCRAPING CHALLENGES:")
            for error in errors:
                print(f"   • {error}")
        
        # Performance log
        performance_log = results.get('performance_log', [])
        if performance_log:
            print(f"\n📋 DETAILED PERFORMANCE LOG:")
            for entry in performance_log:
                status = "✅" if entry.get('success', False) else "❌"
                site_name = entry.get('display_name', 'Unknown')
                response_time = entry.get('response_time', 0)
                commodities = entry.get('commodities_found', 0)
                
                if entry.get('success', False):
                    print(f"   {status} {site_name}: {response_time:.1f}s, {commodities} commodities")
                else:
                    error = entry.get('error', 'Unknown error')
                    print(f"   {status} {site_name}: Failed - {error}")
        
        print(f"\n💾 Data saved to: /Projects/Resource Capital/reports/2025-08-04/metal_prices_data.json")
        print("=" * 60)
        print("🎉 Metal prices intelligence collection completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Critical error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())