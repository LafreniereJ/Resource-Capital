#!/usr/bin/env python3
"""
Test Web Scraper
Test the breaking news monitoring and web scraping functionality
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.append('src')

from intelligence.breaking_news_monitor import BreakingNewsMonitor

async def test_individual_sources():
    """Test individual RSS sources"""
    print("🧪 TESTING INDIVIDUAL RSS SOURCES")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    # Test specific sources one by one
    test_sources = {
        "reuters_commodities": {
            "rss": "https://feeds.reuters.com/reuters/businessNews",
            "type": "rss",
            "priority_weight": 1.0
        },
        "mining_com": {
            "rss": "https://www.mining.com/feed/",
            "type": "rss", 
            "priority_weight": 0.9
        },
        "kitco_news": {
            "rss": "https://www.kitco.com/rss/KitcoNews.xml",
            "type": "rss",
            "priority_weight": 0.8
        }
    }
    
    for source_name, source_config in test_sources.items():
        print(f"\n🔍 Testing {source_name}...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                events = await monitor.monitor_rss_source(session, source_name, source_config, hours_back=24)
                
                print(f"✅ {source_name}: Found {len(events)} events")
                
                # Show sample events
                for i, event in enumerate(events[:3]):
                    print(f"   {i+1}. {event.headline[:80]}...")
                    print(f"      Priority: {event.priority_score:.1f} | Impact: {event.impact_level}")
                
        except Exception as e:
            print(f"❌ {source_name}: Error - {e}")

async def test_full_monitoring():
    """Test full monitoring system"""
    print("\n🚨 TESTING FULL BREAKING NEWS MONITORING")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    try:
        # Monitor all sources for breaking news
        events = await monitor.monitor_all_sources(hours_back=6)
        
        print(f"\n📊 MONITORING RESULTS:")
        print(f"   Total high-priority events: {len(events)}")
        
        if events:
            print(f"\n🏆 TOP BREAKING NEWS EVENTS:")
            for i, event in enumerate(events[:5], 1):
                print(f"   {i}. {event.headline}")
                print(f"      Source: {event.source} | Priority: {event.priority_score:.1f}")
                print(f"      Impact: {event.impact_level} | Canadian: {event.canadian_relevance:.1f}")
                if event.keywords:
                    print(f"      Keywords: {', '.join(event.keywords[:5])}")
                print()
        
        # Test database storage
        print(f"💾 Testing database storage...")
        recent_events = monitor.get_recent_breaking_news(hours_back=6, min_priority=50.0)
        print(f"   Events stored in database: {len(recent_events)}")
        
        return events
        
    except Exception as e:
        print(f"❌ Full monitoring error: {e}")
        return []

async def test_priority_scoring():
    """Test priority scoring with sample headlines"""
    print("\n🎯 TESTING PRIORITY SCORING SYSTEM")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    # Sample headlines to test priority scoring
    test_headlines = [
        "Trump announces 25% tariff on Canadian copper imports",
        "Copper prices plunge 5% on trade war fears",
        "Agnico Eagle reports Q3 earnings beat",
        "Small exploration company announces drill results",
        "Bank of Canada raises interest rates by 0.25%",
        "China announces stimulus package for manufacturing",
        "Newmont Corporation acquires junior gold miner",
        "Canadian mining regulations update announced"
    ]
    
    from intelligence.breaking_news_monitor import BreakingNewsEvent
    from datetime import datetime
    
    print("📝 Testing priority scoring on sample headlines:")
    
    for headline in test_headlines:
        # Create test event
        event = BreakingNewsEvent(
            id="",
            headline=headline,
            summary=headline,
            url="https://test.com",
            source="test_source",
            published=datetime.now()
        )
        
        # Analyze priority
        monitor.analyze_event_priority(event, source_weight=1.0)
        
        print(f"   Priority {event.priority_score:5.1f}: {headline}")
        if event.keywords:
            print(f"                 Keywords: {', '.join(event.keywords)}")

async def test_news_summary_generation():
    """Test breaking news summary generation"""
    print("\n📄 TESTING NEWS SUMMARY GENERATION")
    print("=" * 60)
    
    monitor = BreakingNewsMonitor()
    
    try:
        summary = await monitor.generate_breaking_news_summary(hours_back=12)
        
        print("📊 BREAKING NEWS SUMMARY:")
        print(f"   Total events: {summary.get('total_events', 0)}")
        print(f"   High priority events: {summary.get('high_priority_events', 0)}")
        print(f"   Critical events: {summary.get('critical_events', 0)}")
        
        if 'top_events' in summary:
            print(f"\n🏆 TOP EVENTS:")
            for event in summary['top_events'][:3]:
                print(f"   • {event.get('headline', 'No headline')}")
                print(f"     Priority: {event.get('priority_score', 0):.1f}")
        
        if 'commodity_impacts' in summary:
            print(f"\n💎 COMMODITY IMPACTS:")
            for commodity, impact in summary['commodity_impacts'].items():
                print(f"   {commodity}: {impact}")
        
    except Exception as e:
        print(f"❌ Summary generation error: {e}")

async def main():
    """Main test function"""
    print("🔬 BREAKING NEWS WEB SCRAPER TESTING")
    print("=" * 80)
    
    # Test individual sources first
    await test_individual_sources()
    
    # Test priority scoring
    await test_priority_scoring()
    
    # Test full monitoring
    events = await test_full_monitoring()
    
    # Test summary generation
    await test_news_summary_generation()
    
    print("\n✅ WEB SCRAPER TESTING COMPLETE!")
    print("=" * 80)
    
    if events:
        print(f"🎯 Successfully monitored {len(events)} high-priority breaking news events")
        print("💾 Events saved to database for intelligence analysis")
    else:
        print("⚠️ No high-priority events found in current timeframe")

if __name__ == "__main__":
    asyncio.run(main())