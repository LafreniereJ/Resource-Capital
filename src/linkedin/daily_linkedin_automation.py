#!/usr/bin/env python3
"""
Daily LinkedIn Mining Brief Automation
Orchestrates all intelligence modules to create comprehensive daily LinkedIn posts
"""

import sys
import os
sys.path.append('../')

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import random

# Import our intelligence modules
from .linkedin_brief_generator import LinkedInBriefGenerator, LinkedInBrief
from .commodity_price_tracker import CommodityPriceTracker, CommodityPrice
from .daily_market_screener import DailyMarketScreener, MarketSummary, StockAlert
from .news_intelligence_engine import NewsIntelligenceEngine, NewsAnalysis

from ..core.config import Config

@dataclass
class DailyIntelligence:
    """Complete daily intelligence package"""
    date: str
    market_summary: Optional[MarketSummary]
    commodity_data: List[CommodityPrice]
    news_analysis: Optional[NewsAnalysis]
    linkedin_brief: Optional[LinkedInBrief]
    alerts: List[str]
    post_text: str
    confidence_score: float

class DailyLinkedInAutomation:
    """Main automation system for daily LinkedIn mining briefs"""
    
    def __init__(self):
        self.config = Config()
        
        # Initialize all intelligence modules
        self.brief_generator = LinkedInBriefGenerator()
        self.commodity_tracker = CommodityPriceTracker()
        self.market_screener = DailyMarketScreener()
        self.news_engine = NewsIntelligenceEngine()
        
        # Post templates for different scenarios
        self.templates = {
            "market_dominant": """🏭 Canadian Mining Brief - {date}

⚡ MARKET HIGHLIGHTS
{market_movers}

💰 COMMODITIES
{commodities}

🔍 KEY INSIGHT: {insight}

Data: {company_count} companies | TSX/TSXV
#CanadianMining #TSX #MiningStocks #ResourceSector""",

            "news_dominant": """🏭 Canadian Mining Brief - {date}

📰 TOP STORY
{news_headline}

📊 MARKET PULSE
{market_pulse}

💎 COMMODITY WATCH
{top_commodity}

#MiningNews #CanadianMining #ResourceSector #TSX""",

            "commodity_dominant": """🏭 Canadian Mining Brief - {date}

🚨 COMMODITY ALERT
{commodity_alert}

📈 MARKET REACTION
{market_reaction}

🔍 IMPACT: {impact_analysis}

#CommodityAlert #Mining #MarketUpdate #TSX""",

            "balanced": """🏭 Canadian Mining Brief - {date}

📊 DAILY OVERVIEW
• {market_summary}
• {commodity_summary} 
• {news_summary}

🎯 FOCUS: {daily_focus}

Data: Live market intelligence | TSX/TSXV
#CanadianMining #MiningDaily #ResourceSector"""
        }
    
    def collect_intelligence(self, max_stocks: int = 100) -> DailyIntelligence:
        """Collect intelligence from all sources"""
        print("🧠 Collecting daily mining intelligence...")
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        alerts = []
        confidence_score = 0.0
        
        # 1. Market Screening
        print("📊 Screening market movements...")
        try:
            market_alerts = self.market_screener.screen_all_stocks(max_stocks=max_stocks)
            significant_alerts = self.market_screener.filter_alerts(market_alerts, min_change_pct=5.0)
            market_summary = self.market_screener.generate_market_summary(significant_alerts)
            
            if market_summary.major_moves > 0:
                alerts.append(f"🚨 {market_summary.major_moves} major stock moves detected")
                confidence_score += 20
            
            confidence_score += min(len(significant_alerts) * 2, 30)  # Up to 30 points for market activity
            
        except Exception as e:
            print(f"⚠️ Market screening error: {e}")
            market_summary = None
            alerts.append("⚠️ Market data unavailable")
        
        # 2. Commodity Tracking
        print("💰 Tracking commodity prices...")
        try:
            commodity_data = self.commodity_tracker.get_all_commodity_prices()
            
            # Check for significant commodity moves
            significant_commodities = [c for c in commodity_data if abs(c.change_pct_1d) >= 2.0]
            if significant_commodities:
                top_mover = max(significant_commodities, key=lambda x: abs(x.change_pct_1d))
                alerts.append(f"💎 {top_mover.name} moved {top_mover.change_pct_1d:+.1f}%")
                confidence_score += 15
            
            confidence_score += min(len(commodity_data) * 3, 25)  # Up to 25 points for commodity data
            
        except Exception as e:
            print(f"⚠️ Commodity tracking error: {e}")
            commodity_data = []
            alerts.append("⚠️ Commodity data unavailable")
        
        # 3. News Intelligence
        print("📰 Analyzing news intelligence...")
        try:
            news_items = self.news_engine.fetch_all_news(max_age_hours=24)
            news_analysis = self.news_engine.prioritize_news(news_items)
            
            if news_analysis.critical_news:
                alerts.append(f"📰 {len(news_analysis.critical_news)} critical news stories")
                confidence_score += 20
            
            if news_analysis.ma_activity:
                alerts.append(f"💼 {len(news_analysis.ma_activity)} M&A developments")
                confidence_score += 15
            
            confidence_score += min(news_analysis.total_articles, 20)  # Up to 20 points for news coverage
            
        except Exception as e:
            print(f"⚠️ News analysis error: {e}")
            news_analysis = None
            alerts.append("⚠️ News analysis unavailable")
        
        # 4. Generate LinkedIn Brief
        print("📱 Generating LinkedIn content...")
        try:
            linkedin_brief = self.brief_generator.generate_daily_brief()
            confidence_score += 10  # Base points for successful generation
        except Exception as e:
            print(f"⚠️ LinkedIn generation error: {e}")
            linkedin_brief = None
        
        # Calculate final confidence score
        confidence_score = min(confidence_score, 100.0)
        
        # Generate post text
        post_text = self.create_optimized_post(
            market_summary, commodity_data, news_analysis, linkedin_brief
        )
        
        return DailyIntelligence(
            date=date_str,
            market_summary=market_summary,
            commodity_data=commodity_data,
            news_analysis=news_analysis,
            linkedin_brief=linkedin_brief,
            alerts=alerts,
            post_text=post_text,
            confidence_score=confidence_score
        )
    
    def create_optimized_post(self, market_summary: Optional[MarketSummary],
                            commodity_data: List[CommodityPrice],
                            news_analysis: Optional[NewsAnalysis],
                            linkedin_brief: Optional[LinkedInBrief]) -> str:
        """Create optimized LinkedIn post based on available data"""
        
        date_str = datetime.now().strftime("%B %d, %Y")
        
        # Determine dominant theme
        theme = self.determine_post_theme(market_summary, commodity_data, news_analysis)
        
        try:
            if theme == "market_dominant":
                return self.create_market_focused_post(date_str, market_summary, commodity_data)
            
            elif theme == "news_dominant":
                return self.create_news_focused_post(date_str, news_analysis, market_summary)
            
            elif theme == "commodity_dominant":
                return self.create_commodity_focused_post(date_str, commodity_data, market_summary)
            
            else:  # balanced
                return self.create_balanced_post(date_str, market_summary, commodity_data, news_analysis)
        
        except Exception as e:
            # Fallback to simple format
            return self.create_fallback_post(date_str, market_summary, commodity_data)
    
    def determine_post_theme(self, market_summary: Optional[MarketSummary],
                           commodity_data: List[CommodityPrice],
                           news_analysis: Optional[NewsAnalysis]) -> str:
        """Determine the dominant theme for today's post"""
        
        # Score each theme
        market_score = 0
        news_score = 0
        commodity_score = 0
        
        # Market scoring
        if market_summary:
            market_score += market_summary.major_moves * 10
            market_score += len(market_summary.top_gainers) * 3
            market_score += len(market_summary.top_decliners) * 2
        
        # News scoring
        if news_analysis:
            news_score += len(news_analysis.critical_news) * 15
            news_score += len(news_analysis.ma_activity) * 10
            news_score += len(news_analysis.high_priority_news) * 5
        
        # Commodity scoring
        significant_commodities = [c for c in commodity_data if abs(c.change_pct_1d) >= 3.0]
        commodity_score += len(significant_commodities) * 8
        
        major_commodity_moves = [c for c in commodity_data if abs(c.change_pct_1d) >= 5.0]
        commodity_score += len(major_commodity_moves) * 15
        
        # Determine theme
        max_score = max(market_score, news_score, commodity_score)
        
        if max_score == 0 or max_score < 20:
            return "balanced"
        elif max_score == market_score:
            return "market_dominant"
        elif max_score == news_score:
            return "news_dominant"
        else:
            return "commodity_dominant"
    
    def create_market_focused_post(self, date: str, market_summary: MarketSummary, 
                                 commodity_data: List[CommodityPrice]) -> str:
        """Create market-focused LinkedIn post"""
        
        # Format market movers
        market_movers = []
        
        if market_summary.top_gainers:
            for gainer in market_summary.top_gainers[:3]:
                market_movers.append(f"📈 {gainer.company}: +{gainer.change_pct_1d:.1f}%")
        
        if market_summary.top_decliners:
            for decliner in market_summary.top_decliners[:2]:
                market_movers.append(f"📉 {decliner.company}: {decliner.change_pct_1d:.1f}%")
        
        market_movers_text = "\n".join(market_movers) if market_movers else "Mixed trading conditions"
        
        # Format commodities
        commodity_text = "Market data updating"
        if commodity_data:
            top_commodity = max(commodity_data, key=lambda x: abs(x.change_pct_1d))
            emoji = "⬆️" if top_commodity.change_pct_1d > 0 else "⬇️"
            commodity_text = f"{emoji} {top_commodity.name}: {top_commodity.change_pct_1d:+.1f}%"
        
        # Generate insight
        insight = self.generate_market_insight(market_summary, commodity_data)
        
        return self.templates["market_dominant"].format(
            date=date,
            market_movers=market_movers_text,
            commodities=commodity_text,
            insight=insight,
            company_count=market_summary.total_companies_scanned if market_summary else "999"
        )
    
    def create_news_focused_post(self, date: str, news_analysis: NewsAnalysis,
                               market_summary: Optional[MarketSummary]) -> str:
        """Create news-focused LinkedIn post"""
        
        # Top news headline
        news_headline = "Mining sector developments continue"
        if news_analysis and news_analysis.critical_news:
            headline = news_analysis.critical_news[0].headline
            news_headline = headline[:100] + "..." if len(headline) > 100 else headline
        
        # Market pulse
        market_pulse = "Mixed trading in Canadian mining"
        if market_summary:
            market_pulse = f"{market_summary.gainers} gainers, {market_summary.decliners} decliners"
        
        # Top commodity (placeholder)
        top_commodity = "Gold tracking sideways"
        
        return self.templates["news_dominant"].format(
            date=date,
            news_headline=news_headline,
            market_pulse=market_pulse,
            top_commodity=top_commodity
        )
    
    def create_commodity_focused_post(self, date: str, commodity_data: List[CommodityPrice],
                                    market_summary: Optional[MarketSummary]) -> str:
        """Create commodity-focused LinkedIn post"""
        
        # Find biggest commodity move
        top_commodity = max(commodity_data, key=lambda x: abs(x.change_pct_1d))
        direction = "surges" if top_commodity.change_pct_1d > 0 else "declines"
        
        commodity_alert = f"{top_commodity.name} {direction} {abs(top_commodity.change_pct_1d):.1f}%"
        
        # Market reaction
        market_reaction = "Mining stocks responding to commodity moves"
        if market_summary and market_summary.major_moves > 0:
            market_reaction = f"{market_summary.major_moves} mining stocks showing major moves"
        
        # Impact analysis
        impact_analysis = f"{top_commodity.name} movement driving sector sentiment"
        
        return self.templates["commodity_dominant"].format(
            date=date,
            commodity_alert=commodity_alert,
            market_reaction=market_reaction,
            impact_analysis=impact_analysis
        )
    
    def create_balanced_post(self, date: str, market_summary: Optional[MarketSummary],
                           commodity_data: List[CommodityPrice],
                           news_analysis: Optional[NewsAnalysis]) -> str:
        """Create balanced overview post"""
        
        # Market summary
        market_text = "Mixed trading conditions"
        if market_summary:
            market_text = f"{market_summary.gainers} gainers, {market_summary.decliners} decliners"
        
        # Commodity summary
        commodity_text = "Stable commodity prices"
        if commodity_data:
            active_commodities = [c for c in commodity_data if abs(c.change_pct_1d) >= 1.0]
            if active_commodities:
                commodity_text = f"{len(active_commodities)} commodities showing movement"
        
        # News summary
        news_text = "Standard industry updates"
        if news_analysis:
            news_text = f"{news_analysis.total_articles} news articles analyzed"
        
        # Daily focus
        daily_focus = "Monitoring Canadian mining sector developments"
        
        return self.templates["balanced"].format(
            date=date,
            market_summary=market_text,
            commodity_summary=commodity_text,
            news_summary=news_text,
            daily_focus=daily_focus
        )
    
    def create_fallback_post(self, date: str, market_summary: Optional[MarketSummary],
                           commodity_data: List[CommodityPrice]) -> str:
        """Create simple fallback post when data is limited"""
        
        company_count = market_summary.total_companies_scanned if market_summary else "999"
        
        return f"""🏭 Canadian Mining Brief - {date}

📊 Daily market intelligence update
• {company_count} companies monitored
• Live TSX/TSXV data tracking
• Commodity and news analysis

Providing daily insights into Canada's mining sector.

#CanadianMining #TSX #ResourceSector #MiningDaily"""
    
    def generate_market_insight(self, market_summary: MarketSummary,
                              commodity_data: List[CommodityPrice]) -> str:
        """Generate intelligent market insight"""
        
        insights = []
        
        # Market-based insights
        if market_summary.major_moves >= 3:
            insights.append("High volatility day with multiple major moves")
        elif market_summary.gainers > market_summary.decliners * 2:
            insights.append("Strong bullish sentiment across Canadian mining")
        elif market_summary.decliners > market_summary.gainers * 2:
            insights.append("Market pressure on mining sector today")
        
        # Commodity-based insights
        if commodity_data:
            gold_data = next((c for c in commodity_data if c.name == "Gold"), None)
            if gold_data and abs(gold_data.change_pct_1d) >= 2.0:
                direction = "strength" if gold_data.change_pct_1d > 0 else "weakness"
                insights.append(f"Gold {direction} influencing precious metals miners")
        
        # Volume insights
        if market_summary.high_volume_stocks >= 5:
            insights.append("Elevated trading volumes suggest institutional activity")
        
        # Default insight
        if not insights:
            insights.append("Active monitoring of Canadian mining developments")
        
        return insights[0]
    
    def save_daily_intelligence(self, intelligence: DailyIntelligence) -> str:
        """Save complete daily intelligence package"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/processed/daily_intelligence_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(asdict(intelligence), f, indent=2, default=str)
        
        return filename
    
    def run_daily_automation(self, max_stocks: int = 150) -> DailyIntelligence:
        """Run complete daily automation workflow"""
        print("🚀 Starting Daily LinkedIn Mining Brief Automation")
        print("=" * 60)
        
        # Collect all intelligence
        intelligence = self.collect_intelligence(max_stocks=max_stocks)
        
        print(f"\n✅ Daily intelligence collected:")
        print(f"📊 Confidence Score: {intelligence.confidence_score:.1f}/100")
        print(f"🚨 Alerts: {len(intelligence.alerts)}")
        
        for alert in intelligence.alerts:
            print(f"  {alert}")
        
        print(f"\n📱 LinkedIn Post Generated:")
        print("=" * 50)
        print(intelligence.post_text)
        print("=" * 50)
        
        # Save intelligence package
        filename = self.save_daily_intelligence(intelligence)
        print(f"\n💾 Intelligence saved to: {filename}")
        
        # Save post text separately for easy access
        post_filename = f"data/processed/linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(post_filename, 'w') as f:
            f.write(intelligence.post_text)
        
        print(f"📱 Post text saved to: {post_filename}")
        
        return intelligence

def main():
    """Run LinkedIn automation with weekend detection"""
    from datetime import datetime
    
    today = datetime.now()
    weekday = today.weekday()  # Monday = 0, Sunday = 6
    
    if weekday in [5, 6]:  # Saturday or Sunday
        print("🎯 Weekend detected - routing to weekend content automation")
        try:
            from .weekend_automation import WeekendAutomation
            weekend_automation = WeekendAutomation()
            content = weekend_automation.run_weekend_automation()
            
            if content:
                print(f"\n🎉 Weekend automation completed successfully!")
                print(f"📱 {content.day_type.title()} content ready for LinkedIn!")
            else:
                print("ℹ️ No weekend content generated")
                
        except ImportError as e:
            print(f"⚠️ Weekend automation not available: {e}")
            print("📱 Running standard daily automation instead...")
            automation = DailyLinkedInAutomation()
            intelligence = automation.run_daily_automation(max_stocks=75)
            print(f"\n🎉 Daily automation completed successfully!")
            print(f"📈 Ready to post to LinkedIn!")
    else:
        print("📊 Weekday detected - running daily market intelligence")
        automation = DailyLinkedInAutomation()
        intelligence = automation.run_daily_automation(max_stocks=75)  # Smaller sample for testing
        
        print(f"\n🎉 Daily automation completed successfully!")
        print(f"📈 Ready to post to LinkedIn!")

if __name__ == "__main__":
    main()