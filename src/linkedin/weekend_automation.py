#!/usr/bin/env python3
"""
Weekend Content Automation
Coordinates Saturday weekly recap and Sunday week-ahead content
"""

import sys
import os
sys.path.append('../')

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

# Import weekend content generators
from .weekly_wrap_generator import WeeklyWrapGenerator, WeeklyWrapSummary
from .week_ahead_generator import WeekAheadGenerator, WeekAheadPreview

# Import existing modules for data
from .commodity_price_tracker import CommodityPriceTracker, CommodityPrice
from .daily_market_screener import DailyMarketScreener, MarketSummary, StockAlert
from .news_intelligence_engine import NewsIntelligenceEngine, NewsAnalysis

from ..core.config import Config

@dataclass
class WeekendContent:
    """Weekend content package"""
    date: str
    day_type: str  # "saturday" or "sunday"
    content_type: str  # "weekly_wrap" or "week_ahead"
    post_text: str
    confidence_score: float
    data_summary: Dict

class WeekendAutomation:
    """Main coordinator for weekend LinkedIn content"""
    
    def __init__(self):
        self.config = Config()
        
        # Initialize content generators
        self.weekly_wrap_generator = WeeklyWrapGenerator()
        self.week_ahead_generator = WeekAheadGenerator()
        
        # Initialize data modules (reuse existing)
        self.commodity_tracker = CommodityPriceTracker()
        self.market_screener = DailyMarketScreener()
        self.news_engine = NewsIntelligenceEngine()
        
        # Weekend templates
        self.templates = {
            "saturday_wrap": """📊 Canadian Mining Week Wrap - {week_dates}

📈 WEEK'S TOP MOVERS
{top_movers}

💰 COMMODITY SCORECARD
{commodity_scorecard}

📰 WEEK'S MAJOR STORIES
{major_stories}

🏆 STOCK OF THE WEEK: {stock_of_week}

💡 WEEK'S TAKEAWAY: {weekly_takeaway}

#WeeklyWrap #CanadianMining #TSX #ResourceSector""",

            "sunday_preview": """🔮 Mining Week Ahead - {upcoming_week}

📅 THIS WEEK'S FOCUS
{weeks_focus}

⚡ WATCH LIST
{watch_list}

🌍 GLOBAL FACTORS
{global_factors}

💎 COMMODITY OUTLOOK
{commodity_outlook}

🎯 WEEK'S THEME: {weeks_theme}

What are you watching this week? 💬

#WeekAhead #MiningOutlook #CanadianMining #TSX"""
        }
    
    def detect_weekend_type(self) -> Optional[str]:
        """Detect if today is Saturday or Sunday"""
        today = datetime.now()
        weekday = today.weekday()  # Monday = 0, Sunday = 6
        
        if weekday == 5:  # Saturday
            return "saturday"
        elif weekday == 6:  # Sunday
            return "sunday"
        else:
            return None
    
    def run_weekend_automation(self) -> Optional[WeekendContent]:
        """Run appropriate weekend content generation"""
        weekend_type = self.detect_weekend_type()
        
        if not weekend_type:
            print("⚠️ Not a weekend day - no weekend content generated")
            return None
        
        print(f"🎯 Generating {weekend_type.title()} content...")
        
        if weekend_type == "saturday":
            return self.generate_saturday_content()
        elif weekend_type == "sunday":
            return self.generate_sunday_content()
    
    def generate_saturday_content(self) -> WeekendContent:
        """Generate Saturday weekly wrap content"""
        print("📊 Generating Weekly Wrap-Up...")
        
        # Generate weekly summary using existing data infrastructure
        weekly_summary = self.weekly_wrap_generator.generate_weekly_wrap()
        
        # Calculate confidence score
        confidence_score = self.calculate_wrap_confidence(weekly_summary)
        
        # Format post text
        post_text = self.format_saturday_post(weekly_summary)
        
        return WeekendContent(
            date=datetime.now().strftime("%Y-%m-%d"),
            day_type="saturday",
            content_type="weekly_wrap",
            post_text=post_text,
            confidence_score=confidence_score,
            data_summary=asdict(weekly_summary)
        )
    
    def generate_sunday_content(self) -> WeekendContent:
        """Generate Sunday week-ahead content"""
        print("🔮 Generating Week Ahead Preview...")
        
        # Generate week-ahead preview
        week_ahead = self.week_ahead_generator.generate_week_ahead()
        
        # Calculate confidence score
        confidence_score = self.calculate_preview_confidence(week_ahead)
        
        # Format post text
        post_text = self.format_sunday_post(week_ahead)
        
        return WeekendContent(
            date=datetime.now().strftime("%Y-%m-%d"),
            day_type="sunday",
            content_type="week_ahead",
            post_text=post_text,
            confidence_score=confidence_score,
            data_summary=asdict(week_ahead)
        )
    
    def format_saturday_post(self, weekly_summary: 'WeeklyWrapSummary') -> str:
        """Format Saturday weekly wrap post"""
        
        # Format week dates
        week_dates = f"{weekly_summary.week_start} - {weekly_summary.week_end}"
        
        # Format top movers
        top_movers = []
        if weekly_summary.top_gainers:
            for stock in weekly_summary.top_gainers[:3]:
                top_movers.append(f"📈 {stock['symbol']}: +{stock['weekly_change']:.1f}%")
        
        if weekly_summary.top_decliners:
            for stock in weekly_summary.top_decliners[:2]:
                top_movers.append(f"📉 {stock['symbol']}: {stock['weekly_change']:.1f}%")
        
        top_movers_text = "\n".join(top_movers) if top_movers else "• Mixed trading week across Canadian mining"
        
        # Format commodity scorecard
        commodity_lines = []
        for commodity in weekly_summary.commodity_performance[:5]:
            emoji = "📈" if commodity['weekly_change'] > 0 else "📉" if commodity['weekly_change'] < 0 else "➡️"
            commodity_lines.append(f"{emoji} {commodity['name']}: {commodity['weekly_change']:+.1f}%")
        
        commodity_scorecard = "\n".join(commodity_lines) if commodity_lines else "• Stable commodity price action"
        
        # Format major stories
        major_stories = "\n".join([f"• {story}" for story in weekly_summary.major_stories[:3]]) if weekly_summary.major_stories else "• Standard industry developments this week"
        
        # Stock of the week
        stock_of_week = weekly_summary.stock_of_week if weekly_summary.stock_of_week else "Monitoring sector developments"
        
        # Weekly takeaway
        weekly_takeaway = weekly_summary.key_takeaway if weekly_summary.key_takeaway else "Mixed sentiment in Canadian mining sector"
        
        return self.templates["saturday_wrap"].format(
            week_dates=week_dates,
            top_movers=top_movers_text,
            commodity_scorecard=commodity_scorecard,
            major_stories=major_stories,
            stock_of_week=stock_of_week,
            weekly_takeaway=weekly_takeaway
        )
    
    def format_sunday_post(self, week_ahead: 'WeekAheadPreview') -> str:
        """Format Sunday week-ahead post"""
        
        # Format upcoming week dates
        upcoming_week = f"Week of {week_ahead.week_start}"
        
        # Format week's focus
        weeks_focus = "\n".join([f"• {focus}" for focus in week_ahead.key_events[:3]]) if week_ahead.key_events else "• Standard market monitoring week"
        
        # Format watch list
        watch_list_items = []
        for stock in week_ahead.watch_list[:5]:
            watch_list_items.append(f"• {stock['symbol']}: {stock['reason']}")
        
        watch_list = "\n".join(watch_list_items) if watch_list_items else "• Monitoring broad sector developments"
        
        # Format global factors
        global_factors = "\n".join([f"• {factor}" for factor in week_ahead.global_factors[:3]]) if week_ahead.global_factors else "• Standard economic calendar week"
        
        # Format commodity outlook
        commodity_outlook = "\n".join([f"• {outlook}" for outlook in week_ahead.commodity_outlook[:3]]) if week_ahead.commodity_outlook else "• Monitoring commodity price action"
        
        # Week's theme
        weeks_theme = week_ahead.weeks_theme if week_ahead.weeks_theme else "Standard market monitoring"
        
        return self.templates["sunday_preview"].format(
            upcoming_week=upcoming_week,
            weeks_focus=weeks_focus,
            watch_list=watch_list,
            global_factors=global_factors,
            commodity_outlook=commodity_outlook,
            weeks_theme=weeks_theme
        )
    
    def calculate_wrap_confidence(self, weekly_summary: 'WeeklyWrapSummary') -> float:
        """Calculate confidence score for weekly wrap content"""
        score = 30.0  # Base score
        
        # Add points for data quality
        if weekly_summary.top_gainers:
            score += len(weekly_summary.top_gainers) * 5
        if weekly_summary.top_decliners:
            score += len(weekly_summary.top_decliners) * 5
        if weekly_summary.commodity_performance:
            score += len(weekly_summary.commodity_performance) * 3
        if weekly_summary.major_stories:
            score += len(weekly_summary.major_stories) * 8
        if weekly_summary.stock_of_week:
            score += 10
        
        return min(score, 100.0)
    
    def calculate_preview_confidence(self, week_ahead: 'WeekAheadPreview') -> float:
        """Calculate confidence score for week-ahead content"""
        score = 25.0  # Base score
        
        # Add points for forward-looking data
        if week_ahead.key_events:
            score += len(week_ahead.key_events) * 8
        if week_ahead.watch_list:
            score += len(week_ahead.watch_list) * 5
        if week_ahead.global_factors:
            score += len(week_ahead.global_factors) * 6
        if week_ahead.commodity_outlook:
            score += len(week_ahead.commodity_outlook) * 4
        if week_ahead.weeks_theme:
            score += 10
        
        return min(score, 100.0)
    
    def save_weekend_content(self, content: WeekendContent) -> str:
        """Save weekend content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/processed/weekend_content_{content.day_type}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(asdict(content), f, indent=2, default=str)
        
        return filename

def main():
    """Test weekend automation"""
    print("🎯 Weekend Content Automation Test")
    print("=" * 50)
    
    automation = WeekendAutomation()
    content = automation.run_weekend_automation()
    
    if content:
        print(f"\n✅ {content.day_type.title()} content generated:")
        print(f"📊 Confidence Score: {content.confidence_score:.1f}/100")
        print(f"\n📱 {content.day_type.title()} Post:")
        print("=" * 50)
        print(content.post_text)
        print("=" * 50)
        
        # Save content
        filename = automation.save_weekend_content(content)
        print(f"\n💾 Weekend content saved to: {filename}")
    else:
        print("ℹ️ No weekend content generated (not a weekend day)")

if __name__ == "__main__":
    main()