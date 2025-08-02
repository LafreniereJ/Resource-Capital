#!/usr/bin/env python3
"""
Enhanced News Intelligence System
Integrates robust web scraping with breaking news analysis and company correlation
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from robust_web_scraper import RobustWebScraper, ScrapingResult
from breaking_news_monitor import BreakingNewsMonitor, BreakingNewsEvent

class EnhancedNewsIntelligenceSystem:
    """Complete news intelligence system combining scraping, analysis, and correlation"""
    
    def __init__(self):
        self.scraper = None
        self.news_monitor = BreakingNewsMonitor()
        self.enhanced_dataset_config = self.load_enhanced_dataset_config()
    
    def load_enhanced_dataset_config(self) -> Dict:
        """Load enhanced dataset configuration for company correlation"""
        try:
            with open('../../data/processed/breaking_news_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load enhanced dataset config: {e}")
            return {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.scraper = RobustWebScraper()
        await self.scraper.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.scraper:
            await self.scraper.__aexit__(exc_type, exc_val, exc_tb)
    
    async def comprehensive_news_scan(self, hours_back: int = 6) -> Dict:
        """Perform comprehensive news scanning and analysis"""
        print(f"🔍 COMPREHENSIVE NEWS INTELLIGENCE SCAN")
        print("=" * 70)
        
        # Step 1: Robust multi-website scraping
        print(f"📡 Step 1: Multi-website scraping ({len(self.scraper.scraping_targets)} sources)...")
        scraping_results = await self.scraper.scrape_all_targets()
        
        # Step 2: Collect all events
        all_events = []
        for result in scraping_results:
            all_events.extend(result.events)
        
        print(f"   Scraped {len(all_events)} total events from {len(scraping_results)} sources")
        
        # Step 3: Priority analysis and scoring
        print(f"🎯 Step 2: Priority analysis and scoring...")
        scored_events = []
        
        for event in all_events:
            # Get source weight from scraping config
            source_weight = 1.0
            for target in self.scraper.scraping_targets:
                if target.name == event.source:
                    source_weight = target.priority_weight
                    break
            
            # Analyze priority
            self.news_monitor.analyze_event_priority(event, source_weight)
            
            # Filter for relevant events
            if event.priority_score > 0 or event.canadian_relevance > 0:
                scored_events.append(event)
        
        # Sort by priority
        scored_events.sort(key=lambda x: x.priority_score, reverse=True)
        
        print(f"   Identified {len(scored_events)} relevant events")
        high_priority = [e for e in scored_events if e.priority_score >= 50.0]
        print(f"   High-priority events: {len(high_priority)}")
        
        # Step 4: Company correlation
        print(f"🔗 Step 3: Company correlation analysis...")
        correlated_events = self.correlate_with_companies(high_priority)
        
        # Step 5: Save to database
        print(f"💾 Step 4: Database storage...")
        if high_priority:
            self.news_monitor.save_breaking_news(high_priority)
        
        # Step 6: Generate intelligence summary
        print(f"📊 Step 5: Intelligence summary generation...")
        
        summary = {
            'scan_timestamp': datetime.now().isoformat(),
            'hours_scanned': hours_back,
            'scraping_summary': self.scraper.generate_scraping_summary(scraping_results),
            'total_events_found': len(all_events),
            'relevant_events': len(scored_events),
            'high_priority_events': len(high_priority),
            'critical_events': len([e for e in scored_events if e.impact_level == 'critical']),
            'top_events': [
                {
                    'headline': e.headline,
                    'source': e.source,
                    'priority_score': e.priority_score,
                    'impact_level': e.impact_level,
                    'canadian_relevance': e.canadian_relevance,
                    'commodity_impacts': e.commodity_impact,
                    'url': e.url
                }
                for e in high_priority[:5]
            ],
            'commodity_analysis': self.analyze_commodity_impacts(scored_events),
            'company_correlations': correlated_events,
            'source_performance': {
                result.target_name: {
                    'success': result.success,
                    'events_found': len(result.events),
                    'response_time': result.response_time
                }
                for result in scraping_results
            }
        }
        
        return summary
    
    def correlate_with_companies(self, events: List[BreakingNewsEvent]) -> Dict:
        """Correlate events with companies from enhanced dataset"""
        correlations = {
            'commodity_impacts': {},
            'affected_companies': [],
            'sector_alerts': []
        }
        
        if not self.enhanced_dataset_config:
            return correlations
        
        commodity_companies = self.enhanced_dataset_config.get('commodity_focused_companies', {})
        high_priority_tickers = self.enhanced_dataset_config.get('high_priority_tickers', [])
        
        for event in events:
            # Correlate commodity impacts
            if event.commodity_impact:
                for commodity, impact_score in event.commodity_impact.items():
                    if commodity.lower() in commodity_companies:
                        affected_cos = commodity_companies[commodity.lower()]
                        
                        correlations['commodity_impacts'][commodity] = {
                            'impact_score': impact_score,
                            'event_headline': event.headline,
                            'companies_count': len(affected_cos),
                            'top_companies': [
                                {
                                    'ticker': co.get('ticker', ''),
                                    'name': co.get('company_name', ''),
                                    'stage': co.get('company_stage', '')
                                }
                                for co in affected_cos[:5]
                            ]
                        }
            
            # Check for company-specific mentions
            headline_lower = event.headline.lower()
            summary_lower = event.summary.lower()
            
            # Simple company name matching (could be enhanced with NLP)
            for ticker in high_priority_tickers:
                if ticker.lower() in headline_lower or ticker.lower() in summary_lower:
                    correlations['affected_companies'].append({
                        'ticker': ticker,
                        'event_headline': event.headline,
                        'priority_score': event.priority_score,
                        'mention_type': 'direct'
                    })
        
        return correlations
    
    def analyze_commodity_impacts(self, events: List[BreakingNewsEvent]) -> Dict:
        """Analyze commodity impacts across all events"""
        commodity_summary = {}
        
        for event in events:
            if event.commodity_impact:
                for commodity, impact in event.commodity_impact.items():
                    if commodity not in commodity_summary:
                        commodity_summary[commodity] = {
                            'total_impact': 0,
                            'event_count': 0,
                            'events': []
                        }
                    
                    commodity_summary[commodity]['total_impact'] += impact
                    commodity_summary[commodity]['event_count'] += 1
                    commodity_summary[commodity]['events'].append({
                        'headline': event.headline,
                        'impact': impact,
                        'priority': event.priority_score
                    })
        
        # Sort by total impact
        sorted_commodities = sorted(
            commodity_summary.items(),
            key=lambda x: x[1]['total_impact'],
            reverse=True
        )
        
        return dict(sorted_commodities)
    
    async def generate_intelligence_report(self, summary: Dict) -> str:
        """Generate comprehensive intelligence report"""
        report = []
        
        report.append("🔍 MINING INTELLIGENCE COMPREHENSIVE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {summary['scan_timestamp']}")
        report.append(f"Scan Period: {summary['hours_scanned']} hours")
        
        # Executive Summary
        report.append("\n📊 EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"• Total Events Monitored: {summary['total_events_found']}")
        report.append(f"• Relevant Mining Events: {summary['relevant_events']}")
        report.append(f"• High-Priority Alerts: {summary['high_priority_events']}")
        report.append(f"• Critical Events: {summary['critical_events']}")
        
        # Source Performance
        report.append("\n📡 SOURCE PERFORMANCE")
        report.append("-" * 40)
        scraping_summary = summary['scraping_summary']
        report.append(f"• Success Rate: {scraping_summary['success_rate']:.1%}")
        report.append(f"• Average Response Time: {scraping_summary['average_response_time']:.2f}s")
        
        # Top performing sources
        for source, perf in summary['source_performance'].items():
            if perf['success']:
                report.append(f"  ✅ {source}: {perf['events_found']} events ({perf['response_time']:.2f}s)")
            else:
                report.append(f"  ❌ {source}: Failed")
        
        # Top Events
        if summary['top_events']:
            report.append("\n🚨 TOP PRIORITY EVENTS")
            report.append("-" * 40)
            for i, event in enumerate(summary['top_events'], 1):
                report.append(f"{i}. PRIORITY {event['priority_score']:6.1f} - {event['impact_level'].upper()}")
                report.append(f"   {event['headline']}")
                report.append(f"   Source: {event['source']} | Canadian Relevance: {event['canadian_relevance']:.1f}")
                if event['commodity_impacts']:
                    report.append(f"   Commodity Impacts: {event['commodity_impacts']}")
                report.append("")
        
        # Commodity Analysis
        if summary['commodity_analysis']:
            report.append("\n💎 COMMODITY IMPACT ANALYSIS")
            report.append("-" * 40)
            for commodity, data in summary['commodity_analysis'].items():
                report.append(f"• {commodity.upper()}: {data['total_impact']:.1f} impact points ({data['event_count']} events)")
        
        # Company Correlations
        correlations = summary['company_correlations']
        if correlations['commodity_impacts']:
            report.append("\n🏢 COMPANY IMPACT CORRELATIONS")
            report.append("-" * 40)
            for commodity, impact_data in correlations['commodity_impacts'].items():
                report.append(f"• {commodity.upper()} - {impact_data['companies_count']} companies affected")
                report.append(f"  Event: {impact_data['event_headline'][:60]}...")
                for company in impact_data['top_companies']:
                    report.append(f"    {company['ticker']}: {company['name']} ({company['stage']})")
        
        if correlations['affected_companies']:
            report.append("\n🎯 DIRECTLY MENTIONED COMPANIES")
            report.append("-" * 40)
            for company in correlations['affected_companies'][:10]:
                report.append(f"• {company['ticker']}: {company['event_headline'][:50]}...")
        
        report.append("\n" + "=" * 80)
        report.append("🎯 Report generated by Enhanced Mining Intelligence System")
        
        return "\n".join(report)

async def main():
    """Test the enhanced news intelligence system"""
    print("🚀 TESTING ENHANCED NEWS INTELLIGENCE SYSTEM")
    print("=" * 80)
    
    async with EnhancedNewsIntelligenceSystem() as system:
        # Perform comprehensive scan
        summary = await system.comprehensive_news_scan(hours_back=12)
        
        # Generate intelligence report
        report = await system.generate_intelligence_report(summary)
        
        print("\n" + report)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"../../data/processed/enhanced_intelligence_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Full report saved to: {report_file}")
        
        # Save summary JSON
        summary_file = f"../../data/processed/enhanced_intelligence_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📊 Summary data saved to: {summary_file}")

if __name__ == "__main__":
    asyncio.run(main())