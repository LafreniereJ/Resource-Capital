#!/usr/bin/env python3
"""
Event Correlation Engine
Links news events to market impacts, tracks policy-to-commodity relationships
"""

import asyncio
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
import numpy as np
from .breaking_news_monitor import BreakingNewsEvent, BreakingNewsMonitor

@dataclass
class MarketImpact:
    """Market impact data structure"""
    symbol: str
    company_name: str
    price_before: float
    price_after: float
    change_percent: float
    volume_ratio: float
    impact_score: float
    correlation_confidence: float

@dataclass
class CommodityImpact:
    """Commodity impact data structure"""
    commodity: str
    price_before: float
    price_after: float
    change_percent: float
    impact_score: float
    correlation_confidence: float

@dataclass
class EventCorrelation:
    """Event correlation analysis"""
    event_id: str
    event_headline: str
    event_timestamp: datetime
    event_type: str
    
    # Market impacts
    mining_stock_impacts: List[MarketImpact]
    commodity_impacts: List[CommodityImpact]
    
    # Analysis metrics
    overall_impact_score: float
    canadian_mining_impact: float
    correlation_strength: str  # "strong", "moderate", "weak", "none"
    
    # Insights
    primary_impact: str
    secondary_effects: List[str]
    market_narrative: str

class EventCorrelationEngine:
    """Correlates news events with market movements"""
    
    def __init__(self, db_path: str = "data/databases/mining_intelligence.db"):
        self.db_path = db_path
        self.news_monitor = BreakingNewsMonitor(db_path)
        
        # Canadian mining stock universe
        self.canadian_mining_stocks = {
            # Major Producers
            "ABX.TO": "Barrick Gold Corporation",
            "AEM.TO": "Agnico Eagle Mines Limited", 
            "K.TO": "Kinross Gold Corporation",
            "FM.TO": "First Quantum Minerals Ltd.",
            "LUN.TO": "Lundin Mining Corporation",
            "HBM.TO": "Hudbay Minerals Inc.",
            "TECK-B.TO": "Teck Resources Limited",
            "ELD.TO": "Eldorado Gold Corporation",
            "CG.TO": "Centerra Gold Inc.",
            "IMG.TO": "IAMGOLD Corporation",
            "KL.TO": "Kirkland Lake Gold Ltd.",
            "YRI.TO": "Yamana Gold Inc.",
            "BTO.TO": "B2Gold Corp.",
            "TXG.TO": "Torex Gold Resources Inc.",
            "SEA.TO": "Seabridge Gold Inc.",
            "AGI.TO": "Alamos Gold Inc.",
            
            # Mid-tier and Development
            "FNV.TO": "Franco-Nevada Corporation",
            "WPM.TO": "Wheaton Precious Metals Corp.",
            "SIL.TO": "SilverCrest Metals Inc.",
            "PAAS.TO": "Pan American Silver Corp.",
            "SSL.TO": "Sandstorm Gold Ltd.",
            "OR.TO": "Osisko Gold Royalties Ltd",
            "MAG.TO": "MAG Silver Corp.",
            "CXB.TO": "Calibre Mining Corp.",
            "EDV.TO": "Endeavour Mining Corporation",
            "MINE.TO": "Magna Mining Inc."
        }
        
        # Commodity ETF mappings
        self.commodity_etfs = {
            "Gold": "GLD",
            "Silver": "SLV", 
            "Copper": "CPER",
            "Platinum": "PPLT",
            "Uranium": "URA",
            "Oil": "USO",
            "Natural Gas": "UNG"
        }
        
        # Event-to-impact patterns
        self.impact_patterns = {
            "tariff_announcement": {
                "primary_commodities": ["Copper", "Steel", "Aluminum"],
                "impact_direction": "negative_foreign_positive_domestic",
                "timeline_hours": 24,
                "strength_multiplier": 2.0
            },
            "trade_war_escalation": {
                "primary_commodities": ["Copper", "Gold", "Silver"],
                "impact_direction": "negative_industrial_positive_safe_haven",
                "timeline_hours": 48,
                "strength_multiplier": 1.5
            },
            "fed_policy_change": {
                "primary_commodities": ["Gold", "Silver"],
                "impact_direction": "inverse_dollar",
                "timeline_hours": 12,
                "strength_multiplier": 1.8
            },
            "supply_disruption": {
                "primary_commodities": ["depends_on_source"],
                "impact_direction": "positive_commodity",
                "timeline_hours": 6,
                "strength_multiplier": 3.0
            }
        }
        
        self.setup_correlation_database()
    
    def setup_correlation_database(self):
        """Setup database for correlation tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_correlations (
                id TEXT PRIMARY KEY,
                event_id TEXT,
                event_headline TEXT,
                event_timestamp TIMESTAMP,
                event_type TEXT,
                overall_impact_score REAL,
                canadian_mining_impact REAL,
                correlation_strength TEXT,
                primary_impact TEXT,
                secondary_effects TEXT,
                market_narrative TEXT,
                mining_impacts TEXT,
                commodity_impacts TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES breaking_news (id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_event_timestamp ON event_correlations (event_timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    async def analyze_event_market_impact(self, event: BreakingNewsEvent, 
                                        analysis_window_hours: int = 24) -> EventCorrelation:
        """Analyze market impact of a specific news event"""
        print(f"🔍 Analyzing market impact for: {event.headline[:60]}...")
        
        # Define time windows around event
        event_time = event.published
        before_start = event_time - timedelta(hours=2)  # 2 hours before
        before_end = event_time
        after_start = event_time
        after_end = event_time + timedelta(hours=analysis_window_hours)
        
        # Analyze mining stock impacts
        mining_impacts = await self.analyze_mining_stock_impacts(
            before_start, before_end, after_start, after_end, event
        )
        
        # Analyze commodity impacts
        commodity_impacts = await self.analyze_commodity_impacts(
            before_start, before_end, after_start, after_end, event
        )
        
        # Calculate overall impact metrics
        overall_impact = self.calculate_overall_impact(mining_impacts, commodity_impacts, event)
        canadian_impact = self.calculate_canadian_mining_impact(mining_impacts)
        correlation_strength = self.determine_correlation_strength(overall_impact, event)
        
        # Generate market narrative
        narrative = self.generate_market_narrative(event, mining_impacts, commodity_impacts)
        
        # Identify primary and secondary effects
        primary_impact, secondary_effects = self.identify_impact_hierarchy(
            mining_impacts, commodity_impacts, event
        )
        
        correlation = EventCorrelation(
            event_id=event.id,
            event_headline=event.headline,
            event_timestamp=event.published,
            event_type=event.event_type,
            mining_stock_impacts=mining_impacts,
            commodity_impacts=commodity_impacts,
            overall_impact_score=overall_impact,
            canadian_mining_impact=canadian_impact,
            correlation_strength=correlation_strength,
            primary_impact=primary_impact,
            secondary_effects=secondary_effects,
            market_narrative=narrative
        )
        
        # Save correlation analysis
        self.save_correlation_analysis(correlation)
        
        return correlation
    
    async def analyze_mining_stock_impacts(self, before_start: datetime, before_end: datetime,
                                         after_start: datetime, after_end: datetime,
                                         event: BreakingNewsEvent) -> List[MarketImpact]:
        """Analyze impact on Canadian mining stocks"""
        impacts = []
        
        # Select relevant stocks based on event
        relevant_stocks = self.select_relevant_stocks(event)
        
        for symbol, company_name in relevant_stocks.items():
            try:
                ticker = yf.Ticker(symbol)
                
                # Get price data around event
                hist_data = ticker.history(
                    start=before_start.date(),
                    end=(after_end + timedelta(days=1)).date(),
                    interval="1h"
                )
                
                if hist_data.empty:
                    continue
                
                # Calculate before/after prices
                before_data = hist_data[
                    (hist_data.index >= before_start) & (hist_data.index <= before_end)
                ]
                after_data = hist_data[
                    (hist_data.index >= after_start) & (hist_data.index <= after_end)
                ]
                
                if before_data.empty or after_data.empty:
                    continue
                
                price_before = before_data['Close'].mean()
                price_after = after_data['Close'].mean()
                change_percent = ((price_after - price_before) / price_before) * 100
                
                # Volume analysis
                volume_before = before_data['Volume'].mean()
                volume_after = after_data['Volume'].mean()
                volume_ratio = volume_after / volume_before if volume_before > 0 else 1.0
                
                # Calculate impact score
                impact_score = self.calculate_stock_impact_score(
                    change_percent, volume_ratio, event, symbol
                )
                
                # Correlation confidence
                correlation_confidence = self.calculate_correlation_confidence(
                    change_percent, volume_ratio, event, symbol
                )
                
                impact = MarketImpact(
                    symbol=symbol,
                    company_name=company_name,
                    price_before=round(price_before, 2),
                    price_after=round(price_after, 2),
                    change_percent=round(change_percent, 2),
                    volume_ratio=round(volume_ratio, 2),
                    impact_score=round(impact_score, 1),
                    correlation_confidence=round(correlation_confidence, 2)
                )
                
                impacts.append(impact)
                
            except Exception as e:
                print(f"⚠️ Error analyzing {symbol}: {e}")
                continue
        
        # Sort by impact score
        impacts.sort(key=lambda x: abs(x.impact_score), reverse=True)
        return impacts[:20]  # Return top 20 impacts
    
    async def analyze_commodity_impacts(self, before_start: datetime, before_end: datetime,
                                      after_start: datetime, after_end: datetime,
                                      event: BreakingNewsEvent) -> List[CommodityImpact]:
        """Analyze impact on commodity prices"""
        impacts = []
        
        # Select relevant commodities based on event
        relevant_commodities = self.select_relevant_commodities(event)
        
        for commodity, etf_symbol in relevant_commodities.items():
            try:
                ticker = yf.Ticker(etf_symbol)
                
                # Get price data around event
                hist_data = ticker.history(
                    start=before_start.date(),
                    end=(after_end + timedelta(days=1)).date(),
                    interval="1h"
                )
                
                if hist_data.empty:
                    continue
                
                # Calculate before/after prices
                before_data = hist_data[
                    (hist_data.index >= before_start) & (hist_data.index <= before_end)
                ]
                after_data = hist_data[
                    (hist_data.index >= after_start) & (hist_data.index <= after_end)
                ]
                
                if before_data.empty or after_data.empty:
                    continue
                
                price_before = before_data['Close'].mean()
                price_after = after_data['Close'].mean()
                change_percent = ((price_after - price_before) / price_before) * 100
                
                # Calculate impact score
                impact_score = self.calculate_commodity_impact_score(
                    change_percent, event, commodity
                )
                
                # Correlation confidence
                correlation_confidence = self.calculate_commodity_correlation_confidence(
                    change_percent, event, commodity
                )
                
                impact = CommodityImpact(
                    commodity=commodity,
                    price_before=round(price_before, 2),
                    price_after=round(price_after, 2),
                    change_percent=round(change_percent, 2),
                    impact_score=round(impact_score, 1),
                    correlation_confidence=round(correlation_confidence, 2)
                )
                
                impacts.append(impact)
                
            except Exception as e:
                print(f"⚠️ Error analyzing {commodity}: {e}")
                continue
        
        # Sort by impact score
        impacts.sort(key=lambda x: abs(x.impact_score), reverse=True)
        return impacts
    
    def select_relevant_stocks(self, event: BreakingNewsEvent) -> Dict[str, str]:
        """Select stocks most likely to be affected by the event"""
        # Start with all Canadian mining stocks
        relevant_stocks = self.canadian_mining_stocks.copy()
        
        # Filter based on event characteristics
        if event.commodity_impact:
            # If specific commodities are mentioned, focus on relevant producers
            if "copper" in event.commodity_impact:
                copper_focused = {
                    "FM.TO": "First Quantum Minerals Ltd.",
                    "LUN.TO": "Lundin Mining Corporation", 
                    "HBM.TO": "Hudbay Minerals Inc.",
                    "TECK-B.TO": "Teck Resources Limited"
                }
                relevant_stocks.update(copper_focused)
            
            if "gold" in event.commodity_impact:
                gold_focused = {
                    "ABX.TO": "Barrick Gold Corporation",
                    "AEM.TO": "Agnico Eagle Mines Limited",
                    "K.TO": "Kinross Gold Corporation",
                    "KL.TO": "Kirkland Lake Gold Ltd."
                }
                relevant_stocks.update(gold_focused)
        
        # If companies are specifically mentioned, prioritize them
        if event.companies_affected:
            company_symbols = {}
            for company in event.companies_affected:
                for symbol, name in self.canadian_mining_stocks.items():
                    if company.lower() in name.lower():
                        company_symbols[symbol] = name
            if company_symbols:
                relevant_stocks = company_symbols
        
        return relevant_stocks
    
    def select_relevant_commodities(self, event: BreakingNewsEvent) -> Dict[str, str]:
        """Select commodities most likely to be affected by the event"""
        relevant_commodities = self.commodity_etfs.copy()
        
        # If specific commodities are mentioned in the event, prioritize them
        if event.commodity_impact:
            prioritized = {}
            for commodity in event.commodity_impact.keys():
                if commodity.title() in self.commodity_etfs:
                    prioritized[commodity.title()] = self.commodity_etfs[commodity.title()]
            if prioritized:
                # Add safe havens for policy events
                if event.event_type == "policy":
                    prioritized.update({
                        "Gold": "GLD",
                        "Silver": "SLV"
                    })
                relevant_commodities = prioritized
        
        return relevant_commodities
    
    def calculate_stock_impact_score(self, change_percent: float, volume_ratio: float,
                                   event: BreakingNewsEvent, symbol: str) -> float:
        """Calculate impact score for a stock"""
        base_score = abs(change_percent) * 10  # Base score from price movement
        
        # Volume boost
        if volume_ratio > 1.5:
            base_score *= 1.3
        elif volume_ratio > 2.0:
            base_score *= 1.6
        
        # Event relevance boost
        relevance_multiplier = 1.0
        if event.event_type == "policy" and "tariff" in event.headline.lower():
            relevance_multiplier = 2.0
        elif event.event_type == "market_move":
            relevance_multiplier = 1.5
        
        # Company-specific relevance
        if event.companies_affected:
            company_name = self.canadian_mining_stocks.get(symbol, "")
            for company in event.companies_affected:
                if company.lower() in company_name.lower():
                    relevance_multiplier *= 1.8
                    break
        
        return base_score * relevance_multiplier
    
    def calculate_commodity_impact_score(self, change_percent: float,
                                       event: BreakingNewsEvent, commodity: str) -> float:
        """Calculate impact score for a commodity"""
        base_score = abs(change_percent) * 15  # Commodities get higher base score
        
        # Event type multipliers
        if event.event_type == "policy":
            if "tariff" in event.headline.lower():
                base_score *= 2.5  # Tariffs have major commodity impact
            elif "trade" in event.headline.lower():
                base_score *= 1.8
        elif event.event_type == "market_move":
            base_score *= 1.3
        
        # Commodity-specific relevance
        if commodity.lower() in event.commodity_impact:
            base_score *= 2.0
        
        return base_score
    
    def calculate_correlation_confidence(self, change_percent: float, volume_ratio: float,
                                       event: BreakingNewsEvent, symbol: str) -> float:
        """Calculate confidence in the correlation"""
        confidence = 0.5  # Base confidence
        
        # Price movement magnitude
        if abs(change_percent) > 5:
            confidence += 0.3
        elif abs(change_percent) > 2:
            confidence += 0.2
        
        # Volume confirmation
        if volume_ratio > 2.0:
            confidence += 0.3
        elif volume_ratio > 1.5:
            confidence += 0.15
        
        # Event relevance
        if event.priority_score > 80:
            confidence += 0.2
        elif event.priority_score > 60:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def calculate_commodity_correlation_confidence(self, change_percent: float,
                                                 event: BreakingNewsEvent, commodity: str) -> float:
        """Calculate confidence in commodity correlation"""
        confidence = 0.6  # Base confidence (higher for commodities)
        
        # Price movement magnitude
        if abs(change_percent) > 3:
            confidence += 0.3
        elif abs(change_percent) > 1:
            confidence += 0.15
        
        # Direct mention in event
        if commodity.lower() in event.headline.lower() or commodity.lower() in event.summary.lower():
            confidence += 0.3
        
        # Event type relevance
        if event.event_type == "policy" and "tariff" in event.headline.lower():
            confidence += 0.4
        
        return min(confidence, 1.0)
    
    def calculate_overall_impact(self, mining_impacts: List[MarketImpact],
                               commodity_impacts: List[CommodityImpact],
                               event: BreakingNewsEvent) -> float:
        """Calculate overall impact score"""
        impact_score = 0.0
        
        # Mining stock impacts (weighted by market cap significance)
        if mining_impacts:
            top_impacts = [abs(impact.impact_score) for impact in mining_impacts[:10]]
            impact_score += sum(top_impacts) / len(top_impacts)
        
        # Commodity impacts (higher weight)
        if commodity_impacts:
            commodity_scores = [abs(impact.impact_score) for impact in commodity_impacts]
            impact_score += (sum(commodity_scores) / len(commodity_scores)) * 1.5
        
        # Event priority boost
        impact_score *= (event.priority_score / 100.0)
        
        return min(impact_score, 100.0)
    
    def calculate_canadian_mining_impact(self, mining_impacts: List[MarketImpact]) -> float:
        """Calculate specific impact on Canadian mining sector"""
        if not mining_impacts:
            return 0.0
        
        # Weight by company size (approximated by common knowledge)
        major_miners = ["ABX.TO", "AEM.TO", "K.TO", "FM.TO", "TECK-B.TO"]
        
        total_weighted_impact = 0.0
        total_weight = 0.0
        
        for impact in mining_impacts:
            weight = 2.0 if impact.symbol in major_miners else 1.0
            total_weighted_impact += abs(impact.change_percent) * weight
            total_weight += weight
        
        return total_weighted_impact / total_weight if total_weight > 0 else 0.0
    
    def determine_correlation_strength(self, overall_impact: float, event: BreakingNewsEvent) -> str:
        """Determine correlation strength"""
        if overall_impact >= 15 and event.priority_score >= 80:
            return "strong"
        elif overall_impact >= 8 and event.priority_score >= 60:
            return "moderate"
        elif overall_impact >= 3:
            return "weak"
        else:
            return "none"
    
    def generate_market_narrative(self, event: BreakingNewsEvent,
                                mining_impacts: List[MarketImpact],
                                commodity_impacts: List[CommodityImpact]) -> str:
        """Generate narrative explanation of market impact"""
        narrative_parts = []
        
        # Event description
        event_desc = f"Following {event.headline.lower()}"
        narrative_parts.append(event_desc)
        
        # Commodity impacts
        if commodity_impacts:
            top_commodity = commodity_impacts[0]
            if abs(top_commodity.change_percent) >= 2:
                direction = "surged" if top_commodity.change_percent > 0 else "declined"
                narrative_parts.append(
                    f"{top_commodity.commodity} {direction} {abs(top_commodity.change_percent):.1f}%"
                )
        
        # Mining stock impacts
        if mining_impacts:
            significant_impacts = [i for i in mining_impacts if abs(i.change_percent) >= 2]
            if significant_impacts:
                if len(significant_impacts) >= 3:
                    avg_change = sum(i.change_percent for i in significant_impacts) / len(significant_impacts)
                    direction = "gained" if avg_change > 0 else "declined"
                    narrative_parts.append(
                        f"Canadian mining stocks broadly {direction} with {len(significant_impacts)} companies showing significant moves"
                    )
                else:
                    for impact in significant_impacts[:2]:
                        direction = "gained" if impact.change_percent > 0 else "declined"
                        narrative_parts.append(
                            f"{impact.company_name} {direction} {abs(impact.change_percent):.1f}%"
                        )
        
        # Correlation assessment
        if event.event_type == "policy":
            narrative_parts.append("reflecting policy impact on resource sector")
        elif event.event_type == "market_move":
            narrative_parts.append("amid broader market volatility")
        
        return ". ".join(narrative_parts) + "."
    
    def identify_impact_hierarchy(self, mining_impacts: List[MarketImpact],
                                commodity_impacts: List[CommodityImpact],
                                event: BreakingNewsEvent) -> Tuple[str, List[str]]:
        """Identify primary and secondary effects"""
        primary_impact = "Limited market response"
        secondary_effects = []
        
        # Determine primary impact
        if commodity_impacts:
            top_commodity = commodity_impacts[0]
            if abs(top_commodity.change_percent) >= 3:
                direction = "surge" if top_commodity.change_percent > 0 else "decline"
                primary_impact = f"{top_commodity.commodity} {direction} of {abs(top_commodity.change_percent):.1f}%"
        
        # Secondary effects
        if mining_impacts:
            significant_mining = [i for i in mining_impacts if abs(i.change_percent) >= 2]
            if significant_mining:
                secondary_effects.append(f"Mining stock volatility ({len(significant_mining)} companies affected)")
        
        if event.event_type == "policy":
            secondary_effects.append("Policy uncertainty impact")
        
        if len(commodity_impacts) > 1:
            secondary_effects.append("Broader commodity market reaction")
        
        return primary_impact, secondary_effects
    
    def save_correlation_analysis(self, correlation: EventCorrelation):
        """Save correlation analysis to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert complex objects to JSON
        mining_impacts_json = json.dumps([asdict(impact) for impact in correlation.mining_stock_impacts])
        commodity_impacts_json = json.dumps([asdict(impact) for impact in correlation.commodity_impacts])
        secondary_effects_json = json.dumps(correlation.secondary_effects)
        
        correlation_id = f"corr_{correlation.event_id}_{int(correlation.event_timestamp.timestamp())}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO event_correlations
            (id, event_id, event_headline, event_timestamp, event_type,
             overall_impact_score, canadian_mining_impact, correlation_strength,
             primary_impact, secondary_effects, market_narrative,
             mining_impacts, commodity_impacts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            correlation_id, correlation.event_id, correlation.event_headline,
            correlation.event_timestamp, correlation.event_type,
            correlation.overall_impact_score, correlation.canadian_mining_impact,
            correlation.correlation_strength, correlation.primary_impact,
            secondary_effects_json, correlation.market_narrative,
            mining_impacts_json, commodity_impacts_json
        ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Saved correlation analysis for event: {correlation.event_headline[:50]}...")

async def main():
    """Test the event correlation engine"""
    print("🔍 Event Correlation Engine Test")
    print("=" * 60)
    
    # Initialize engines
    news_monitor = BreakingNewsMonitor()
    correlation_engine = EventCorrelationEngine()
    
    # Get recent high-priority events
    recent_events = news_monitor.get_recent_breaking_news(hours_back=48, min_priority=60.0)
    
    if recent_events:
        print(f"📊 Analyzing {len(recent_events)} high-priority events...")
        
        for event in recent_events[:3]:  # Analyze top 3 events
            print(f"\n🔍 Event: {event.headline}")
            
            correlation = await correlation_engine.analyze_event_market_impact(event)
            
            print(f"📈 Overall Impact Score: {correlation.overall_impact_score:.1f}")
            print(f"🇨🇦 Canadian Mining Impact: {correlation.canadian_mining_impact:.1f}%")
            print(f"🔗 Correlation Strength: {correlation.correlation_strength}")
            print(f"🎯 Primary Impact: {correlation.primary_impact}")
            print(f"📰 Market Narrative: {correlation.market_narrative}")
            
            if correlation.commodity_impacts:
                print("💎 Top Commodity Impacts:")
                for impact in correlation.commodity_impacts[:3]:
                    print(f"   {impact.commodity}: {impact.change_percent:+.1f}% (confidence: {impact.correlation_confidence:.2f})")
            
            if correlation.mining_stock_impacts:
                print("📊 Top Stock Impacts:")
                for impact in correlation.mining_stock_impacts[:3]:
                    print(f"   {impact.symbol}: {impact.change_percent:+.1f}% (impact score: {impact.impact_score:.1f})")
    
    else:
        print("ℹ️ No recent high-priority events found for correlation analysis")

if __name__ == "__main__":
    asyncio.run(main())