#!/usr/bin/env python3
"""
Enhanced Weekend Automation
Integrates breaking news monitor, event correlation, and smart report generation
"""

import sys
import os
sys.path.append('../')

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import asyncio

# Import enhanced intelligence systems
from ..intelligence.breaking_news_monitor import BreakingNewsMonitor, BreakingNewsEvent
from ..intelligence.event_correlation_engine import EventCorrelationEngine, EventCorrelation
from ..intelligence.smart_report_generator import SmartReportGenerator, SmartReportContent

# Import existing weekend systems for fallback
try:
    from .weekend_automation import WeekendAutomation as OriginalWeekendAutomation
except ImportError:
    OriginalWeekendAutomation = None

from ..core.config import Config

@dataclass
class EnhancedWeekendContent:
    """Enhanced weekend content with intelligent event integration"""
    date: str
    day_type: str  # "saturday" or "sunday"
    content_type: str  # "weekly_wrap" or "week_ahead"
    
    # Enhanced content
    smart_report: SmartReportContent
    post_text: str
    confidence_score: float
    
    # Event intelligence
    major_events_detected: int
    event_correlations_analyzed: int
    canadian_relevance_score: float
    market_impact_score: float
    
    # Metadata
    intelligence_enhanced: bool
    fallback_used: bool

class EnhancedWeekendAutomation:
    """Enhanced weekend automation with intelligent event detection"""
    
    def __init__(self):
        self.config = Config()
        
        # Initialize enhanced intelligence systems
        self.news_monitor = BreakingNewsMonitor()
        self.correlation_engine = EventCorrelationEngine()
        self.smart_generator = SmartReportGenerator()
        
        # Fallback to original system if needed
        self.original_automation = OriginalWeekendAutomation() if OriginalWeekendAutomation else None
        
        # Enhanced templates with event integration
        self.enhanced_templates = {
            "saturday_event_driven": """🚨 Canadian Mining Week Wrap - {week_dates}

⚡ WEEK'S MAJOR DEVELOPMENT
{major_event_headline}

📊 MARKET IMPACT
{market_impact_summary}

💰 COMMODITY SCORECARD
{commodity_scorecard}

📈 CANADIAN MINING REACTION
{canadian_mining_reaction}

🔍 ANALYSIS: {event_analysis}

💡 WEEK'S TAKEAWAY: {weekly_takeaway}

#WeeklyWrap #BreakingNews #CanadianMining #TSX #ResourceSector""",

            "saturday_enhanced": """📊 Canadian Mining Week Wrap - {week_dates}

📰 WEEK'S KEY EVENTS
{major_events}

📈 MARKET MOVEMENTS
{market_movements}

💰 COMMODITY PERFORMANCE  
{commodity_performance}

🇨🇦 CANADIAN MINING FOCUS
{canadian_focus}

💡 WEEK'S TAKEAWAY: {weekly_takeaway}

#WeeklyWrap #CanadianMining #TSX #ResourceSector""",

            "sunday_enhanced": """🔮 Mining Week Ahead - {upcoming_week}

📅 WEEK'S CONTEXT
{weeks_context}

⚡ EVENTS TO WATCH
{events_to_watch}

🎯 MARKET IMPLICATIONS
{market_implications}

💎 COMMODITY OUTLOOK
{commodity_outlook}

🇨🇦 CANADIAN MINING FOCUS
{canadian_focus}

#WeekAhead #MiningOutlook #CanadianMining #TSX""",

            "fallback_enhanced": """🏭 Canadian Mining Brief - {date}

📊 WEEKEND INTELLIGENCE SUMMARY
{intelligence_summary}

📰 Recent developments in Canadian mining sector
💰 Commodity price movements monitored  
📈 TSX/TSXV mining stock activity tracked

Data: Enhanced intelligence system | Market monitoring active

#CanadianMining #WeekendWrap #MiningDaily #ResourceSector"""
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
    
    async def run_enhanced_weekend_automation(self) -> Optional[EnhancedWeekendContent]:
        """Run enhanced weekend content generation with intelligence integration"""
        weekend_type = self.detect_weekend_type()
        
        if not weekend_type:
            print("⚠️ Not a weekend day - no weekend content generated")
            return None
        
        print(f"🧠 Generating Enhanced {weekend_type.title()} Content...")
        print("🔍 Integrating breaking news, event correlation, and smart analysis")
        
        try:
            if weekend_type == "saturday":
                return await self.generate_enhanced_saturday_content()
            elif weekend_type == "sunday":
                return await self.generate_enhanced_sunday_content()
        except Exception as e:
            print(f"⚠️ Enhanced generation failed: {e}")
            print("🔄 Falling back to enhanced basic generation...")
            return await self.generate_fallback_enhanced_content(weekend_type)
    
    async def generate_enhanced_saturday_content(self) -> EnhancedWeekendContent:
        """Generate enhanced Saturday weekly wrap with intelligent event analysis"""
        print("📊 Generating Enhanced Weekly Wrap...")
        
        # Generate smart report with event integration
        smart_report = await self.smart_generator.generate_smart_weekend_report("saturday_wrap")
        
        # Determine content style based on events
        if (smart_report.event_driven and 
            smart_report.major_events and 
            smart_report.major_events[0].priority_score >= 80.0):
            
            post_text = self.format_event_driven_saturday_post(smart_report)
            content_style = "event_driven"
        else:
            post_text = self.format_enhanced_saturday_post(smart_report)
            content_style = "enhanced"
        
        # Calculate enhanced metrics
        major_events_count = len(smart_report.major_events)
        correlations_count = len(smart_report.event_correlations)
        
        market_impact_score = 0.0
        if smart_report.event_correlations:
            market_impact_score = sum(c.overall_impact_score for c in smart_report.event_correlations) / len(smart_report.event_correlations)
        
        return EnhancedWeekendContent(
            date=datetime.now().strftime("%Y-%m-%d"),
            day_type="saturday",
            content_type="weekly_wrap",
            smart_report=smart_report,
            post_text=post_text,
            confidence_score=smart_report.confidence_score,
            major_events_detected=major_events_count,
            event_correlations_analyzed=correlations_count,
            canadian_relevance_score=smart_report.canadian_relevance_score,
            market_impact_score=market_impact_score,
            intelligence_enhanced=True,
            fallback_used=False
        )
    
    async def generate_enhanced_sunday_content(self) -> EnhancedWeekendContent:
        """Generate enhanced Sunday week-ahead with intelligent context"""
        print("🔮 Generating Enhanced Week Ahead...")
        
        # Generate smart report with forward-looking analysis
        smart_report = await self.smart_generator.generate_smart_weekend_report("sunday_preview")
        
        # Format Sunday post with event context
        post_text = self.format_enhanced_sunday_post(smart_report)
        
        # Calculate enhanced metrics
        major_events_count = len(smart_report.major_events)
        correlations_count = len(smart_report.event_correlations)
        
        market_impact_score = 0.0
        if smart_report.event_correlations:
            market_impact_score = sum(c.overall_impact_score for c in smart_report.event_correlations) / len(smart_report.event_correlations)
        
        return EnhancedWeekendContent(
            date=datetime.now().strftime("%Y-%m-%d"),
            day_type="sunday",
            content_type="week_ahead",
            smart_report=smart_report,
            post_text=post_text,
            confidence_score=smart_report.confidence_score,
            major_events_detected=major_events_count,
            event_correlations_analyzed=correlations_count,
            canadian_relevance_score=smart_report.canadian_relevance_score,
            market_impact_score=market_impact_score,
            intelligence_enhanced=True,
            fallback_used=False
        )
    
    async def generate_fallback_enhanced_content(self, weekend_type: str) -> EnhancedWeekendContent:
        """Generate fallback enhanced content when smart generation fails"""
        print("🔄 Generating Fallback Enhanced Content...")
        
        # Try to get recent breaking news at minimum
        try:
            recent_events = self.news_monitor.get_recent_breaking_news(hours_back=168, min_priority=60.0)  # 1 week
            events_summary = f"{len(recent_events)} major events detected in past week"
        except Exception:
            recent_events = []
            events_summary = "Standard market monitoring active"
        
        # Create basic enhanced post
        date_str = datetime.now().strftime("%B %d, %Y")
        post_text = self.enhanced_templates["fallback_enhanced"].format(
            date=date_str,
            intelligence_summary=events_summary
        )
        
        # Create minimal smart report
        smart_report = SmartReportContent(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            report_type=f"{weekend_type}_wrap" if weekend_type == "saturday" else "sunday_preview",
            market_summary={},
            commodity_summary={},
            news_summary={},
            major_events=recent_events[:5],
            event_correlations=[],
            market_narrative="Enhanced monitoring system active with fallback content generation.",
            impact_analysis="Limited analysis due to system constraints.",
            headline_section="📊 WEEKEND BRIEF",
            market_section="📈 Market monitoring active",
            commodity_section="💰 Commodity tracking active", 
            events_section="📰 Event detection active",
            outlook_section="🎯 Continuing enhanced monitoring",
            confidence_score=60.0,
            event_driven=len(recent_events) > 0,
            canadian_relevance_score=70.0
        )
        
        return EnhancedWeekendContent(
            date=datetime.now().strftime("%Y-%m-%d"),
            day_type=weekend_type,
            content_type="weekly_wrap" if weekend_type == "saturday" else "week_ahead",
            smart_report=smart_report,
            post_text=post_text,
            confidence_score=60.0,
            major_events_detected=len(recent_events),
            event_correlations_analyzed=0,
            canadian_relevance_score=70.0,
            market_impact_score=0.0,
            intelligence_enhanced=True,
            fallback_used=True
        )
    
    def format_event_driven_saturday_post(self, smart_report: SmartReportContent) -> str:
        """Format Saturday post when driven by major events"""
        
        week_start = (datetime.now() - timedelta(days=6)).strftime("%b %d")
        week_end = datetime.now().strftime("%b %d")
        week_dates = f"{week_start} - {week_end}"
        
        # Get top event
        top_event = smart_report.major_events[0]
        major_event_headline = top_event.headline
        
        # Market impact from correlations
        market_impact_summary = "Limited market data available"
        canadian_mining_reaction = "Monitoring Canadian mining response"
        
        if smart_report.event_correlations:
            top_correlation = smart_report.event_correlations[0]
            market_impact_summary = top_correlation.primary_impact
            if top_correlation.canadian_mining_impact > 0:
                canadian_mining_reaction = f"Canadian mining sector: {top_correlation.canadian_mining_impact:.1f}% average movement"
        
        # Commodity scorecard
        commodity_lines = []
        if top_event.commodity_impact:
            for commodity, impact in top_event.commodity_impact.items():
                if abs(impact) >= 5:
                    emoji = "📈" if impact > 0 else "📉"
                    commodity_lines.append(f"{emoji} {commodity}: Event-driven volatility")
        
        commodity_scorecard = "\n".join(commodity_lines) if commodity_lines else "• Monitoring commodity price reactions"
        
        # Event analysis
        event_analysis = smart_report.impact_analysis
        
        # Weekly takeaway
        weekly_takeaway = smart_report.market_narrative
        
        return self.enhanced_templates["saturday_event_driven"].format(
            week_dates=week_dates,
            major_event_headline=major_event_headline,
            market_impact_summary=market_impact_summary,
            commodity_scorecard=commodity_scorecard,
            canadian_mining_reaction=canadian_mining_reaction,
            event_analysis=event_analysis,
            weekly_takeaway=weekly_takeaway
        )
    
    def format_enhanced_saturday_post(self, smart_report: SmartReportContent) -> str:
        """Format enhanced Saturday post with multiple events"""
        
        week_start = (datetime.now() - timedelta(days=6)).strftime("%b %d")
        week_end = datetime.now().strftime("%b %d")
        week_dates = f"{week_start} - {week_end}"
        
        # Major events
        event_lines = []
        if smart_report.major_events:
            for event in smart_report.major_events[:4]:
                priority_emoji = "🚨" if event.priority_score >= 80 else "⚡" if event.priority_score >= 60 else "📍"
                event_lines.append(f"{priority_emoji} {event.headline}")
        else:
            event_lines.append("• Standard industry developments this week")
        
        major_events = "\n".join(event_lines)
        
        # Market movements
        market_lines = ["📈 Mixed trading across Canadian mining sector"]
        if smart_report.event_correlations:
            significant_correlations = [c for c in smart_report.event_correlations if c.overall_impact_score >= 10]
            for correlation in significant_correlations[:2]:
                market_lines.append(f"• {correlation.market_narrative}")
        
        market_movements = "\n".join(market_lines)
        
        # Commodity performance
        commodity_lines = ["💰 Commodity price monitoring active"]
        
        # Canadian focus
        canadian_lines = [f"🇨🇦 Canadian mining relevance: {smart_report.canadian_relevance_score:.0f}%"]
        if smart_report.event_driven:
            canadian_lines.append("• Enhanced event analysis applied")
        
        canadian_focus = "\n".join(canadian_lines)
        
        # Weekly takeaway
        weekly_takeaway = smart_report.market_narrative
        
        return self.enhanced_templates["saturday_enhanced"].format(
            week_dates=week_dates,
            major_events=major_events,
            market_movements=market_movements,
            commodity_performance="\n".join(commodity_lines),
            canadian_focus=canadian_focus,
            weekly_takeaway=weekly_takeaway
        )
    
    def format_enhanced_sunday_post(self, smart_report: SmartReportContent) -> str:
        """Format enhanced Sunday week-ahead post"""
        
        next_week_start = (datetime.now() + timedelta(days=1)).strftime("%b %d")
        upcoming_week = f"Week of {next_week_start}"
        
        # Week's context from recent events
        context_lines = []
        if smart_report.major_events:
            policy_events = [e for e in smart_report.major_events if e.event_type == "policy"]
            market_events = [e for e in smart_report.major_events if e.event_type == "market_move"]
            
            if policy_events:
                context_lines.append("• Policy developments continue to influence markets")
            if market_events:
                context_lines.append("• Market volatility from recent events")
            if not context_lines:
                context_lines.append("• Standard market progression expected")
        else:
            context_lines.append("• Stable market environment heading into new week")
        
        weeks_context = "\n".join(context_lines)
        
        # Events to watch (forward-looking)
        watch_lines = [
            "• Continuation of recent event impacts",
            "• Policy development monitoring",
            "• Canadian mining sector reaction tracking"
        ]
        events_to_watch = "\n".join(watch_lines)
        
        # Market implications
        implications_lines = []
        if smart_report.event_correlations:
            strong_correlations = [c for c in smart_report.event_correlations if c.correlation_strength == "strong"]
            if strong_correlations:
                implications_lines.append("• Strong event-market correlations suggest continued volatility")
        
        if not implications_lines:
            implications_lines.append("• Standard market dynamics expected")
        
        market_implications = "\n".join(implications_lines)
        
        # Commodity outlook
        commodity_lines = ["• Monitoring for event-driven commodity movements"]
        
        # Canadian focus
        canadian_lines = [
            "• Enhanced monitoring of Canadian mining impacts",
            f"• {smart_report.canadian_relevance_score:.0f}% relevance score for tracked events"
        ]
        
        return self.enhanced_templates["sunday_enhanced"].format(
            upcoming_week=upcoming_week,
            weeks_context=weeks_context,
            events_to_watch=events_to_watch,
            market_implications=market_implications,
            commodity_outlook="\n".join(commodity_lines),
            canadian_focus="\n".join(canadian_lines)
        )
    
    def save_enhanced_weekend_content(self, content: EnhancedWeekendContent) -> str:
        """Save enhanced weekend content to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/processed/enhanced_weekend_content_{content.day_type}_{timestamp}.json"
        
        # Convert smart_report to dict for JSON serialization
        content_dict = asdict(content)
        content_dict["smart_report"] = asdict(content.smart_report)
        
        with open(filename, 'w') as f:
            json.dump(content_dict, f, indent=2, default=str)
        
        return filename

async def main():
    """Test enhanced weekend automation"""
    print("🧠 Enhanced Weekend Content Automation Test")
    print("=" * 60)
    
    automation = EnhancedWeekendAutomation()
    content = await automation.run_enhanced_weekend_automation()
    
    if content:
        print(f"\n✅ Enhanced {content.day_type.title()} content generated:")
        print(f"📊 Confidence Score: {content.confidence_score:.1f}/100")
        print(f"🎯 Intelligence Enhanced: {content.intelligence_enhanced}")
        print(f"🔄 Fallback Used: {content.fallback_used}")
        print(f"📰 Major Events Detected: {content.major_events_detected}")
        print(f"🔗 Event Correlations: {content.event_correlations_analyzed}")
        print(f"🇨🇦 Canadian Relevance: {content.canadian_relevance_score:.1f}%")
        print(f"📈 Market Impact Score: {content.market_impact_score:.1f}")
        
        print(f"\n📱 Enhanced {content.day_type.title()} Post:")
        print("=" * 60)
        print(content.post_text)
        print("=" * 60)
        
        # Save content
        filename = automation.save_enhanced_weekend_content(content)
        print(f"\n💾 Enhanced weekend content saved to: {filename}")
        
        # Show event details if available
        if content.smart_report.major_events:
            print(f"\n📰 Major Events Detected:")
            for i, event in enumerate(content.smart_report.major_events[:3], 1):
                print(f"  {i}. [{event.priority_score:.0f}] {event.headline}")
        
        if content.smart_report.event_correlations:
            print(f"\n🔗 Event Correlations:")
            for i, correlation in enumerate(content.smart_report.event_correlations[:2], 1):
                print(f"  {i}. {correlation.primary_impact} (strength: {correlation.correlation_strength})")
    
    else:
        print("ℹ️ No enhanced weekend content generated (not a weekend day)")

if __name__ == "__main__":
    asyncio.run(main())