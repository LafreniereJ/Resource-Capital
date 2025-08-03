#!/usr/bin/env python3
"""
Daily Market Brief Generator
Generates social media ready daily mining sector briefs
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import json

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from daily_data_collector import DailyMarketCollector


class DailyBriefGenerator:
    """Generates daily market briefs for social media"""
    
    def __init__(self, template_path: str = None):
        """Initialize the daily brief generator"""
        self.template_path = template_path or "templates/daily_market_brief_template.md"
        self.data_collector = DailyMarketCollector()
        
    def generate_brief(self, output_path: str = None) -> str:
        """Generate a daily market brief"""
        
        today = datetime.now()
        print(f"📱 Generating daily market brief for {today.strftime('%Y-%m-%d')}")
        
        # Collect fresh market data
        market_data = self.data_collector.collect_daily_data()
        
        # Load template
        template = self._load_template()
        
        # Generate brief content
        brief_content = self._populate_template(template, market_data, today)
        
        # Save brief
        if output_path is None:
            output_path = self._generate_output_path(today)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(brief_content)
        
        print(f"✅ Daily brief generated: {output_path}")
        return output_path
    
    def _load_template(self) -> str:
        """Load the daily brief template"""
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error: Could not load template from {self.template_path}: {e}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """Return a basic template if main template is not available"""
        return """🏭 **Canadian Mining Daily Brief** - {date}

## 📊 **Market Highlights**
{market_summary}

## 📈 **Top Performers**
{top_gainers}

## 📉 **Notable Declines**
{top_decliners}

## 💎 **Commodity Watch**
{commodity_highlights}

{major_news_section}

---
*Live market intelligence from TSX/TSXV mining sector*

{hashtags}"""
    
    def _populate_template(self, template: str, data: Dict[str, Any], date: datetime) -> str:
        """Populate template with market data"""
        
        # Generate all template sections
        replacements = {
            'date': date.strftime("%B %d, %Y"),
            'market_summary': self._generate_market_summary(data),
            'top_gainers': self._generate_top_gainers(data),
            'top_decliners': self._generate_top_decliners(data),
            'volume_leaders': self._generate_volume_leaders(data),
            'commodity_highlights': self._generate_commodity_highlights(data),
            'major_news_section': self._generate_news_section(data),
            'breaking_news_section': self._generate_breaking_news_section(data),
            'hashtags': self._generate_hashtags(data)
        }
        
        # Replace placeholders in template
        for key, value in replacements.items():
            placeholder = "{" + key + "}"
            template = template.replace(placeholder, str(value) if value is not None else "")
        
        return template
    
    def _generate_market_summary(self, data: Dict[str, Any]) -> str:
        """Generate market summary section"""
        
        summary = data.get('market_summary', {})
        stock_stats = data['market_data'].get('market_stats', {})
        
        sentiment = summary.get('market_sentiment', 'mixed')
        gainers_count = stock_stats.get('gainers_count', 0)
        decliners_count = stock_stats.get('decliners_count', 0)
        total_stocks = stock_stats.get('total_stocks', 0)
        
        if sentiment == 'bullish':
            sentiment_emoji = "📈"
            sentiment_text = "positive momentum"
        elif sentiment == 'bearish':
            sentiment_emoji = "📉"
            sentiment_text = "selling pressure"
        else:
            sentiment_emoji = "↔️"
            sentiment_text = "mixed trading"
        
        market_summary = f"""{sentiment_emoji} **{sentiment_text.title()}** across Canadian mining sector
• {gainers_count} gainers, {decliners_count} decliners out of {total_stocks} tracked stocks"""
        
        # Add top mover context
        top_gainer = summary.get('top_gainer')
        if top_gainer:
            market_summary += f"\n• Leading gainer: **{top_gainer['symbol']}** +{top_gainer['change_pct']:.1f}%"
        
        top_decliner = summary.get('top_decliner') 
        if top_decliner:
            market_summary += f"\n• Notable decline: **{top_decliner['symbol']}** {top_decliner['change_pct']:.1f}%"
        
        return market_summary
    
    def _generate_top_gainers(self, data: Dict[str, Any]) -> str:
        """Generate top gainers section"""
        
        gainers = data['market_data'].get('gainers', [])
        
        if not gainers:
            return "• No significant gainers today (>2% threshold)"
        
        gainer_lines = []
        for i, stock in enumerate(gainers[:3], 1):
            gainer_lines.append(
                f"{i}. **{stock['symbol']}** - ${stock['current_price']:.2f} "
                f"(+{stock['change_pct']:.1f}%) {self._get_volume_indicator(stock['volume'])}"
            )
        
        return "\n".join(gainer_lines)
    
    def _generate_top_decliners(self, data: Dict[str, Any]) -> str:
        """Generate top decliners section"""
        
        decliners = data['market_data'].get('decliners', [])
        
        if not decliners:
            return "• No significant declines today (>2% threshold)"
        
        decliner_lines = []
        for i, stock in enumerate(decliners[:3], 1):
            decliner_lines.append(
                f"{i}. **{stock['symbol']}** - ${stock['current_price']:.2f} "
                f"({stock['change_pct']:.1f}%) {self._get_volume_indicator(stock['volume'])}"
            )
        
        return "\n".join(decliner_lines)
    
    def _generate_volume_leaders(self, data: Dict[str, Any]) -> str:
        """Generate volume leaders section"""
        
        volume_leaders = data['market_data'].get('volume_leaders', [])
        
        if not volume_leaders:
            return "• No notable volume activity"
        
        volume_lines = []
        for i, stock in enumerate(volume_leaders[:3], 1):
            volume_str = self._format_volume(stock['volume'])
            volume_lines.append(
                f"{i}. **{stock['symbol']}** - {volume_str} "
                f"({stock['change_pct']:+.1f}%)"
            )
        
        return "\n".join(volume_lines)
    
    def _generate_commodity_highlights(self, data: Dict[str, Any]) -> str:
        """Generate commodity highlights section"""
        
        commodity_data = data.get('commodity_data', {})
        
        highlights = []
        
        # Focus on major mining commodities
        priority_commodities = ['Gold', 'Silver', 'Copper']
        
        for commodity in priority_commodities:
            if commodity in commodity_data:
                info = commodity_data[commodity]
                change_pct = info['change_pct']
                price = info['price']
                
                if abs(change_pct) >= 0.5:  # Show if significant move
                    direction_emoji = "📈" if change_pct > 0 else "📉"
                    highlights.append(f"{direction_emoji} **{commodity}**: ${price:.2f} ({change_pct:+.1f}%)")
        
        # Add other significant commodity moves
        significant_moves = data['market_summary'].get('significant_commodity_moves', [])
        for move in significant_moves:
            if move['name'] not in priority_commodities:
                direction_emoji = "📈" if move['direction'] == 'up' else "📉" 
                highlights.append(f"{direction_emoji} **{move['name']}**: ({move['change_pct']:+.1f}%)")
        
        if not highlights:
            return "• Commodities trading in narrow ranges"
        
        return "\n".join(highlights)
    
    def _generate_news_section(self, data: Dict[str, Any]) -> str:
        """Generate major news section"""
        
        major_news = data['news_data'].get('major_news', [])
        
        if not major_news:
            return ""
        
        # Take top 2 most relevant news items
        news_section = "\n## 📰 **Market News**\n"
        
        for i, news in enumerate(major_news[:2], 1):
            title = news['title']
            # Truncate long titles
            if len(title) > 80:
                title = title[:77] + "..."
            
            news_section += f"• **{title}**\n"
        
        return news_section
    
    def _generate_breaking_news_section(self, data: Dict[str, Any]) -> str:
        """Generate breaking news section if any"""
        
        breaking_news = data['news_data'].get('breaking_news', [])
        
        if not breaking_news:
            return ""
        
        breaking_section = "\n## 🚨 **Breaking News**\n"
        
        for news in breaking_news[:2]:
            title = news['title']
            if len(title) > 80:
                title = title[:77] + "..."
            
            breaking_section += f"🔥 **{title}**\n"
        
        return breaking_section
    
    def _generate_hashtags(self, data: Dict[str, Any]) -> str:
        """Generate relevant hashtags"""
        
        base_hashtags = ["#CanadianMining", "#TSX", "#MiningDaily", "#ResourceSector"]
        
        # Add dynamic hashtags based on market activity
        dynamic_hashtags = []
        
        # Add commodity hashtags for significant moves
        commodity_data = data.get('commodity_data', {})
        for commodity, info in commodity_data.items():
            if abs(info['change_pct']) >= 2.0:
                dynamic_hashtags.append(f"#{commodity}")
        
        # Add market sentiment hashtag
        sentiment = data['market_summary'].get('market_sentiment', 'mixed')
        if sentiment == 'bullish':
            dynamic_hashtags.append("#MarketGains")
        elif sentiment == 'bearish':
            dynamic_hashtags.append("#MarketDecline")
        
        # Combine and limit to reasonable number
        all_hashtags = base_hashtags + dynamic_hashtags
        return " ".join(all_hashtags[:8])  # Limit to 8 hashtags
    
    def _get_volume_indicator(self, volume: int) -> str:
        """Get volume indicator emoji"""
        if volume > 2000000:
            return "🔥"  # High volume
        elif volume > 1000000:
            return "📊"  # Above average
        else:
            return ""    # Normal volume
    
    def _format_volume(self, volume: int) -> str:
        """Format volume for display"""
        if volume >= 1000000:
            return f"{volume/1000000:.1f}M shares"
        elif volume >= 1000:
            return f"{volume/1000:.0f}K shares"
        else:
            return f"{volume:,} shares"
    
    def _generate_output_path(self, date: datetime) -> str:
        """Generate output file path"""
        date_str = date.strftime("%Y%m%d")
        filename = f"daily_brief_{date_str}.md"
        return os.path.join("reports", "social", filename)


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate daily mining sector brief")
    parser.add_argument("--template", help="Path to template file")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    
    args = parser.parse_args()
    
    # Generate brief
    generator = DailyBriefGenerator(args.template)
    output_path = generator.generate_brief(args.output)
    
    print(f"\n📱 Daily brief completed!")
    print(f"📄 Brief saved to: {output_path}")
    
    # Show preview if in test mode
    if args.test:
        with open(output_path, 'r') as f:
            content = f.read()
        
        print(f"\n📋 Brief Preview:")
        print("=" * 60)
        print(content[:500] + "...")
        print("=" * 60)


if __name__ == "__main__":
    main()