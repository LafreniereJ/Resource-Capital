#!/usr/bin/env python3
"""
Daily Market Screener
Scans Canadian mining stocks for significant price movements, volume spikes, and trading patterns
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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

from ..core.config import Config

@dataclass
class StockAlert:
    """Stock movement alert data structure"""
    company: str
    ticker: str
    exchange: str
    price: float
    change_1d: float
    change_pct_1d: float
    volume: int
    avg_volume: Optional[int] = None
    volume_ratio: Optional[float] = None
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    province: Optional[str] = None
    alert_type: str = "price_move"  # price_move, volume_spike, gap_up, gap_down
    alert_level: str = "normal"     # normal, significant, major, critical
    news_related: bool = False
    last_updated: str = ""
    
    def __post_init__(self):
        self.last_updated = datetime.now().isoformat()
        self.alert_level = self._calculate_alert_level()
        if self.avg_volume and self.volume:
            self.volume_ratio = self.volume / self.avg_volume
    
    def _calculate_alert_level(self) -> str:
        """Determine alert level based on price movement"""
        abs_change = abs(self.change_pct_1d)
        if abs_change >= 20.0:
            return "critical"
        elif abs_change >= 10.0:
            return "major"
        elif abs_change >= 5.0:
            return "significant"
        else:
            return "normal"

@dataclass 
class MarketSummary:
    """Daily market summary data"""
    date: str
    total_companies_scanned: int
    gainers: int
    decliners: int
    unchanged: int
    high_volume_stocks: int
    major_moves: int
    tsx_performance: float
    tsxv_performance: float
    top_gainers: List[StockAlert]
    top_decliners: List[StockAlert]
    volume_leaders: List[StockAlert]
    sector_performance: Dict[str, float]

class DailyMarketScreener:
    """Screens Canadian mining stocks for daily trading insights"""
    
    def __init__(self):
        self.config = Config()
        self.canadian_companies = self._load_canadian_companies()
        
        # Screening thresholds
        self.thresholds = {
            "significant_move": 5.0,    # % change
            "major_move": 10.0,         # % change  
            "critical_move": 20.0,      # % change
            "volume_spike": 3.0,        # ratio to average
            "min_volume": 10000,        # minimum daily volume
            "min_market_cap": 1000000   # minimum market cap
        }
    
    def _load_canadian_companies(self) -> pd.DataFrame:
        """Load Canadian mining companies data"""
        try:
            tsx_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSX Canadian Companies'
            )
            tsxv_df = pd.read_excel(
                'data/processed/canadian_mining_companies_filtered.xlsx',
                sheet_name='TSXV Canadian Companies'  
            )
            
            # Add exchange information
            tsx_df['Exchange'] = 'TSX'
            tsxv_df['Exchange'] = 'TSXV'
            
            # Combine dataframes
            combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
            
            # Clean ticker symbols with correct exchange suffixes
            def format_ticker(row):
                if pd.notna(row['Root Ticker']):
                    ticker = str(row['Root Ticker']).strip()
                    if row['Exchange'] == 'TSX':
                        return f"{ticker}.TO"
                    elif row['Exchange'] == 'TSXV':
                        return f"{ticker}.V"
                return None
            
            combined_df['Clean_Ticker'] = combined_df.apply(format_ticker, axis=1)
            
            return combined_df
            
        except Exception as e:
            print(f"Error loading company data: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, ticker: str, company_info: Dict) -> Optional[StockAlert]:
        """Get detailed stock data for a single company"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get recent price history (5 days for volume average)
            hist = stock.history(period="5d")
            if len(hist) < 2:
                return None
            
            # Current vs previous price
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2]
            change_1d = current_price - previous_price
            change_pct_1d = (change_1d / previous_price) * 100
            
            # Volume analysis
            current_volume = int(hist['Volume'].iloc[-1])
            avg_volume = int(hist['Volume'].mean()) if len(hist) > 1 else current_volume
            
            # Skip if volume too low or change too small
            if current_volume < self.thresholds["min_volume"]:
                return None
            
            if abs(change_pct_1d) < 2.0:  # Only track moves > 2%
                return None
            
            # Get additional company info
            info = stock.info
            market_cap = info.get('marketCap')
            sector = info.get('sector', 'Mining')
            
            # Skip penny stocks and micro caps
            if market_cap and market_cap < self.thresholds["min_market_cap"]:
                return None
            
            # Determine alert type
            alert_type = "price_move"
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            if volume_ratio >= self.thresholds["volume_spike"]:
                alert_type = "volume_spike"
            
            return StockAlert(
                company=company_info.get('Name', 'Unknown'),
                ticker=ticker,
                exchange=company_info.get('Exchange', 'Unknown'),
                price=current_price,
                change_1d=change_1d,
                change_pct_1d=change_pct_1d,
                volume=current_volume,
                avg_volume=avg_volume,
                volume_ratio=volume_ratio,
                market_cap=market_cap,
                sector=sector,
                province=company_info.get('CANADA', 'Unknown'),
                alert_type=alert_type
            )
            
        except Exception as e:
            # Silently skip problematic tickers
            return None
    
    def screen_all_stocks(self, max_stocks: int = 200, use_threading: bool = True) -> List[StockAlert]:
        """Screen all Canadian mining stocks for alerts"""
        alerts = []
        
        if self.canadian_companies.empty:
            print("No company data available")
            return alerts
        
        # Sample companies to avoid overwhelming free APIs
        companies_to_scan = self.canadian_companies.dropna(subset=['Clean_Ticker'])
        if len(companies_to_scan) > max_stocks:
            companies_to_scan = companies_to_scan.sample(n=max_stocks)
        
        print(f"🔍 Scanning {len(companies_to_scan)} companies...")
        
        if use_threading:
            # Use threading for faster scanning
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                
                for _, company in companies_to_scan.iterrows():
                    if pd.isna(company['Clean_Ticker']):
                        continue
                    
                    future = executor.submit(
                        self.get_stock_data,
                        company['Clean_Ticker'],
                        company.to_dict()
                    )
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            alerts.append(result)
                    except Exception as e:
                        continue
        else:
            # Sequential scanning (slower but more reliable)
            for _, company in companies_to_scan.iterrows():
                if pd.isna(company['Clean_Ticker']):
                    continue
                
                result = self.get_stock_data(company['Clean_Ticker'], company.to_dict())
                if result:
                    alerts.append(result)
                
                # Rate limiting for free APIs
                time.sleep(0.1)
        
        print(f"✅ Found {len(alerts)} alerts")
        return alerts
    
    def filter_alerts(self, alerts: List[StockAlert], 
                     min_change_pct: float = 5.0,
                     alert_levels: List[str] = None) -> List[StockAlert]:
        """Filter alerts by criteria"""
        filtered = alerts
        
        # Filter by minimum change
        filtered = [a for a in filtered if abs(a.change_pct_1d) >= min_change_pct]
        
        # Filter by alert level
        if alert_levels:
            filtered = [a for a in filtered if a.alert_level in alert_levels]
        
        return filtered
    
    def get_top_movers(self, alerts: List[StockAlert], limit: int = 5) -> Tuple[List[StockAlert], List[StockAlert]]:
        """Get top gaining and declining stocks"""
        gainers = [a for a in alerts if a.change_pct_1d > 0]
        decliners = [a for a in alerts if a.change_pct_1d < 0]
        
        # Sort by magnitude of change
        gainers.sort(key=lambda x: x.change_pct_1d, reverse=True)
        decliners.sort(key=lambda x: x.change_pct_1d)
        
        return gainers[:limit], decliners[:limit]
    
    def get_volume_leaders(self, alerts: List[StockAlert], limit: int = 5) -> List[StockAlert]:
        """Get stocks with highest volume ratios"""
        volume_leaders = [a for a in alerts if a.volume_ratio and a.volume_ratio >= 2.0]
        volume_leaders.sort(key=lambda x: x.volume_ratio or 0, reverse=True)
        return volume_leaders[:limit]
    
    def analyze_sector_performance(self, alerts: List[StockAlert]) -> Dict[str, float]:
        """Analyze performance by mining sector"""
        sector_data = {}
        
        for alert in alerts:
            sector = alert.sector or "Mining"
            if sector not in sector_data:
                sector_data[sector] = []
            sector_data[sector].append(alert.change_pct_1d)
        
        # Calculate average performance per sector
        sector_performance = {}
        for sector, changes in sector_data.items():
            if changes:
                sector_performance[sector] = sum(changes) / len(changes)
        
        return sector_performance
    
    def generate_market_summary(self, alerts: List[StockAlert]) -> MarketSummary:
        """Generate comprehensive market summary"""
        gainers, decliners = self.get_top_movers(alerts)
        volume_leaders = self.get_volume_leaders(alerts)
        sector_performance = self.analyze_sector_performance(alerts)
        
        # Calculate aggregate stats
        total_scanned = len(alerts)
        gainers_count = len([a for a in alerts if a.change_pct_1d > 0])
        decliners_count = len([a for a in alerts if a.change_pct_1d < 0])
        unchanged_count = total_scanned - gainers_count - decliners_count
        
        high_volume_count = len([a for a in alerts if a.volume_ratio and a.volume_ratio >= 2.0])
        major_moves_count = len([a for a in alerts if a.alert_level in ["major", "critical"]])
        
        # Calculate exchange performance
        tsx_alerts = [a for a in alerts if a.exchange == "TSX"]
        tsxv_alerts = [a for a in alerts if a.exchange == "TSXV"]
        
        tsx_performance = sum(a.change_pct_1d for a in tsx_alerts) / len(tsx_alerts) if tsx_alerts else 0.0
        tsxv_performance = sum(a.change_pct_1d for a in tsxv_alerts) / len(tsxv_alerts) if tsxv_alerts else 0.0
        
        return MarketSummary(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_companies_scanned=total_scanned,
            gainers=gainers_count,
            decliners=decliners_count,
            unchanged=unchanged_count,
            high_volume_stocks=high_volume_count,
            major_moves=major_moves_count,
            tsx_performance=tsx_performance,
            tsxv_performance=tsxv_performance,
            top_gainers=gainers,
            top_decliners=decliners,
            volume_leaders=volume_leaders,
            sector_performance=sector_performance
        )
    
    def format_alerts_for_linkedin(self, summary: MarketSummary) -> str:
        """Format market alerts for LinkedIn posting"""
        lines = []
        
        # Market overview
        lines.append(f"📊 Market Scan: {summary.total_companies_scanned} companies")
        lines.append(f"📈 {summary.gainers} gainers | 📉 {summary.decliners} decliners")
        
        if summary.major_moves > 0:
            lines.append(f"🚨 {summary.major_moves} major moves (>10%)")
        
        # Top gainers
        if summary.top_gainers:
            lines.append("\n🚀 TOP GAINERS:")
            for gainer in summary.top_gainers[:3]:
                lines.append(f"• {gainer.company}: +{gainer.change_pct_1d:.1f}% (${gainer.price:.2f})")
        
        # Top decliners
        if summary.top_decliners:
            lines.append("\n📉 TOP DECLINERS:")
            for decliner in summary.top_decliners[:2]:
                lines.append(f"• {decliner.company}: {decliner.change_pct_1d:.1f}% (${decliner.price:.2f})")
        
        # Volume leaders
        if summary.volume_leaders:
            lines.append("\n📊 VOLUME SPIKES:")
            for leader in summary.volume_leaders[:2]:
                ratio = leader.volume_ratio or 0
                lines.append(f"• {leader.company}: {ratio:.1f}x avg volume")
        
        return "\n".join(lines)
    
    def save_screening_results(self, summary: MarketSummary, alerts: List[StockAlert]) -> str:
        """Save screening results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary_file = f"data/processed/market_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(asdict(summary), f, indent=2, default=str)
        
        # Save all alerts
        alerts_file = f"data/processed/market_alerts_{timestamp}.json"
        with open(alerts_file, 'w') as f:
            json.dump([asdict(alert) for alert in alerts], f, indent=2, default=str)
        
        return summary_file

def main():
    """Test the daily market screener"""
    print("🔍 Daily Market Screener - Canadian Mining Stocks")
    print("=" * 60)
    
    screener = DailyMarketScreener()
    
    print("🚀 Starting stock screening...")
    alerts = screener.screen_all_stocks(max_stocks=50)  # Smaller sample for testing
    
    if not alerts:
        print("❌ No alerts found")
        return
    
    # Filter for significant moves
    significant_alerts = screener.filter_alerts(alerts, min_change_pct=3.0)
    
    print(f"📈 Found {len(significant_alerts)} significant moves")
    
    # Generate summary
    summary = screener.generate_market_summary(significant_alerts)
    
    print("\n📊 MARKET SUMMARY:")
    print(f"• Companies Scanned: {summary.total_companies_scanned}")
    print(f"• Gainers: {summary.gainers} | Decliners: {summary.decliners}")
    print(f"• Major Moves: {summary.major_moves}")
    print(f"• TSX Performance: {summary.tsx_performance:+.1f}%")
    print(f"• TSXV Performance: {summary.tsxv_performance:+.1f}%")
    
    # Show top movers
    if summary.top_gainers:
        print("\n🚀 TOP GAINERS:")
        for gainer in summary.top_gainers[:3]:
            print(f"  • {gainer.company}: +{gainer.change_pct_1d:.1f}%")
    
    if summary.top_decliners:
        print("\n📉 TOP DECLINERS:")
        for decliner in summary.top_decliners[:3]:
            print(f"  • {decliner.company}: {decliner.change_pct_1d:.1f}%")
    
    # LinkedIn format
    print("\n📱 LINKEDIN FORMAT:")
    print("=" * 40)
    linkedin_text = screener.format_alerts_for_linkedin(summary)
    print(linkedin_text)
    print("=" * 40)
    
    # Save results
    summary_file = screener.save_screening_results(summary, significant_alerts)
    print(f"\n💾 Results saved to: {summary_file}")

if __name__ == "__main__":
    main()