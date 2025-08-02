#!/usr/bin/env python3
"""
Week Ahead Generator
Creates Sunday preview content for the upcoming trading week
"""

import sys
import os
sys.path.append('../')

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

# Import existing modules
from .commodity_price_tracker import CommodityPriceTracker
from .daily_market_screener import DailyMarketScreener
from .news_intelligence_engine import NewsIntelligenceEngine

from ..core.config import Config

@dataclass
class WeekAheadPreview:
    """Week ahead preview data structure"""
    week_start: str
    key_events: List[str]
    watch_list: List[Dict]
    global_factors: List[str]
    commodity_outlook: List[str]
    weeks_theme: str
    economic_calendar: List[Dict]
    earnings_calendar: List[Dict]

class WeekAheadGenerator:
    """Generates Sunday week-ahead preview content"""
    
    def __init__(self):
        self.config = Config()
        self.commodity_tracker = CommodityPriceTracker()
        self.market_screener = DailyMarketScreener()
        self.news_engine = NewsIntelligenceEngine()
        
        # Economic indicators that affect mining
        self.economic_indicators = {
            'high_impact': [
                'Federal Reserve Meeting',
                'Interest Rate Decision', 
                'Inflation Data (CPI)',
                'GDP Release',
                'Employment Report',
                'China Economic Data'
            ],
            'medium_impact': [
                'Manufacturing PMI',
                'Consumer Confidence',
                'Retail Sales',
                'Industrial Production',
                'Currency Movements'
            ]
        }
        
        # Load Canadian companies for watch list generation
        self.canadian_companies = self._load_canadian_companies()
    
    def _load_canadian_companies(self) -> List[Dict]:
        """Load Canadian mining companies for watch list"""
        try:
            import pandas as pd
            
            # Load TSX companies (focus on larger companies for watch list)
            tsx_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSX Canadian Companies',
                header=8
            )
            
            # Also load some TSXV companies for watch list diversity
            tsxv_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSXV Canadian Companies',
                header=8
            )
            
            companies = []
            
            # TSX companies (use .TO suffix)
            for _, row in tsx_df.iterrows():
                if pd.notna(row.get('Symbol')):
                    companies.append({
                        'symbol': f"{row['Symbol']}.TO",
                        'name': row.get('Name', ''),
                        'exchange': 'TSX',
                        'sector': row.get('Sub-Industry', ''),
                        'province': row.get('Province', '')
                    })
            
            # TSXV companies (use .V suffix) - take first 50 for watch list
            for _, row in tsxv_df.head(50).iterrows():
                if pd.notna(row.get('Symbol')):
                    companies.append({
                        'symbol': f"{row['Symbol']}.V",
                        'name': row.get('Name', ''),
                        'exchange': 'TSXV',
                        'sector': row.get('Sub-Industry', ''),
                        'province': row.get('Province', '')
                    })
            
            return companies
            
        except Exception as e:
            print(f"⚠️ Error loading companies for watch list: {e}")
            return []
    
    def get_upcoming_week_dates(self) -> Tuple[datetime, datetime]:
        """Get the start and end dates of the upcoming trading week"""
        today = datetime.now()
        
        # If it's Sunday, get the upcoming week (Mon-Fri)
        if today.weekday() == 6:  # Sunday
            # Next Monday
            days_until_monday = 1
            week_start = today + timedelta(days=days_until_monday)
            week_end = week_start + timedelta(days=4)  # Friday
        else:
            # For testing on other days, get next week
            days_until_next_monday = 7 - today.weekday()
            week_start = today + timedelta(days=days_until_next_monday)
            week_end = week_start + timedelta(days=4)
        
        return week_start, week_end
    
    def generate_economic_calendar(self) -> List[Dict]:
        """Generate economic calendar for the upcoming week"""
        week_start, week_end = self.get_upcoming_week_dates()
        
        print(f"📅 Generating economic calendar for: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        
        # Since we're using free tools, we'll create a template of common weekly events
        # In production, this could integrate with free economic calendar APIs
        
        economic_events = []
        
        # Common weekly economic patterns
        week_start_date = week_start.strftime('%Y-%m-%d')
        
        # Monday events
        economic_events.append({
            'date': week_start.strftime('%A, %b %d'),
            'event': 'Week Opening - Global Market Assessment',
            'impact': 'medium',
            'description': 'Monitor overnight global developments'
        })
        
        # Tuesday events (common day for data releases)
        tuesday = week_start + timedelta(days=1)
        economic_events.append({
            'date': tuesday.strftime('%A, %b %d'),
            'event': 'Economic Data Watch',
            'impact': 'medium',
            'description': 'Potential inflation or employment data'
        })
        
        # Wednesday events (Fed meetings often occur)
        wednesday = week_start + timedelta(days=2)
        economic_events.append({
            'date': wednesday.strftime('%A, %b %d'),
            'event': 'Mid-Week Assessment',
            'impact': 'low',
            'description': 'Federal Reserve communications watch'
        })
        
        # Thursday events (weekly unemployment claims)
        thursday = week_start + timedelta(days=3)
        economic_events.append({
            'date': thursday.strftime('%A, %b %d'),
            'event': 'Weekly Economic Indicators',
            'impact': 'medium',
            'description': 'Unemployment claims and economic surveys'
        })
        
        # Friday events (monthly jobs report first Friday)
        friday = week_start + timedelta(days=4)
        if friday.day <= 7:  # First Friday of month
            economic_events.append({
                'date': friday.strftime('%A, %b %d'),
                'event': 'Monthly Employment Report',
                'impact': 'high',
                'description': 'Critical jobs data affecting Fed policy'
            })
        else:
            economic_events.append({
                'date': friday.strftime('%A, %b %d'),
                'event': 'Week Closing Assessment',
                'impact': 'low',
                'description': 'Weekly positioning and month-end flows'
            })
        
        return economic_events
    
    def generate_earnings_calendar(self) -> List[Dict]:
        """Generate mining company earnings calendar for upcoming week"""
        
        # Since we're using free tools, create a template of typical earnings patterns
        # In production, this could scrape company IR pages or use earnings APIs
        
        earnings_calendar = []
        week_start, week_end = self.get_upcoming_week_dates()
        
        # Common earnings seasons: Q1 (Apr-May), Q2 (Jul-Aug), Q3 (Oct-Nov), Q4 (Jan-Feb)
        current_month = datetime.now().month
        
        earnings_seasons = {
            1: "Q4 Earnings Season",  # January
            2: "Q4 Earnings Season",  # February  
            4: "Q1 Earnings Season",  # April
            5: "Q1 Earnings Season",  # May
            7: "Q2 Earnings Season",  # July
            8: "Q2 Earnings Season",  # August
            10: "Q3 Earnings Season", # October
            11: "Q3 Earnings Season"  # November
        }
        
        if current_month in earnings_seasons:
            earnings_calendar.append({
                'period': earnings_seasons[current_month],
                'companies': 'Multiple Canadian miners',
                'focus': 'Production results and guidance updates',
                'impact': 'Individual stock movements expected'
            })
        
        return earnings_calendar
    
    def generate_watch_list(self) -> List[Dict]:
        """Generate watch list of stocks to monitor for upcoming week"""
        
        watch_list = []
        
        try:
            # Use recent market data to identify stocks with potential catalysts
            recent_alerts = self.market_screener.screen_all_stocks(max_stocks=30)
            
            # Focus on stocks with recent momentum that might continue
            momentum_stocks = []
            for alert in recent_alerts:
                if abs(alert.change_pct_1d) >= 5.0:  # Significant recent move
                    momentum_stocks.append(alert)
            
            # Add top momentum stocks to watch list
            for stock in momentum_stocks[:3]:
                direction = "continuation" if stock.change_pct_1d > 0 else "reversal"
                # Clean symbol for display
                clean_symbol = stock.symbol.replace('.TO', '').replace('.V', '')
                watch_list.append({
                    'symbol': clean_symbol,
                    'reason': f"Monitor for {direction} after {stock.change_pct_1d:+.1f}% move",
                    'type': 'momentum'
                })
            
        except Exception as e:
            print(f"⚠️ Error generating momentum watch list: {e}")
        
        # Add some fundamental watch list items (major Canadian miners)
        fundamental_watches = [
            {
                'symbol': 'ABX',
                'reason': 'Gold price correlation and production updates',
                'type': 'fundamental'
            },
            {
                'symbol': 'SHOP', 
                'reason': 'Tech sector leader affecting TSX sentiment',
                'type': 'market_leader'
            },
            {
                'symbol': 'CNQ',
                'reason': 'Energy sector performance indicator',
                'type': 'sector_proxy'
            }
        ]
        
        # Add fundamental watches if we don't have enough momentum plays
        while len(watch_list) < 5:
            for item in fundamental_watches:
                if len(watch_list) < 5 and item not in watch_list:
                    watch_list.append(item)
                if len(watch_list) >= 5:
                    break
        
        return watch_list
    
    def generate_commodity_outlook(self) -> List[str]:
        """Generate commodity outlook for upcoming week"""
        
        outlook = []
        
        try:
            # Get current commodity data for context
            commodities = self.commodity_tracker.get_all_commodity_prices()
            
            for commodity in commodities:
                # Identify commodities with significant recent moves
                if abs(commodity.change_pct_1d) >= 2.0:
                    direction = "upward pressure" if commodity.change_pct_1d > 0 else "downward pressure"
                    outlook.append(f"{commodity.name}: {direction} continues after {commodity.change_pct_1d:+.1f}% move")
                
                # Technical level comments
                if commodity.name == "Gold" and commodity.alert_level == "significant":
                    outlook.append("Gold: Key psychological levels in focus")
                elif commodity.name == "Copper" and commodity.alert_level == "significant":
                    outlook.append("Copper: Industrial demand indicators crucial")
                elif commodity.name == "Oil" and commodity.alert_level == "significant":
                    outlook.append("Oil: OPEC+ decisions and inventory data key")
        
        except Exception as e:
            print(f"⚠️ Error analyzing commodity outlook: {e}")
        
        # Default outlooks if no specific alerts
        if not outlook:
            outlook = [
                "Gold: Monitor Fed policy signals for direction",
                "Copper: China economic data remains key driver",
                "Energy: Geopolitical developments in focus"
            ]
        
        return outlook[:4]  # Limit to 4 items
    
    def generate_global_factors(self) -> List[str]:
        """Generate global factors to watch for upcoming week"""
        
        factors = [
            "Federal Reserve policy signals and interest rate expectations",
            "China economic data and metals demand indicators", 
            "US Dollar strength impacting commodity prices",
            "Geopolitical developments affecting energy markets"
        ]
        
        # Add seasonal or current factors
        current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:  # Winter
            factors.append("Winter energy demand and weather patterns")
        elif current_month in [3, 4, 5]:  # Spring
            factors.append("Spring construction season demand outlook")
        elif current_month in [6, 7, 8]:  # Summer
            factors.append("Summer driving season and cooling demand")
        elif current_month in [9, 10, 11]:  # Fall
            factors.append("Autumn industrial activity and heating season prep")
        
        return factors[:4]  # Limit to 4 factors
    
    def determine_weeks_theme(self, economic_events: List[Dict], 
                            earnings_calendar: List[Dict]) -> str:
        """Determine the main theme for the upcoming week"""
        
        # Check for high-impact economic events
        high_impact_events = [event for event in economic_events if event.get('impact') == 'high']
        
        if high_impact_events:
            return f"Economic Data Week - {high_impact_events[0]['event']} in focus"
        
        # Check for earnings season
        if earnings_calendar:
            return f"{earnings_calendar[0]['period']} continues"
        
        # Check month positioning
        next_week_start = self.get_upcoming_week_dates()[0]
        
        if next_week_start.day <= 7:  # First week of month
            return "Month-start positioning and new money flows"
        elif next_week_start.day >= 21:  # Last week of month
            return "Month-end rebalancing and option expiry"
        else:
            return "Standard market monitoring and trend continuation"
    
    def generate_key_events(self, economic_events: List[Dict], 
                          earnings_calendar: List[Dict]) -> List[str]:
        """Generate key events list for the week"""
        
        events = []
        
        # Add high-impact economic events
        for event in economic_events:
            if event.get('impact') == 'high':
                events.append(f"{event['event']} ({event['date']})")
        
        # Add earnings if available
        if earnings_calendar:
            events.append(f"Canadian mining earnings continue ({earnings_calendar[0]['period']})")
        
        # Add standard weekly events
        if not events:
            events = [
                "Weekly economic data releases monitored",
                "Global commodity market developments",
                "Federal Reserve policy communications"
            ]
        
        return events[:4]  # Limit to 4 events
    
    def generate_week_ahead(self) -> WeekAheadPreview:
        """Generate complete week-ahead preview"""
        print("🔮 Generating Week Ahead Preview...")
        
        week_start, week_end = self.get_upcoming_week_dates()
        
        # Generate all components
        economic_calendar = self.generate_economic_calendar()
        earnings_calendar = self.generate_earnings_calendar()
        watch_list = self.generate_watch_list()
        commodity_outlook = self.generate_commodity_outlook()
        global_factors = self.generate_global_factors()
        
        # Generate derived content
        weeks_theme = self.determine_weeks_theme(economic_calendar, earnings_calendar)
        key_events = self.generate_key_events(economic_calendar, earnings_calendar)
        
        return WeekAheadPreview(
            week_start=week_start.strftime("%b %d"),
            key_events=key_events,
            watch_list=watch_list,
            global_factors=global_factors,
            commodity_outlook=commodity_outlook,
            weeks_theme=weeks_theme,
            economic_calendar=economic_calendar,
            earnings_calendar=earnings_calendar
        )

def main():
    """Test week ahead generator"""
    print("🔮 Week Ahead Generator Test")
    print("=" * 50)
    
    generator = WeekAheadGenerator()
    week_ahead = generator.generate_week_ahead()
    
    print(f"\n📅 Week Starting: {week_ahead.week_start}")
    print(f"🎯 Week's Theme: {week_ahead.weeks_theme}")
    
    print(f"\n📅 KEY EVENTS:")
    for event in week_ahead.key_events:
        print(f"  • {event}")
    
    print(f"\n⚡ WATCH LIST:")
    for stock in week_ahead.watch_list:
        print(f"  • {stock['symbol']}: {stock['reason']}")
    
    print(f"\n🌍 GLOBAL FACTORS:")
    for factor in week_ahead.global_factors:
        print(f"  • {factor}")
    
    print(f"\n💎 COMMODITY OUTLOOK:")
    for outlook in week_ahead.commodity_outlook:
        print(f"  • {outlook}")
    
    if week_ahead.economic_calendar:
        print(f"\n📊 ECONOMIC CALENDAR:")
        for event in week_ahead.economic_calendar:
            print(f"  • {event['date']}: {event['event']} ({event['impact']} impact)")

if __name__ == "__main__":
    main()