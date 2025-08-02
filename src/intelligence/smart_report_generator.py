#!/usr/bin/env python3
"""
Smart Report Generator
Automatically includes major market events in weekend reports and LinkedIn posts
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3

from .breaking_news_monitor import BreakingNewsMonitor, BreakingNewsEvent
from .event_correlation_engine import EventCorrelationEngine, EventCorrelation

@dataclass
class SmartReportContent:
    """Smart report content with integrated event analysis"""
    report_date: str
    report_type: str  # "saturday_wrap", "sunday_preview", "daily_brief"
    
    # Traditional content
    market_summary: Dict
    commodity_summary: Dict
    news_summary: Dict
    
    # Enhanced event-driven content
    major_events: List[BreakingNewsEvent]
    event_correlations: List[EventCorrelation]
    market_narrative: str
    impact_analysis: str
    
    # Report sections
    headline_section: str
    market_section: str
    commodity_section: str
    events_section: str
    outlook_section: str
    
    # Metadata
    confidence_score: float
    event_driven: bool
    canadian_relevance_score: float

class SmartReportGenerator:
    """Generates intelligent reports with automatic event integration"""
    
    def __init__(self, db_path: str = "data/databases/mining_intelligence.db"):
        self.db_path = db_path
        self.news_monitor = BreakingNewsMonitor(db_path)
        self.correlation_engine = EventCorrelationEngine(db_path)
        
        # Report templates with event integration
        self.templates = {
            "saturday_wrap": {
                "header": "📊 Canadian Mining Week Wrap - {week_dates}",
                "event_priority": True,
                "focus": "weekly_analysis_with_events"
            },
            "sunday_preview": {
                "header": "🔮 Mining Week Ahead - {upcoming_week}",
                "event_priority": True,
                "focus": "forward_looking_with_context"
            },
            "daily_brief": {
                "header": "🏭 Canadian Mining Brief - {date}",
                "event_priority": False,
                "focus": "daily_update_with_breaking"
            }
        }
        
        # Event significance thresholds
        self.significance_thresholds = {
            "critical_event": 80.0,
            "major_event": 60.0,
            "notable_event": 40.0,
            "minor_event": 20.0
        }
        
        # Canadian mining context keywords
        self.canadian_context = [
            "canadian mining", "tsx mining", "toronto stock exchange",
            "canadian resources", "mining sector canada", "canadian miners",
            "resource sector", "canadian commodities"
        ]
    
    async def generate_smart_weekend_report(self, report_type: str = "saturday_wrap") -> SmartReportContent:
        """Generate intelligent weekend report with event integration"""
        print(f"🧠 Generating smart {report_type} report...")
        
        # Determine analysis period
        if report_type == "saturday_wrap":
            analysis_days = 7  # Look back at the week
            future_days = 0
        else:  # sunday_preview
            analysis_days = 2  # Recent context
            future_days = 7  # Look ahead at next week
        
        # Collect breaking news and correlations
        major_events = await self.collect_major_events(analysis_days)
        event_correlations = await self.analyze_event_correlations(major_events)
        
        # Generate traditional content summaries
        market_summary = await self.generate_market_summary(analysis_days)
        commodity_summary = await self.generate_commodity_summary(analysis_days)
        news_summary = await self.generate_news_summary(analysis_days)
        
        # Create event-driven narrative
        market_narrative = self.create_market_narrative(major_events, event_correlations)
        impact_analysis = self.create_impact_analysis(event_correlations)
        
        # Generate report sections
        sections = await self.generate_report_sections(
            report_type, major_events, event_correlations,
            market_summary, commodity_summary, news_summary
        )
        
        # Calculate scores
        confidence_score = self.calculate_report_confidence(
            major_events, event_correlations, market_summary
        )
        event_driven = len(major_events) > 0
        canadian_relevance = self.calculate_canadian_relevance(major_events, event_correlations)
        
        report = SmartReportContent(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            report_type=report_type,
            market_summary=market_summary,
            commodity_summary=commodity_summary,
            news_summary=news_summary,
            major_events=major_events,
            event_correlations=event_correlations,
            market_narrative=market_narrative,
            impact_analysis=impact_analysis,
            headline_section=sections["headline"],
            market_section=sections["market"],
            commodity_section=sections["commodity"],
            events_section=sections["events"],
            outlook_section=sections["outlook"],
            confidence_score=confidence_score,
            event_driven=event_driven,
            canadian_relevance_score=canadian_relevance
        )
        
        return report
    
    async def collect_major_events(self, days_back: int) -> List[BreakingNewsEvent]:
        """Collect major events from the specified period"""
        # Get fresh breaking news
        await self.news_monitor.monitor_all_sources(hours_back=24)
        
        # Get significant events from database
        hours_back = days_back * 24
        events = self.news_monitor.get_recent_breaking_news(
            hours_back=hours_back,
            min_priority=self.significance_thresholds["notable_event"]
        )
        
        # Filter and prioritize for Canadian mining relevance
        relevant_events = []
        for event in events:
            if (event.canadian_relevance >= 30.0 or 
                event.priority_score >= self.significance_thresholds["major_event"] or
                any(commodity in event.commodity_impact for commodity in ["copper", "gold", "silver"])):
                relevant_events.append(event)
        
        # Sort by combined priority and relevance
        relevant_events.sort(
            key=lambda x: (x.priority_score + x.canadian_relevance), 
            reverse=True
        )
        
        return relevant_events[:10]  # Top 10 most significant events
    
    async def analyze_event_correlations(self, events: List[BreakingNewsEvent]) -> List[EventCorrelation]:
        """Analyze market correlations for major events"""
        correlations = []
        
        for event in events:
            if event.priority_score >= self.significance_thresholds["major_event"]:
                try:
                    correlation = await self.correlation_engine.analyze_event_market_impact(event)
                    correlations.append(correlation)
                except Exception as e:
                    print(f"⚠️ Error analyzing correlation for {event.headline[:50]}: {e}")
        
        # Sort by impact strength
        correlations.sort(key=lambda x: x.overall_impact_score, reverse=True)
        return correlations
    
    async def generate_market_summary(self, days_back: int) -> Dict:
        """Generate market performance summary"""
        # This would integrate with existing market screening systems
        # For now, return a basic structure
        return {
            "period_days": days_back,
            "major_movers": [],
            "sector_performance": {},
            "volume_trends": {},
            "volatility_assessment": "moderate"
        }
    
    async def generate_commodity_summary(self, days_back: int) -> Dict:
        """Generate commodity performance summary"""
        # This would integrate with existing commodity tracking
        return {
            "period_days": days_back,
            "commodity_changes": {},
            "trend_analysis": {},
            "volatility_flags": []
        }
    
    async def generate_news_summary(self, days_back: int) -> Dict:
        """Generate news activity summary"""
        return {
            "period_days": days_back,
            "total_articles": 0,
            "major_themes": [],
            "company_mentions": {},
            "sentiment_overview": "neutral"
        }
    
    def create_market_narrative(self, events: List[BreakingNewsEvent], 
                              correlations: List[EventCorrelation]) -> str:
        """Create overarching market narrative"""
        if not events:
            return "Standard market activity with no major disruptions during the period."
        
        narrative_parts = []
        
        # Lead with most significant event
        top_event = events[0]
        if top_event.priority_score >= self.significance_thresholds["critical_event"]:
            narrative_parts.append(f"Market dominated by {top_event.headline.lower()}")
        elif top_event.priority_score >= self.significance_thresholds["major_event"]:
            narrative_parts.append(f"Significant market development: {top_event.headline.lower()}")
        
        # Add correlation insights
        if correlations:
            top_correlation = correlations[0]
            if top_correlation.correlation_strength in ["strong", "moderate"]:
                narrative_parts.append(f"with {top_correlation.correlation_strength} correlation to Canadian mining performance")
        
        # Add secondary themes
        policy_events = [e for e in events if e.event_type == "policy"]
        market_events = [e for e in events if e.event_type == "market_move"]
        
        if len(policy_events) > 1:
            narrative_parts.append("amid broader policy uncertainty")
        elif len(market_events) > 2:
            narrative_parts.append("reflecting elevated market volatility")
        
        return ". ".join(narrative_parts) + "."
    
    def create_impact_analysis(self, correlations: List[EventCorrelation]) -> str:
        """Create detailed impact analysis"""
        if not correlations:
            return "Limited direct market impact observed."
        
        analysis_parts = []
        
        # Overall impact assessment
        total_impact = sum(c.overall_impact_score for c in correlations) / len(correlations)
        if total_impact >= 15:
            analysis_parts.append("Significant market disruption with measurable impacts across the sector")
        elif total_impact >= 8:
            analysis_parts.append("Moderate market impact with selective stock movements")
        else:
            analysis_parts.append("Limited market impact despite news attention")
        
        # Canadian mining specific impact
        canadian_impacts = [c.canadian_mining_impact for c in correlations if c.canadian_mining_impact > 0]
        if canadian_impacts:
            avg_canadian_impact = sum(canadian_impacts) / len(canadian_impacts)
            if avg_canadian_impact >= 3:
                analysis_parts.append(f"Canadian mining sector showed pronounced reaction with average movement of {avg_canadian_impact:.1f}%")
        
        # Commodity correlation
        strong_correlations = [c for c in correlations if c.correlation_strength == "strong"]
        if strong_correlations:
            analysis_parts.append(f"{len(strong_correlations)} events showed strong market correlation")
        
        return ". ".join(analysis_parts) + "."
    
    async def generate_report_sections(self, report_type: str, events: List[BreakingNewsEvent],
                                     correlations: List[EventCorrelation], market_summary: Dict,
                                     commodity_summary: Dict, news_summary: Dict) -> Dict[str, str]:
        """Generate formatted report sections"""
        
        sections = {}
        
        # Headline section
        if events and events[0].priority_score >= self.significance_thresholds["major_event"]:
            sections["headline"] = f"🚨 WEEK'S MAJOR DEVELOPMENT\n{events[0].headline}"
        else:
            if report_type == "saturday_wrap":
                sections["headline"] = "📊 WEEKLY MARKET SUMMARY"
            else:
                sections["headline"] = "🔮 WEEK AHEAD OUTLOOK"
        
        # Events section
        if events:
            events_lines = []
            for i, event in enumerate(events[:5], 1):
                impact_emoji = self.get_impact_emoji(event.priority_score)
                events_lines.append(f"{impact_emoji} {event.headline}")
                
                # Add correlation info if available
                event_correlation = next((c for c in correlations if c.event_id == event.id), None)
                if event_correlation and event_correlation.correlation_strength in ["strong", "moderate"]:
                    events_lines.append(f"   Market Impact: {event_correlation.primary_impact}")
            
            sections["events"] = "📰 MAJOR DEVELOPMENTS\n" + "\n".join(events_lines)
        else:
            sections["events"] = "📰 MARKET DEVELOPMENTS\n• Standard industry activity this period"
        
        # Market section with event context
        market_lines = ["📈 MARKET PERFORMANCE"]
        
        if correlations:
            significant_correlations = [c for c in correlations if c.overall_impact_score >= 10]
            if significant_correlations:
                market_lines.append("• Event-driven volatility observed")
                for correlation in significant_correlations[:3]:
                    market_lines.append(f"• {correlation.market_narrative}")
        else:
            market_lines.append("• Standard trading patterns")
        
        sections["market"] = "\n".join(market_lines)
        
        # Commodity section with event impacts
        commodity_lines = ["💰 COMMODITY SPOTLIGHT"]
        
        # Aggregate commodity impacts from events
        commodity_impacts = {}
        for event in events:
            for commodity, impact in event.commodity_impact.items():
                if commodity not in commodity_impacts:
                    commodity_impacts[commodity] = []
                commodity_impacts[commodity].append((event.headline, impact))
        
        if commodity_impacts:
            for commodity, impacts in commodity_impacts.items():
                if impacts:
                    avg_impact = sum(impact[1] for impact in impacts) / len(impacts)
                    if abs(avg_impact) >= 5:
                        direction = "⬆️" if avg_impact > 0 else "⬇️"
                        commodity_lines.append(f"{direction} {commodity}: Multiple events driving volatility")
        else:
            commodity_lines.append("• Stable commodity price environment")
        
        sections["commodity"] = "\n".join(commodity_lines)
        
        # Outlook section
        if report_type == "saturday_wrap":
            outlook_lines = ["💡 WEEK'S TAKEAWAY"]
            if events:
                policy_events = [e for e in events if e.event_type == "policy"]
                if policy_events:
                    outlook_lines.append("• Policy developments continue to drive market sentiment")
                else:
                    outlook_lines.append("• Market focusing on operational fundamentals")
            else:
                outlook_lines.append("• Steady progression in Canadian mining sector")
        else:  # sunday_preview
            outlook_lines = ["🎯 WEEK AHEAD FOCUS"]
            outlook_lines.append("• Monitor ongoing event impacts")
            outlook_lines.append("• Watch for policy development continuations")
        
        sections["outlook"] = "\n".join(outlook_lines)
        
        return sections
    
    def get_impact_emoji(self, priority_score: float) -> str:
        """Get emoji based on event priority score"""
        if priority_score >= self.significance_thresholds["critical_event"]:
            return "🚨"
        elif priority_score >= self.significance_thresholds["major_event"]:
            return "⚡"
        elif priority_score >= self.significance_thresholds["notable_event"]:
            return "📍"
        else:
            return "•"
    
    def calculate_report_confidence(self, events: List[BreakingNewsEvent],
                                  correlations: List[EventCorrelation],
                                  market_summary: Dict) -> float:
        """Calculate confidence score for the report"""
        base_confidence = 50.0
        
        # Event quality boost
        if events:
            avg_event_priority = sum(e.priority_score for e in events) / len(events)
            base_confidence += (avg_event_priority / 100.0) * 30
        
        # Correlation analysis boost
        if correlations:
            strong_correlations = [c for c in correlations if c.correlation_strength == "strong"]
            base_confidence += len(strong_correlations) * 10
        
        # Data availability boost
        base_confidence += 10  # Base data availability
        
        return min(base_confidence, 100.0)
    
    def calculate_canadian_relevance(self, events: List[BreakingNewsEvent],
                                   correlations: List[EventCorrelation]) -> float:
        """Calculate Canadian mining relevance score"""
        if not events:
            return 30.0  # Base relevance
        
        total_relevance = 0.0
        total_weight = 0.0
        
        for event in events:
            weight = event.priority_score / 100.0
            total_relevance += event.canadian_relevance * weight
            total_weight += weight
        
        # Boost for strong correlations
        strong_correlations = [c for c in correlations if c.correlation_strength == "strong"]
        if strong_correlations:
            correlation_boost = len(strong_correlations) * 10
            total_relevance += correlation_boost
        
        return min(total_relevance / total_weight if total_weight > 0 else 30.0, 100.0)
    
    def format_linkedin_post(self, report: SmartReportContent) -> str:
        """Format report as LinkedIn post"""
        
        # Determine post style based on events
        if report.event_driven and report.major_events:
            top_event = report.major_events[0]
            if top_event.priority_score >= self.significance_thresholds["critical_event"]:
                return self.format_event_driven_post(report, top_event)
        
        # Standard format with event integration
        return self.format_standard_post_with_events(report)
    
    def format_event_driven_post(self, report: SmartReportContent, top_event: BreakingNewsEvent) -> str:
        """Format event-driven LinkedIn post"""
        
        lines = []
        
        # Header with event focus
        lines.append(f"🚨 BREAKING: Canadian Mining Impact")
        lines.append("")
        
        # Main event
        lines.append(f"📰 {top_event.headline}")
        lines.append("")
        
        # Market impact
        event_correlation = next(
            (c for c in report.event_correlations if c.event_id == top_event.id), 
            None
        )
        
        if event_correlation:
            lines.append("📊 MARKET REACTION")
            lines.append(f"• {event_correlation.primary_impact}")
            if event_correlation.canadian_mining_impact > 0:
                lines.append(f"• Canadian mining sector: {event_correlation.canadian_mining_impact:.1f}% average movement")
            lines.append("")
        
        # Commodity impact
        if top_event.commodity_impact:
            lines.append("💰 COMMODITY IMPACT")
            for commodity, impact in top_event.commodity_impact.items():
                if abs(impact) >= 5:
                    direction = "↗️" if impact > 0 else "↘️"
                    lines.append(f"{direction} {commodity}: Event-driven volatility")
            lines.append("")
        
        # Context and outlook
        lines.append("🎯 IMPLICATIONS")
        lines.append(f"• {report.impact_analysis}")
        lines.append("")
        
        lines.append("#CanadianMining #BreakingNews #MiningStocks #CommodityMarkets")
        
        return "\n".join(lines)
    
    def format_standard_post_with_events(self, report: SmartReportContent) -> str:
        """Format standard post with event integration"""
        
        lines = []
        
        # Header
        if report.report_type == "saturday_wrap":
            week_start = (datetime.now() - timedelta(days=6)).strftime("%b %d")
            week_end = datetime.now().strftime("%b %d")
            lines.append(f"📊 Canadian Mining Week Wrap - {week_start} to {week_end}")
        else:
            next_week = (datetime.now() + timedelta(days=1)).strftime("Week of %b %d")
            lines.append(f"🔮 Mining Week Ahead - {next_week}")
        
        lines.append("")
        
        # Events section (if significant)
        if report.major_events:
            significant_events = [e for e in report.major_events 
                                if e.priority_score >= self.significance_thresholds["major_event"]]
            if significant_events:
                lines.append("⚡ WEEK'S KEY EVENTS")
                for event in significant_events[:3]:
                    lines.append(f"• {event.headline}")
                lines.append("")
        
        # Market section
        lines.append(report.market_section)
        lines.append("")
        
        # Commodity section
        lines.append(report.commodity_section)
        lines.append("")
        
        # Takeaway
        lines.append(report.outlook_section)
        lines.append("")
        
        # Footer
        lines.append(f"📊 Confidence: {report.confidence_score:.0f}% | Canadian Relevance: {report.canadian_relevance_score:.0f}%")
        lines.append("")
        lines.append("#CanadianMining #TSX #MiningStocks #ResourceSector #WeeklyWrap")
        
        return "\n".join(lines)

async def main():
    """Test the smart report generator"""
    print("🧠 Smart Report Generator Test")
    print("=" * 60)
    
    generator = SmartReportGenerator()
    
    # Generate Saturday wrap report
    print("📊 Generating Saturday wrap report...")
    saturday_report = await generator.generate_smart_weekend_report("saturday_wrap")
    
    print(f"\n✅ Saturday Report Generated:")
    print(f"📅 Date: {saturday_report.report_date}")
    print(f"🎯 Event-driven: {saturday_report.event_driven}")
    print(f"📊 Confidence: {saturday_report.confidence_score:.1f}%")
    print(f"🇨🇦 Canadian Relevance: {saturday_report.canadian_relevance_score:.1f}%")
    print(f"📰 Major Events: {len(saturday_report.major_events)}")
    print(f"🔗 Correlations: {len(saturday_report.event_correlations)}")
    
    if saturday_report.major_events:
        print("\n📰 Top Events:")
        for i, event in enumerate(saturday_report.major_events[:3], 1):
            print(f"  {i}. [{event.priority_score:.0f}] {event.headline}")
    
    print(f"\n📰 Market Narrative: {saturday_report.market_narrative}")
    print(f"📊 Impact Analysis: {saturday_report.impact_analysis}")
    
    # Generate LinkedIn post
    print("\n📱 LinkedIn Post:")
    print("=" * 50)
    linkedin_post = generator.format_linkedin_post(saturday_report)
    print(linkedin_post)
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())