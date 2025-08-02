#!/usr/bin/env python3
"""
Weekly Wrap Generator
Analyzes the past trading week to create Saturday recap content
"""

import sys
import os
sys.path.append('../')

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

# Import existing modules for data
from .commodity_price_tracker import CommodityPriceTracker, CommodityPrice
from .daily_market_screener import DailyMarketScreener, MarketSummary, StockAlert
from .news_intelligence_engine import NewsIntelligenceEngine, NewsAnalysis

from ..core.config import Config

@dataclass
class WeeklyWrapSummary:
    """Weekly wrap-up data structure"""
    week_start: str
    week_end: str
    top_gainers: List[Dict]
    top_decliners: List[Dict]
    commodity_performance: List[Dict]
    major_stories: List[str]
    stock_of_week: str
    key_takeaway: str
    market_sentiment: str  # "bullish", "bearish", "mixed"
    total_companies_analyzed: int
    week_summary_stats: Dict

class WeeklyWrapGenerator:
    """Generates Saturday weekly recap content"""
    
    def __init__(self):
        self.config = Config()
        self.commodity_tracker = CommodityPriceTracker()
        self.market_screener = DailyMarketScreener()
        self.news_engine = NewsIntelligenceEngine()
        
        # Load Canadian mining companies for analysis
        self.canadian_companies = self._load_canadian_companies()
    
    def _load_canadian_companies(self) -> List[Dict]:
        """Load Canadian mining companies from Excel file"""
        try:
            import pandas as pd
            
            # Load both sheets
            tsx_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSX Canadian Companies',
                header=8  # Headers are in row 9 (0-indexed)
            )
            
            tsxv_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSXV Canadian Companies',
                header=8
            )
            
            companies = []
            
            # Process TSX companies (use .TO suffix)
            for _, row in tsx_df.iterrows():
                if pd.notna(row.get('Symbol')):
                    companies.append({
                        'symbol': f"{row['Symbol']}.TO",
                        'name': row.get('Name', ''),
                        'exchange': 'TSX',
                        'province': row.get('Province', ''),
                        'sector': row.get('Sub-Industry', '')
                    })
            
            # Process TSXV companies (use .V suffix)
            for _, row in tsxv_df.iterrows():
                if pd.notna(row.get('Symbol')):
                    companies.append({
                        'symbol': f"{row['Symbol']}.V",
                        'name': row.get('Name', ''),
                        'exchange': 'TSXV',
                        'province': row.get('Province', ''),
                        'sector': row.get('Sub-Industry', '')
                    })
            
            print(f"📊 Loaded {len(companies)} Canadian mining companies for weekly analysis")
            return companies
            
        except Exception as e:
            print(f"⚠️ Error loading companies: {e}")
            return []
    
    def get_trading_week_dates(self) -> Tuple[datetime, datetime]:
        """Get the start and end dates of the most recent complete trading week"""
        today = datetime.now()
        
        # If it's Saturday, analyze the week that just ended (Mon-Fri)
        if today.weekday() == 5:  # Saturday
            # Get previous Friday (end of week)
            days_since_friday = (today.weekday() - 4) % 7
            if days_since_friday == 0:
                days_since_friday = 7
            week_end = today - timedelta(days=days_since_friday)
            
            # Get Monday of that week (start of week)
            week_start = week_end - timedelta(days=4)
        else:
            # For testing on other days, get the most recent complete week
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday + 7)
            week_end = week_start + timedelta(days=4)
        
        return week_start, week_end
    
    def analyze_weekly_stock_performance(self, max_stocks: int = 50) -> Tuple[List[Dict], List[Dict]]:
        """Analyze weekly stock performance for top gainers and decliners"""
        week_start, week_end = self.get_trading_week_dates()
        
        print(f"📊 Analyzing weekly performance: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        
        gainers = []
        decliners = []
        
        # Sample companies for analysis (limit for performance)
        companies_to_analyze = self.canadian_companies[:max_stocks] if self.canadian_companies else []
        
        for company in companies_to_analyze:
            try:
                symbol = company['symbol']
                stock = yf.Ticker(symbol)
                
                # Get weekly data
                hist = stock.history(period="1mo")  # Get monthly data to ensure we have the week
                
                if len(hist) < 5:  # Need at least a week of data
                    continue
                
                # Find Monday and Friday prices
                week_start_str = week_start.strftime('%Y-%m-%d')
                week_end_str = week_end.strftime('%Y-%m-%d')
                
                # Get closest trading days to our target dates
                monday_price = None
                friday_price = None
                
                for date_str, row in hist.iterrows():
                    date_only = date_str.strftime('%Y-%m-%d')
                    
                    if date_only >= week_start_str and monday_price is None:
                        monday_price = row['Close']
                    
                    if date_only <= week_end_str:
                        friday_price = row['Close']
                
                if monday_price and friday_price and monday_price > 0:
                    weekly_change = ((friday_price - monday_price) / monday_price) * 100
                    
                    # Clean symbol for display (remove exchange suffix)
                    clean_symbol = symbol.replace('.TO', '').replace('.V', '')
                    
                    stock_data = {
                        'symbol': clean_symbol,
                        'name': company['name'][:25],  # Truncate long names
                        'exchange': company['exchange'],
                        'monday_price': monday_price,
                        'friday_price': friday_price,
                        'weekly_change': weekly_change,
                        'volume': hist['Volume'].mean()
                    }
                    
                    # Categorize significant moves
                    if weekly_change >= 10.0:  # 10%+ gain
                        gainers.append(stock_data)
                    elif weekly_change <= -10.0:  # 10%+ decline
                        decliners.append(stock_data)
                
            except Exception as e:
                continue  # Skip problematic stocks
        
        # Sort by performance
        gainers.sort(key=lambda x: x['weekly_change'], reverse=True)
        decliners.sort(key=lambda x: x['weekly_change'])
        
        print(f"📈 Found {len(gainers)} significant gainers (+10% or more)")
        print(f"📉 Found {len(decliners)} significant decliners (-10% or more)")
        
        return gainers[:10], decliners[:10]  # Top 10 each
    
    def analyze_weekly_commodities(self) -> List[Dict]:
        """Analyze weekly commodity performance"""
        print("💰 Analyzing weekly commodity performance...")
        
        commodity_performance = []
        
        try:
            # Get current commodity data
            current_commodities = self.commodity_tracker.get_all_commodity_prices()
            
            for commodity in current_commodities:
                # Use the weekly change if available, otherwise estimate from daily
                if commodity.change_pct_1w is not None:
                    weekly_change = commodity.change_pct_1w
                else:
                    # Rough estimate: multiply daily by 5 (not perfect but gives direction)
                    weekly_change = commodity.change_pct_1d * 3  # Conservative estimate
                
                commodity_performance.append({
                    'name': commodity.name,
                    'symbol': commodity.symbol,
                    'current_price': commodity.price,
                    'weekly_change': weekly_change,
                    'alert_level': commodity.alert_level
                })
            
            # Sort by absolute weekly change (most volatile first)
            commodity_performance.sort(key=lambda x: abs(x['weekly_change']), reverse=True)
            
        except Exception as e:
            print(f"⚠️ Error analyzing commodities: {e}")
        
        return commodity_performance
    
    def analyze_weekly_news(self) -> List[str]:
        """Analyze major news stories from the past week"""
        print("📰 Analyzing week's major stories...")
        
        try:
            # Fetch news from the past week
            news_items = self.news_engine.fetch_all_news(max_age_hours=168)  # 7 days
            
            if not news_items:
                return ["Standard industry developments this week"]
            
            # Get high-priority and M&A news
            analysis = self.news_engine.prioritize_news(news_items)
            
            major_stories = []
            
            # Add critical news
            for item in analysis.critical_news[:2]:
                major_stories.append(item.headline[:80] + "..." if len(item.headline) > 80 else item.headline)
            
            # Add M&A activity
            for item in analysis.ma_activity[:2]:
                major_stories.append(f"M&A: {item.headline[:60]}..." if len(item.headline) > 60 else f"M&A: {item.headline}")
            
            # Add top operational news
            for item in analysis.operational_news[:1]:
                major_stories.append(item.headline[:80] + "..." if len(item.headline) > 80 else item.headline)
            
            return major_stories[:3] if major_stories else ["Standard industry developments this week"]
            
        except Exception as e:
            print(f"⚠️ Error analyzing news: {e}")
            return ["Industry monitoring continues"]
    
    def determine_stock_of_week(self, gainers: List[Dict], decliners: List[Dict]) -> str:
        """Determine the stock of the week based on performance and story"""
        
        if not gainers and not decliners:
            return "No standout performers this week"
        
        # Prefer gainers with significant moves
        if gainers:
            top_gainer = gainers[0]
            return f"{top_gainer['symbol']} (+{top_gainer['weekly_change']:.1f}%) - Top weekly performer"
        
        # If no significant gainers, mention top decliner as cautionary tale
        if decliners:
            top_decliner = decliners[0]
            return f"{top_decliner['symbol']} ({top_decliner['weekly_change']:.1f}%) - Notable weekly decline"
        
        return "Mixed performance across sector"
    
    def generate_key_takeaway(self, gainers: List[Dict], decliners: List[Dict], 
                            commodities: List[Dict]) -> str:
        """Generate intelligent key takeaway for the week"""
        
        takeaways = []
        
        # Market sentiment analysis
        if len(gainers) > len(decliners):
            takeaways.append("Positive sentiment drove Canadian mining higher")
        elif len(decliners) > len(gainers):
            takeaways.append("Market pressure weighed on mining sector")
        else:
            takeaways.append("Mixed sentiment in Canadian mining sector")
        
        # Commodity-driven insights
        if commodities:
            # Find biggest commodity move
            top_commodity = max(commodities, key=lambda x: abs(x['weekly_change']))
            if abs(top_commodity['weekly_change']) >= 5.0:
                direction = "strength" if top_commodity['weekly_change'] > 0 else "weakness"
                takeaways.append(f"{top_commodity['name']} {direction} influenced sector performance")
        
        # Volume/activity insights
        if gainers and len(gainers) >= 3:
            takeaways.append("Broad-based strength across multiple mining names")
        
        # Default if no strong patterns
        if not takeaways:
            takeaways.append("Active monitoring of sector developments continues")
        
        return takeaways[0]
    
    def determine_market_sentiment(self, gainers: List[Dict], decliners: List[Dict]) -> str:
        """Determine overall market sentiment for the week"""
        
        if len(gainers) > len(decliners) * 2:
            return "bullish"
        elif len(decliners) > len(gainers) * 2:
            return "bearish"
        else:
            return "mixed"
    
    def generate_weekly_wrap(self) -> WeeklyWrapSummary:
        """Generate complete weekly wrap-up summary"""
        print("📊 Generating Weekly Wrap-Up Summary...")
        
        week_start, week_end = self.get_trading_week_dates()
        
        # Analyze stock performance
        gainers, decliners = self.analyze_weekly_stock_performance(max_stocks=100)
        
        # Analyze commodity performance
        commodity_performance = self.analyze_weekly_commodities()
        
        # Analyze news stories
        major_stories = self.analyze_weekly_news()
        
        # Generate insights
        stock_of_week = self.determine_stock_of_week(gainers, decliners)
        key_takeaway = self.generate_key_takeaway(gainers, decliners, commodity_performance)
        market_sentiment = self.determine_market_sentiment(gainers, decliners)
        
        # Summary statistics
        week_stats = {
            'total_gainers': len(gainers),
            'total_decliners': len(decliners),
            'avg_gainer_change': sum(g['weekly_change'] for g in gainers) / len(gainers) if gainers else 0,
            'avg_decliner_change': sum(d['weekly_change'] for d in decliners) / len(decliners) if decliners else 0,
            'commodity_movements': len([c for c in commodity_performance if abs(c['weekly_change']) >= 3.0])
        }
        
        return WeeklyWrapSummary(
            week_start=week_start.strftime("%b %d"),
            week_end=week_end.strftime("%b %d"),
            top_gainers=gainers[:5],
            top_decliners=decliners[:5],
            commodity_performance=commodity_performance[:7],
            major_stories=major_stories,
            stock_of_week=stock_of_week,
            key_takeaway=key_takeaway,
            market_sentiment=market_sentiment,
            total_companies_analyzed=len(self.canadian_companies),
            week_summary_stats=week_stats
        )

def main():
    """Test weekly wrap generator"""
    print("📊 Weekly Wrap Generator Test")
    print("=" * 50)
    
    generator = WeeklyWrapGenerator()
    weekly_summary = generator.generate_weekly_wrap()
    
    print(f"\n📅 Week: {weekly_summary.week_start} - {weekly_summary.week_end}")
    print(f"📈 Top Gainers: {len(weekly_summary.top_gainers)}")
    print(f"📉 Top Decliners: {len(weekly_summary.top_decliners)}")
    print(f"💰 Commodities Tracked: {len(weekly_summary.commodity_performance)}")
    print(f"📰 Major Stories: {len(weekly_summary.major_stories)}")
    print(f"🏆 Stock of Week: {weekly_summary.stock_of_week}")
    print(f"💡 Key Takeaway: {weekly_summary.key_takeaway}")
    print(f"😊 Market Sentiment: {weekly_summary.market_sentiment}")
    
    if weekly_summary.top_gainers:
        print(f"\n📈 TOP GAINERS:")
        for gainer in weekly_summary.top_gainers[:3]:
            print(f"  • {gainer['symbol']}: +{gainer['weekly_change']:.1f}%")
    
    if weekly_summary.top_decliners:
        print(f"\n📉 TOP DECLINERS:")
        for decliner in weekly_summary.top_decliners[:3]:
            print(f"  • {decliner['symbol']}: {decliner['weekly_change']:.1f}%")

if __name__ == "__main__":
    main()