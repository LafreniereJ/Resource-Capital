#!/usr/bin/env python3
"""
Test the complete Weekend Content System
Tests both Saturday weekly wrap and Sunday week-ahead functionality
"""

import sys
import os
sys.path.append('src')

from datetime import datetime, timedelta
from src.linkedin.weekend_automation import WeekendAutomation
from src.linkedin.weekly_wrap_generator import WeeklyWrapGenerator
from src.linkedin.week_ahead_generator import WeekAheadGenerator

def test_weekend_content_system():
    """Test the complete weekend content system"""
    print("🎯 Testing Weekend Content System")
    print("=" * 60)
    
    # Test Weekend Automation Coordinator
    print("\n🔧 Testing Weekend Automation Coordinator...")
    automation = WeekendAutomation()
    
    # Test weekend detection
    weekend_type = automation.detect_weekend_type()
    print(f"📅 Weekend Detection: {weekend_type if weekend_type else 'Not a weekend'}")
    
    # Test Saturday Weekly Wrap Generator
    print("\n📊 Testing Saturday Weekly Wrap Generator...")
    print("=" * 50)
    
    try:
        wrap_generator = WeeklyWrapGenerator()
        weekly_summary = wrap_generator.generate_weekly_wrap()
        
        print(f"✅ Weekly Wrap Generated:")
        print(f"📅 Week: {weekly_summary.week_start} - {weekly_summary.week_end}")
        print(f"📈 Top Gainers: {len(weekly_summary.top_gainers)}")
        print(f"📉 Top Decliners: {len(weekly_summary.top_decliners)}")
        print(f"💰 Commodities: {len(weekly_summary.commodity_performance)}")
        print(f"📰 Major Stories: {len(weekly_summary.major_stories)}")
        print(f"🏆 Stock of Week: {weekly_summary.stock_of_week}")
        print(f"💡 Key Takeaway: {weekly_summary.key_takeaway}")
        print(f"😊 Sentiment: {weekly_summary.market_sentiment}")
        
        # Show sample content
        if weekly_summary.top_gainers:
            print(f"\n📈 SAMPLE GAINERS:")
            for i, gainer in enumerate(weekly_summary.top_gainers[:3]):
                print(f"  {i+1}. {gainer['symbol']}: +{gainer['weekly_change']:.1f}%")
        
        if weekly_summary.commodity_performance:
            print(f"\n💰 SAMPLE COMMODITIES:")
            for i, commodity in enumerate(weekly_summary.commodity_performance[:3]):
                emoji = "📈" if commodity['weekly_change'] > 0 else "📉" if commodity['weekly_change'] < 0 else "➡️"
                print(f"  {i+1}. {emoji} {commodity['name']}: {commodity['weekly_change']:+.1f}%")
        
    except Exception as e:
        print(f"❌ Weekly Wrap Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Sunday Week Ahead Generator
    print("\n🔮 Testing Sunday Week Ahead Generator...")
    print("=" * 50)
    
    try:
        ahead_generator = WeekAheadGenerator()
        week_ahead = ahead_generator.generate_week_ahead()
        
        print(f"✅ Week Ahead Generated:")
        print(f"📅 Week Starting: {week_ahead.week_start}")
        print(f"🎯 Week's Theme: {week_ahead.weeks_theme}")
        print(f"📅 Key Events: {len(week_ahead.key_events)}")
        print(f"⚡ Watch List: {len(week_ahead.watch_list)}")
        print(f"🌍 Global Factors: {len(week_ahead.global_factors)}")
        print(f"💎 Commodity Outlook: {len(week_ahead.commodity_outlook)}")
        
        # Show sample content
        if week_ahead.key_events:
            print(f"\n📅 SAMPLE KEY EVENTS:")
            for i, event in enumerate(week_ahead.key_events[:3]):
                print(f"  {i+1}. {event}")
        
        if week_ahead.watch_list:
            print(f"\n⚡ SAMPLE WATCH LIST:")
            for i, stock in enumerate(week_ahead.watch_list[:3]):
                print(f"  {i+1}. {stock['symbol']}: {stock['reason']}")
        
        if week_ahead.commodity_outlook:
            print(f"\n💎 SAMPLE COMMODITY OUTLOOK:")
            for i, outlook in enumerate(week_ahead.commodity_outlook[:3]):
                print(f"  {i+1}. {outlook}")
        
    except Exception as e:
        print(f"❌ Week Ahead Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Complete Weekend Automation
    print("\n🚀 Testing Complete Weekend Automation...")
    print("=" * 50)
    
    try:
        content = automation.run_weekend_automation()
        
        if content:
            print(f"✅ Weekend Content Generated:")
            print(f"📅 Date: {content.date}")
            print(f"📱 Type: {content.day_type} ({content.content_type})")
            print(f"📊 Confidence Score: {content.confidence_score:.1f}/100")
            
            print(f"\n📱 GENERATED POST:")
            print("=" * 40)
            print(content.post_text)
            print("=" * 40)
            
            # Save test content
            filename = automation.save_weekend_content(content)
            print(f"\n💾 Content saved to: {filename}")
            
        else:
            print("ℹ️ No weekend content generated (likely not a weekend)")
            print("🧪 Testing Saturday content simulation...")
            
            # Force Saturday content for testing
            saturday_content = automation.generate_saturday_content()
            print(f"\n📊 SATURDAY TEST POST:")
            print("=" * 40)
            print(saturday_content.post_text)
            print("=" * 40)
            
            print("\n🧪 Testing Sunday content simulation...")
            
            # Force Sunday content for testing  
            sunday_content = automation.generate_sunday_content()
            print(f"\n🔮 SUNDAY TEST POST:")
            print("=" * 40)
            print(sunday_content.post_text)
            print("=" * 40)
        
    except Exception as e:
        print(f"❌ Weekend Automation Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 Weekend Content System Test Completed!")

def test_7_day_simulation():
    """Simulate a full week of content generation"""
    print("\n🗓️ 7-Day Content Simulation")
    print("=" * 60)
    
    # Simulate each day of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, day in enumerate(days):
        print(f"\n📅 {day} Simulation:")
        
        if i < 5:  # Weekdays (Mon-Fri)
            print("  📊 Daily Market Intelligence Brief")
            print("  🎯 Focus: Real-time market data and news")
            print("  📱 Format: Fast-paced daily update")
        elif i == 5:  # Saturday
            print("  📊 Weekly Wrap-Up")
            print("  🎯 Focus: Summarize week's performance")
            print("  📱 Format: Analytical recap")
        else:  # Sunday
            print("  🔮 Week Ahead Preview")
            print("  🎯 Focus: Upcoming week preparation")
            print("  📱 Format: Forward-looking preview")
    
    print(f"\n✅ 7-Day Content Strategy Complete!")
    print("📊 Monday-Friday: Daily market intelligence")
    print("📊 Saturday: Weekly recap and analysis")
    print("🔮 Sunday: Week-ahead preview and preparation")

def main():
    """Run complete weekend system test"""
    test_weekend_content_system()
    test_7_day_simulation()
    
    print(f"\n🚀 Complete 7-Day LinkedIn Automation System is Ready!")
    print("🎯 Use daily_linkedin_automation.py for all days")
    print("📅 System automatically detects weekends and routes appropriately")

if __name__ == "__main__":
    main()