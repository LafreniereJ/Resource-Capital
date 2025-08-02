#!/usr/bin/env python3
"""
Commodity Price Tracker
Tracks metal and energy commodity prices using 100% free data sources
"""

import sys
import os
sys.path.append('../')

import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import time

from ..core.config import Config

@dataclass
class CommodityPrice:
    """Commodity price data structure"""
    name: str
    symbol: str
    price: float
    change_1d: float
    change_pct_1d: float
    change_1w: Optional[float] = None
    change_pct_1w: Optional[float] = None
    currency: str = "USD"
    source: str = "yfinance"
    last_updated: str = ""
    alert_level: str = "normal"  # normal, significant, major
    
    def __post_init__(self):
        self.last_updated = datetime.now().isoformat()
        self.alert_level = self._calculate_alert_level()
    
    def _calculate_alert_level(self) -> str:
        """Determine alert level based on price movement"""
        abs_change = abs(self.change_pct_1d)
        if abs_change >= 5.0:
            return "major"
        elif abs_change >= 2.0:
            return "significant" 
        else:
            return "normal"

class CommodityPriceTracker:
    """Tracks commodity prices using free data sources"""
    
    def __init__(self):
        self.config = Config()
        
        # Free commodity tracking via ETFs and futures
        self.commodity_etfs = {
            # Precious Metals
            "Gold": {"symbol": "GLD", "multiplier": 0.1, "description": "SPDR Gold Trust"},
            "Silver": {"symbol": "SLV", "multiplier": 0.1, "description": "iShares Silver Trust"},
            "Platinum": {"symbol": "PPLT", "multiplier": 1.0, "description": "Aberdeen Platinum ETF"},
            
            # Base Metals
            "Copper": {"symbol": "CPER", "multiplier": 1.0, "description": "US Copper Index Fund"},
            "Aluminum": {"symbol": "JJU", "multiplier": 1.0, "description": "iPath Aluminum ETN"},
            
            # Energy
            "Oil": {"symbol": "USO", "multiplier": 1.0, "description": "US Oil Fund"},
            "Natural Gas": {"symbol": "UNG", "multiplier": 1.0, "description": "US Natural Gas Fund"},
            
            # Other
            "Uranium": {"symbol": "URA", "multiplier": 1.0, "description": "Global X Uranium ETF"},
            "Coal": {"symbol": "KOL", "multiplier": 1.0, "description": "VanEck Coal ETF"}
        }
        
        # Alternative free sources for spot prices
        self.web_sources = {
            "investing.com": "https://www.investing.com/commodities/",
            "marketwatch": "https://www.marketwatch.com/investing/future/"
        }
        
    def get_etf_commodity_data(self, commodity: str, etf_info: Dict) -> Optional[CommodityPrice]:
        """Get commodity data via ETF proxy"""
        try:
            ticker = yf.Ticker(etf_info["symbol"])
            
            # Get recent price history
            hist = ticker.history(period="7d")
            if len(hist) < 2:
                return None
            
            # Calculate changes
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2] 
            week_ago_price = hist['Close'].iloc[0] if len(hist) >= 5 else previous_price
            
            change_1d = current_price - previous_price
            change_pct_1d = (change_1d / previous_price) * 100
            
            change_1w = current_price - week_ago_price
            change_pct_1w = (change_1w / week_ago_price) * 100
            
            # Apply multiplier if needed (for ETFs that don't directly track spot price)
            adjusted_price = current_price * etf_info.get("multiplier", 1.0)
            
            return CommodityPrice(
                name=commodity,
                symbol=etf_info["symbol"],
                price=adjusted_price,
                change_1d=change_1d * etf_info.get("multiplier", 1.0),
                change_pct_1d=change_pct_1d,
                change_1w=change_1w * etf_info.get("multiplier", 1.0),
                change_pct_1w=change_pct_1w,
                source=f"ETF:{etf_info['symbol']}"
            )
            
        except Exception as e:
            print(f"Error getting ETF data for {commodity}: {e}")
            return None
    
    def scrape_investing_com_price(self, commodity: str) -> Optional[CommodityPrice]:
        """Scrape commodity price from Investing.com (free)"""
        try:
            # Map commodity names to Investing.com URLs
            commodity_urls = {
                "Gold": "gold",
                "Silver": "silver", 
                "Copper": "copper",
                "Oil": "crude-oil",
                "Natural Gas": "natural-gas"
            }
            
            if commodity not in commodity_urls:
                return None
            
            url = f"https://www.investing.com/commodities/{commodity_urls[commodity]}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for price elements (these selectors may need updates)
            price_selectors = [
                '[data-test="instrument-price-last"]',
                '.text-2xl',
                '.instrument-price_last__JQN7O'
            ]
            
            price_element = None
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    break
            
            if not price_element:
                return None
            
            price_text = price_element.text.strip().replace(',', '')
            current_price = float(price_text)
            
            # Try to get change data
            change_selectors = [
                '[data-test="instrument-price-change"]',
                '.instrument-price_change__JQN7O'
            ]
            
            change_element = None
            for selector in change_selectors:
                change_element = soup.select_one(selector)
                if change_element:
                    break
            
            change_1d = 0.0
            change_pct_1d = 0.0
            
            if change_element:
                change_text = change_element.text.strip()
                try:
                    if '(' in change_text and ')' in change_text:
                        # Extract percentage from parentheses
                        pct_text = change_text.split('(')[1].split(')')[0].replace('%', '')
                        change_pct_1d = float(pct_text)
                        
                        # Calculate absolute change
                        change_1d = (change_pct_1d / 100) * current_price
                        
                except Exception:
                    pass
            
            return CommodityPrice(
                name=commodity,
                symbol=commodity_urls[commodity],
                price=current_price,
                change_1d=change_1d,
                change_pct_1d=change_pct_1d,
                source="investing.com"
            )
            
        except Exception as e:
            print(f"Error scraping {commodity} from Investing.com: {e}")
            return None
    
    def get_all_commodity_prices(self, use_web_scraping: bool = False) -> List[CommodityPrice]:
        """Get all commodity prices using available free sources"""
        prices = []
        
        # Primary method: ETF tracking
        for commodity, etf_info in self.commodity_etfs.items():
            price_data = self.get_etf_commodity_data(commodity, etf_info)
            if price_data:
                prices.append(price_data)
            
            # Rate limiting
            time.sleep(0.5)
        
        # Secondary method: Web scraping (optional, more fragile)
        if use_web_scraping:
            for commodity in ["Gold", "Silver", "Copper", "Oil", "Natural Gas"]:
                scraped_data = self.scrape_investing_com_price(commodity)
                if scraped_data:
                    # Check if we already have this commodity from ETF
                    existing = next((p for p in prices if p.name == commodity), None)
                    if not existing:
                        prices.append(scraped_data)
                
                time.sleep(1)  # More conservative rate limiting for scraping
        
        return prices
    
    def get_significant_movers(self, prices: List[CommodityPrice], 
                            min_change_pct: float = 2.0) -> Tuple[List[CommodityPrice], List[CommodityPrice]]:
        """Get commodities with significant price movements"""
        gainers = [p for p in prices if p.change_pct_1d >= min_change_pct]
        decliners = [p for p in prices if p.change_pct_1d <= -min_change_pct]
        
        # Sort by magnitude of change
        gainers.sort(key=lambda x: x.change_pct_1d, reverse=True)
        decliners.sort(key=lambda x: x.change_pct_1d)
        
        return gainers, decliners
    
    def get_alerts(self, prices: List[CommodityPrice]) -> List[CommodityPrice]:
        """Get commodities with alert-worthy movements"""
        return [p for p in prices if p.alert_level in ["significant", "major"]]
    
    def format_commodity_summary(self, prices: List[CommodityPrice]) -> str:
        """Format commodity data for reports"""
        if not prices:
            return "No commodity data available"
        
        lines = []
        
        # Group by category
        precious = [p for p in prices if p.name in ["Gold", "Silver", "Platinum"]]
        base = [p for p in prices if p.name in ["Copper", "Aluminum"]]
        energy = [p for p in prices if p.name in ["Oil", "Natural Gas"]]
        
        if precious:
            lines.append("💰 PRECIOUS METALS:")
            for p in precious:
                emoji = "⬆️" if p.change_pct_1d > 0 else "⬇️" if p.change_pct_1d < 0 else "➡️"
                lines.append(f"  {emoji} {p.name}: ${p.price:.2f} ({p.change_pct_1d:+.1f}%)")
        
        if base:
            lines.append("🔧 BASE METALS:")
            for p in base:
                emoji = "⬆️" if p.change_pct_1d > 0 else "⬇️" if p.change_pct_1d < 0 else "➡️"
                lines.append(f"  {emoji} {p.name}: ${p.price:.2f} ({p.change_pct_1d:+.1f}%)")
        
        if energy:
            lines.append("⚡ ENERGY:")
            for p in energy:
                emoji = "⬆️" if p.change_pct_1d > 0 else "⬇️" if p.change_pct_1d < 0 else "➡️"
                lines.append(f"  {emoji} {p.name}: ${p.price:.2f} ({p.change_pct_1d:+.1f}%)")
        
        return "\n".join(lines)
    
    def save_historical_data(self, prices: List[CommodityPrice], filename: Optional[str] = None):
        """Save commodity price data for historical tracking"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/processed/commodity_prices_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "prices": [asdict(p) for p in prices],
            "summary": {
                "total_commodities": len(prices),
                "major_alerts": len([p for p in prices if p.alert_level == "major"]),
                "significant_alerts": len([p for p in prices if p.alert_level == "significant"])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename

def main():
    """Test the commodity price tracker"""
    print("📊 Commodity Price Tracker - FREE Edition")
    print("=" * 50)
    
    tracker = CommodityPriceTracker()
    
    print("🔄 Fetching commodity prices...")
    prices = tracker.get_all_commodity_prices(use_web_scraping=False)
    
    if not prices:
        print("❌ No commodity data retrieved")
        return
    
    print(f"✅ Retrieved {len(prices)} commodity prices")
    print("\n📈 Current Prices:")
    print(tracker.format_commodity_summary(prices))
    
    # Get significant movers
    gainers, decliners = tracker.get_significant_movers(prices, min_change_pct=1.0)
    
    if gainers:
        print(f"\n🚀 Top Gainers ({len(gainers)}):")
        for gainer in gainers[:3]:
            print(f"  • {gainer.name}: +{gainer.change_pct_1d:.1f}%")
    
    if decliners:
        print(f"\n📉 Top Decliners ({len(decliners)}):")
        for decliner in decliners[:3]:
            print(f"  • {decliner.name}: {decliner.change_pct_1d:.1f}%")
    
    # Get alerts
    alerts = tracker.get_alerts(prices)
    if alerts:
        print(f"\n🚨 Price Alerts ({len(alerts)}):")
        for alert in alerts:
            print(f"  • {alert.name}: {alert.change_pct_1d:+.1f}% ({alert.alert_level})")
    
    # Save data
    filename = tracker.save_historical_data(prices)
    print(f"\n💾 Data saved to: {filename}")

if __name__ == "__main__":
    main()