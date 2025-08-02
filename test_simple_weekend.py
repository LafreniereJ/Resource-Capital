#!/usr/bin/env python3
"""
Simple Weekend Content Test
Tests weekend content generation without heavy stock analysis
"""

import sys
import os
sys.path.append('src')

from datetime import datetime
from src.linkedin.weekend_automation import WeekendAutomation

def test_weekend_automation():
    """Test weekend automation with minimal data"""
    print("🎯 Simple Weekend Content Test")
    print("=" * 50)
    
    automation = WeekendAutomation()
    
    # Test weekend detection
    weekend_type = automation.detect_weekend_type()
    print(f"📅 Today: {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"🎯 Weekend Type: {weekend_type if weekend_type else 'Weekday - no weekend content'}")
    
    if weekend_type:
        print(f"\n✅ Weekend detected - generating {weekend_type} content...")
        content = automation.run_weekend_automation()
        
        if content:
            print(f"\n📱 {content.day_type.title()} LinkedIn Post Generated:")
            print("=" * 50)
            print(content.post_text)
            print("=" * 50)
            print(f"📊 Confidence Score: {content.confidence_score:.1f}/100")
        else:
            print("❌ No content generated")
    else:
        print("\n🧪 Testing Saturday simulation...")
        try:
            saturday_content = automation.generate_saturday_content()
            print(f"\n📊 SATURDAY SIMULATION:")
            print("=" * 40)
            print(saturday_content.post_text)
            print("=" * 40)
        except Exception as e:
            print(f"❌ Saturday test error: {e}")
        
        print("\n🧪 Testing Sunday simulation...")
        try:
            sunday_content = automation.generate_sunday_content()
            print(f"\n🔮 SUNDAY SIMULATION:")
            print("=" * 40)
            print(sunday_content.post_text)
            print("=" * 40)
        except Exception as e:
            print(f"❌ Sunday test error: {e}")
    
    print(f"\n✅ Weekend automation test completed!")
    
    # Show 7-day strategy
    print(f"\n📅 7-DAY LINKEDIN STRATEGY:")
    print("📊 Monday-Friday: Daily market intelligence briefs")
    print("📊 Saturday: Weekly wrap-up and analysis") 
    print("🔮 Sunday: Week-ahead preview and preparation")
    print(f"\n🚀 Complete system ready for daily use!")

if __name__ == "__main__":
    test_weekend_automation()