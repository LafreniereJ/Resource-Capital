#!/usr/bin/env python3
"""
LinkedIn Daily Brief Generator
Creates engaging daily mining industry briefs for LinkedIn posting
"""

import sys
import os
sys.path.append('../')

from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import random

from ..core.config import Config

@dataclass
class MarketMover:
    """Stock movement data structure"""
    company: str
    ticker: str
    price: float
    change_pct: float
    volume: int
    reason: str = ""
    market_cap: Optional[int] = None

@dataclass
class CommodityData:
    """Commodity price data structure"""
    name: str
    symbol: str
    price: float
    change_pct: float
    currency: str = "USD"

@dataclass
class NewsItem:
    """News item data structure"""
    headline: str
    summary: str
    priority: str  # critical, high, medium, low
    category: str  # M&A, earnings, operational, etc.
    companies: List[str] = None

@dataclass
class LinkedInBrief:
    """Complete LinkedIn brief data structure"""
    date: str
    header: str
    headlines: List[str]
    market_movers: Dict[str, List[MarketMover]]
    commodities: List[CommodityData]
    insights: List[str]
    footer: str
    template_type: str
    hashtags: List[str]

class LinkedInBriefGenerator:
    """Generates daily LinkedIn briefs for Canadian mining industry"""
    
    def __init__(self):
        self.config = Config()
        self.canadian_companies = self._load_canadian_companies()
        self.templates = self._load_templates()
        
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
            
            # Combine and add exchange info
            tsx_df['Exchange'] = 'TSX'
            tsxv_df['Exchange'] = 'TSXV'
            
            return pd.concat([tsx_df, tsxv_df], ignore_index=True)
            
        except Exception as e:
            print(f"Warning: Could not load company data: {e}")
            return pd.DataFrame()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load LinkedIn post templates"""
        return {
            "market_focus": """🏭 Canadian Mining Brief - {date}

⚡ MARKET MOVERS
{market_movers}

💰 COMMODITIES
{commodities}

🔍 INSIGHT: {insight}

Data: {company_count} companies tracked | {exchanges}
#CanadianMining #TSX #MiningStocks #ResourceSector""",

            "news_focus": """🏭 Canadian Mining Brief - {date}

📰 TOP STORY
{top_story}

📊 BY THE NUMBERS
{market_summary}

📍 PROVINCIAL ACTIVITY
{provincial_activity}

Data: TSX/TSXV | Live market intelligence
#MiningNews #CanadianMining #ResourceSector""",

            "sector_analysis": """🏭 Canadian Mining Brief - {date}

🎯 SECTOR SPOTLIGHT: {sector}
{sector_analysis}

📈 TOP PERFORMERS
{top_performers}

🔍 KEY DRIVER: {key_driver}

#SectorAnalysis #CommodityMarkets #MiningInvestor"""
        }
    
    def get_market_movers(self, min_change_pct: float = 5.0, limit: int = 5) -> Tuple[List[MarketMover], List[MarketMover]]:
        """Get top gaining and declining stocks"""
        gainers = []
        decliners = []
        
        try:
            # Sample companies for performance (full scan would be too slow for daily use)
            sample_companies = self.canadian_companies.sample(min(100, len(self.canadian_companies)))
            
            for _, company in sample_companies.iterrows():
                try:
                    if pd.isna(company.get('Root Ticker')):
                        continue
                        
                    ticker = f"{company['Root Ticker']}.TO"
                    stock = yf.Ticker(ticker)
                    
                    # Get recent price data
                    hist = stock.history(period="2d")
                    if len(hist) < 2:
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2]
                    change_pct = ((current_price - previous_price) / previous_price) * 100
                    
                    if abs(change_pct) < min_change_pct:
                        continue
                    
                    # Get additional data
                    info = stock.info
                    volume = hist['Volume'].iloc[-1] if 'Volume' in hist else 0
                    
                    mover = MarketMover(
                        company=company['Name'],
                        ticker=ticker,
                        price=current_price,
                        change_pct=change_pct,
                        volume=int(volume),
                        market_cap=info.get('marketCap')
                    )
                    
                    if change_pct > 0:
                        gainers.append(mover)
                    else:
                        decliners.append(mover)
                        
                except Exception as e:
                    continue
            
            # Sort and limit results
            gainers.sort(key=lambda x: x.change_pct, reverse=True)
            decliners.sort(key=lambda x: x.change_pct)
            
            return gainers[:limit], decliners[:limit]
            
        except Exception as e:
            print(f"Error getting market movers: {e}")
            return [], []
    
    def get_commodity_data(self) -> List[CommodityData]:
        """Get commodity price data using free sources"""
        commodities = []
        
        # Use ETFs as proxies for commodity prices (free via yfinance)
        commodity_etfs = {
            "Gold": "GLD",
            "Silver": "SLV", 
            "Copper": "CPER",
            "Oil": "USO",
            "Natural Gas": "UNG"
        }
        
        try:
            for name, symbol in commodity_etfs.items():
                try:
                    etf = yf.Ticker(symbol)
                    hist = etf.history(period="2d")
                    
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change_pct = ((current - previous) / previous) * 100
                        
                        commodities.append(CommodityData(
                            name=name,
                            symbol=symbol,
                            price=current,
                            change_pct=change_pct
                        ))
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error getting commodity data: {e}")
        
        return commodities
    
    def generate_insights(self, gainers: List[MarketMover], decliners: List[MarketMover], 
                         commodities: List[CommodityData]) -> List[str]:
        """Generate intelligent insights from market data"""
        insights = []
        
        try:
            # Market sentiment insight
            if len(gainers) > len(decliners):
                insights.append(f"Bullish sentiment in Canadian mining with {len(gainers)} significant gainers vs {len(decliners)} decliners")
            elif len(decliners) > len(gainers):
                insights.append(f"Market pressure on mining sector with {len(decliners)} significant declines")
            else:
                insights.append("Mixed sentiment in Canadian mining sector today")
            
            # Commodity insight
            if commodities:
                gold_data = next((c for c in commodities if c.name == "Gold"), None)
                if gold_data and abs(gold_data.change_pct) > 1:
                    direction = "rally" if gold_data.change_pct > 0 else "decline"
                    insights.append(f"Gold {direction} of {gold_data.change_pct:.1f}% impacting precious metals miners")
            
            # Volume insight
            high_volume_movers = [m for m in gainers + decliners if m.volume > 1000000]
            if high_volume_movers:
                insights.append(f"High volume activity in {len(high_volume_movers)} mining stocks suggests institutional interest")
            
            # Provincial insight based on movers
            tsx_movers = [m for m in gainers + decliners if 'TSX' in m.ticker]
            if tsx_movers:
                insights.append(f"TSX mining sector showing {len(tsx_movers)} significant moves - focus on major producers")
                
        except Exception as e:
            insights.append("Market analysis indicates mixed trading conditions in Canadian mining")
        
        return insights[:2]  # Limit to 2 key insights
    
    def format_market_movers(self, gainers: List[MarketMover], decliners: List[MarketMover]) -> str:
        """Format market movers for LinkedIn post"""
        lines = []
        
        # Top gainers
        for i, gainer in enumerate(gainers[:3]):
            emoji = "🚀" if i == 0 else "📈"
            lines.append(f"{emoji} {gainer.company}: +{gainer.change_pct:.1f}% (${gainer.price:.2f})")
        
        # Top decliners  
        for i, decliner in enumerate(decliners[:2]):
            emoji = "📉"
            lines.append(f"{emoji} {decliner.company}: {decliner.change_pct:.1f}% (${decliner.price:.2f})")
        
        return "\n".join(lines)
    
    def format_commodities(self, commodities: List[CommodityData]) -> str:
        """Format commodity data for LinkedIn post"""
        lines = []
        
        for commodity in commodities[:3]:  # Limit to top 3
            emoji = "⬆️" if commodity.change_pct > 0 else "⬇️"
            lines.append(f"{emoji} {commodity.name}: ${commodity.price:.2f} ({commodity.change_pct:+.1f}%)")
        
        return "\n".join(lines)
    
    def generate_daily_brief(self, template_type: str = "auto") -> LinkedInBrief:
        """Generate complete daily LinkedIn brief"""
        
        # Auto-select template based on market conditions
        if template_type == "auto":
            template_type = random.choice(["market_focus", "news_focus", "sector_analysis"])
        
        # Get market data
        gainers, decliners = self.get_market_movers()
        commodities = self.get_commodity_data()
        insights = self.generate_insights(gainers, decliners, commodities)
        
        # Build brief
        date_str = datetime.now().strftime("%B %d, %Y")
        
        brief = LinkedInBrief(
            date=date_str,
            header=f"🏭 Canadian Mining Brief - {date_str}",
            headlines=[],
            market_movers={"gainers": gainers, "decliners": decliners},
            commodities=commodities,
            insights=insights,
            footer="Data: TSX/TSXV | Live market intelligence",
            template_type=template_type,
            hashtags=["#CanadianMining", "#TSX", "#MiningStocks", "#ResourceSector"]
        )
        
        return brief
    
    def format_linkedin_post(self, brief: LinkedInBrief) -> str:
        """Format brief into LinkedIn post text"""
        
        try:
            if brief.template_type == "market_focus":
                return self.templates["market_focus"].format(
                    date=brief.date,
                    market_movers=self.format_market_movers(
                        brief.market_movers["gainers"], 
                        brief.market_movers["decliners"]
                    ),
                    commodities=self.format_commodities(brief.commodities),
                    insight=brief.insights[0] if brief.insights else "Active trading in Canadian mining sector",
                    company_count=len(self.canadian_companies),
                    exchanges="TSX/TSXV"
                )
            
            elif brief.template_type == "news_focus":
                return self.templates["news_focus"].format(
                    date=brief.date,
                    top_story="Market analysis shows mixed sentiment in mining sector",
                    market_summary=f"• {len(brief.market_movers['gainers'])} gainers, {len(brief.market_movers['decliners'])} decliners\n• Gold: {brief.commodities[0].price:.2f} ({brief.commodities[0].change_pct:+.1f}%)" if brief.commodities else "Market data updating",
                    provincial_activity="BC: 174 companies • ON: 147 companies • QC: 136 companies"
                )
            
            else:  # sector_analysis
                return self.templates["sector_analysis"].format(
                    date=brief.date,
                    sector="GOLD MINING",
                    sector_analysis=f"• Price Action: {brief.commodities[0].name} {brief.commodities[0].change_pct:+.1f}%" if brief.commodities else "• Price Action: Mixed",
                    top_performers=self.format_market_movers(brief.market_movers["gainers"][:2], []),
                    key_driver=brief.insights[0] if brief.insights else "Market dynamics driving sector performance"
                )
                
        except Exception as e:
            # Fallback simple format
            return f"""🏭 Canadian Mining Brief - {brief.date}

📊 Market Update: {len(self.canadian_companies)} companies tracked
{self.format_market_movers(brief.market_movers.get("gainers", [])[:2], brief.market_movers.get("decliners", [])[:2])}

#CanadianMining #TSX #ResourceSector"""

def main():
    """Test the LinkedIn brief generator"""
    generator = LinkedInBriefGenerator()
    
    print("🔄 Generating LinkedIn Daily Brief...")
    brief = generator.generate_daily_brief()
    
    print("\n📱 LinkedIn Post:")
    print("=" * 50)
    post_text = generator.format_linkedin_post(brief)
    print(post_text)
    print("=" * 50)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/processed/linkedin_brief_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(post_text)
    
    print(f"\n💾 Brief saved to: {filename}")
    
    # Save data as JSON for analysis
    json_filename = f"data/processed/linkedin_brief_data_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(asdict(brief), f, indent=2, default=str)
    
    print(f"📊 Data saved to: {json_filename}")

if __name__ == "__main__":
    main()