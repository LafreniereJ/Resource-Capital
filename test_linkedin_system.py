#!/usr/bin/env python3
"""
Test the complete LinkedIn System (7-day automation)
Automatically detects weekdays vs weekends and routes appropriately
"""

import sys
import os
sys.path.append('src')

from datetime import datetime

def main():
    """Test the complete LinkedIn automation system with weekend detection"""
    print("🚀 Testing Complete 7-Day LinkedIn System")
    print("=" * 60)
    
    # Import after sys.path setup
    from src.linkedin.daily_linkedin_automation import DailyLinkedInAutomation
    from src.linkedin.weekend_automation import WeekendAutomation
    
    today = datetime.now()
    weekday = today.weekday()  # Monday = 0, Sunday = 6
    
    print(f"📅 Today: {today.strftime('%A, %B %d, %Y')}")
    
    try:
        if weekday in [5, 6]:  # Saturday or Sunday
            print("🎯 Weekend detected - running weekend content automation")
            
            weekend_automation = WeekendAutomation()
            content = weekend_automation.run_weekend_automation()
            
            if content:
                print(f"\n🎉 Weekend automation completed successfully!")
                print(f"📊 Confidence Score: {content.confidence_score:.1f}/100")
                print(f"📱 {content.day_type.title()} post ready for LinkedIn!")
            else:
                print("ℹ️ No weekend content generated")
        else:
            print("📊 Weekday detected - running daily market intelligence")
            
            automation = DailyLinkedInAutomation()
            intelligence = automation.run_daily_automation(max_stocks=30)  # Small sample for testing
            
            print(f"\n🎉 Daily automation completed successfully!")
            print(f"📊 Confidence Score: {intelligence.confidence_score:.1f}/100")
            print(f"📱 Daily brief ready for LinkedIn!")
        
        print(f"\n✅ Complete 7-Day System Test Successful!")
        print("📊 System automatically routes weekdays → daily briefs")
        print("📊 System automatically routes weekends → weekend content")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()