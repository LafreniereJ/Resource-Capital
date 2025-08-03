#!/usr/bin/env python3
"""
Daily Market Data Collector
Collects real-time market data for daily mining sector social media briefs
"""

import yfinance as yf
import pandas as pd
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os


class DailyMarketCollector:
    """Collects daily market data for mining sector briefs"""
    
    def __init__(self):
        """Initialize the daily market collector"""
        self.canadian_mining_symbols = [
            # Large Cap Mining
            'AEM.TO', 'GOLD.TO', 'ABX.TO', 'FM.TO', 'LUN.TO', 'HBM.TO',
            'TECK-B.TO', 'CCO.TO', 'SU.TO', 'CNQ.TO', 'TOU.TO',
            
            # Mid Cap Mining  
            'WPM.TO', 'FNV.TO', 'MAG.TO', 'SSL.TO', 'OR.TO', 'EQX.TO',
            'KL.TO', 'PAAS.TO', 'CG.TO', 'AGI.TO',
            
            # TSXV Active
            'NFGC.V', 'NFG.TO', 'GSVR.V', 'DV.TO', 'FURY.TO'
        ]
        
        self.commodity_symbols = {
            'Gold': 'GLD',
            'Silver': 'SLV', 
            'Copper': 'CPER',
            'Oil': 'USO',
            'Natural Gas': 'UNG'
        }
        
        self.news_sources = [
            'https://feeds.bbci.co.uk/news/business/rss.xml',
            'https://feeds.marketwatch.com/marketwatch/topstories/',
            'https://feeds.marketwatch.com/marketwatch/marketpulse/',
            'https://www.mining-technology.com/feed/'
        ]
    
    def collect_daily_data(self) -> Dict[str, Any]:
        """Collect all daily market data"""
        print(f"📊 Collecting daily market data for {datetime.now().strftime('%Y-%m-%d')}")
        
        data = {
            'collection_date': datetime.now().isoformat(),
            'market_data': self._collect_stock_data(),
            'commodity_data': self._collect_commodity_data(),
            'news_data': self._collect_news_data(),
            'market_summary': {}
        }
        
        # Generate market summary
        data['market_summary'] = self._generate_market_summary(data)
        
        return data
    
    def _collect_stock_data(self) -> Dict[str, Any]:
        """Collect Canadian mining stock data"""
        print("📈 Collecting stock market data...")
        
        stock_data = {
            'gainers': [],
            'decliners': [],
            'volume_leaders': [],
            'market_stats': {}
        }
        
        try:
            # Fetch data for all symbols
            tickers = yf.Tickers(' '.join(self.canadian_mining_symbols))
            
            daily_performances = []
            
            for symbol in self.canadian_mining_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    info = ticker.info
                    
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2]
                        change = current_price - prev_price
                        change_pct = (change / prev_price) * 100 if prev_price > 0 else 0
                        volume = hist['Volume'].iloc[-1]
                        
                        stock_info = {
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'current_price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_pct': round(change_pct, 2),
                            'volume': int(volume),
                            'market_cap': info.get('marketCap', 0)
                        }
                        
                        daily_performances.append(stock_info)
                        
                except Exception as e:
                    print(f"Warning: Could not fetch data for {symbol}: {e}")
                    continue
            
            # Sort and categorize
            if daily_performances:
                # Top gainers (minimum 2% gain)
                gainers = [s for s in daily_performances if s['change_pct'] >= 2.0]
                gainers.sort(key=lambda x: x['change_pct'], reverse=True)
                stock_data['gainers'] = gainers[:5]
                
                # Top decliners (minimum 2% loss)
                decliners = [s for s in daily_performances if s['change_pct'] <= -2.0]
                decliners.sort(key=lambda x: x['change_pct'])
                stock_data['decliners'] = decliners[:5]
                
                # Volume leaders
                volume_leaders = sorted(daily_performances, key=lambda x: x['volume'], reverse=True)
                stock_data['volume_leaders'] = volume_leaders[:5]
                
                # Market statistics
                total_gainers = len([s for s in daily_performances if s['change_pct'] > 0])
                total_decliners = len([s for s in daily_performances if s['change_pct'] < 0])
                avg_change = sum(s['change_pct'] for s in daily_performances) / len(daily_performances)
                
                stock_data['market_stats'] = {
                    'total_stocks': len(daily_performances),
                    'gainers_count': total_gainers,
                    'decliners_count': total_decliners,
                    'unchanged_count': len(daily_performances) - total_gainers - total_decliners,
                    'avg_change_pct': round(avg_change, 2)
                }
        
        except Exception as e:
            print(f"Error collecting stock data: {e}")
            
        return stock_data
    
    def _collect_commodity_data(self) -> Dict[str, Any]:
        """Collect commodity price data"""
        print("💎 Collecting commodity data...")
        
        commodity_data = {}
        
        for commodity, symbol in self.commodity_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100 if prev_price > 0 else 0
                    
                    commodity_data[commodity] = {
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'symbol': symbol
                    }
                    
            except Exception as e:
                print(f"Warning: Could not fetch {commodity} data: {e}")
                commodity_data[commodity] = {
                    'price': 0,
                    'change': 0,
                    'change_pct': 0,
                    'symbol': symbol
                }
        
        return commodity_data
    
    def _collect_news_data(self) -> Dict[str, Any]:
        """Collect relevant mining news"""
        print("📰 Collecting news data...")
        
        news_data = {
            'breaking_news': [],
            'major_news': [],
            'total_articles': 0
        }
        
        mining_keywords = [
            'mining', 'copper', 'gold', 'silver', 'uranium', 'lithium',
            'agnico', 'barrick', 'first quantum', 'lundin', 'hudbay',
            'teck', 'canadian mining', 'tsx', 'tsxv'
        ]
        
        for feed_url in self.news_sources:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Limit to recent entries
                    title = entry.get('title', '')
                    description = entry.get('description', '')
                    link = entry.get('link', '')
                    published = entry.get('published', '')
                    
                    # Check if article is mining-related
                    text_content = f"{title} {description}".lower()
                    is_mining_related = any(keyword in text_content for keyword in mining_keywords)
                    
                    if is_mining_related:
                        # Determine if breaking news (published in last 4 hours)
                        try:
                            import time
                            from email.utils import parsedate_to_datetime
                            
                            pub_date = parsedate_to_datetime(published)
                            hours_ago = (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600
                            
                            news_item = {
                                'title': title,
                                'description': description[:200],
                                'link': link,
                                'published': published,
                                'source': feed_url,
                                'hours_ago': round(hours_ago, 1)
                            }
                            
                            if hours_ago <= 4:  # Breaking news threshold
                                news_data['breaking_news'].append(news_item)
                            else:
                                news_data['major_news'].append(news_item)
                                
                            news_data['total_articles'] += 1
                            
                        except Exception:
                            # If we can't parse date, treat as major news
                            news_item = {
                                'title': title,
                                'description': description[:200],
                                'link': link,
                                'published': published,
                                'source': feed_url
                            }
                            news_data['major_news'].append(news_item)
                            news_data['total_articles'] += 1
                            
            except Exception as e:
                print(f"Warning: Could not fetch news from {feed_url}: {e}")
        
        # Sort by relevance/recency
        news_data['breaking_news'] = news_data['breaking_news'][:3]
        news_data['major_news'] = news_data['major_news'][:5]
        
        return news_data
    
    def _generate_market_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market summary from collected data"""
        
        stock_stats = data['market_data'].get('market_stats', {})
        commodity_data = data['commodity_data']
        
        # Market sentiment
        gainers_count = stock_stats.get('gainers_count', 0)
        decliners_count = stock_stats.get('decliners_count', 0)
        total_stocks = stock_stats.get('total_stocks', 1)
        
        if gainers_count > decliners_count:
            market_sentiment = "bullish"
        elif decliners_count > gainers_count:
            market_sentiment = "bearish"
        else:
            market_sentiment = "mixed"
        
        # Key movers
        top_gainer = data['market_data']['gainers'][0] if data['market_data']['gainers'] else None
        top_decliner = data['market_data']['decliners'][0] if data['market_data']['decliners'] else None
        
        # Commodity highlights
        commodity_moves = []
        for commodity, info in commodity_data.items():
            if abs(info['change_pct']) >= 1.0:  # Significant moves only
                commodity_moves.append({
                    'name': commodity,
                    'change_pct': info['change_pct'],
                    'direction': 'up' if info['change_pct'] > 0 else 'down'
                })
        
        commodity_moves.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        
        return {
            'market_sentiment': market_sentiment,
            'gainers_vs_decliners': f"{gainers_count} vs {decliners_count}",
            'top_gainer': top_gainer,
            'top_decliner': top_decliner,
            'significant_commodity_moves': commodity_moves[:3],
            'total_news_articles': data['news_data']['total_articles'],
            'breaking_news_count': len(data['news_data']['breaking_news'])
        }
    
    def save_daily_data(self, data: Dict[str, Any], output_path: str = None):
        """Save collected data to JSON file"""
        if output_path is None:
            date_str = datetime.now().strftime("%Y%m%d")
            output_path = f"data/daily_market_data_{date_str}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"💾 Daily market data saved to {output_path}")
        return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect daily market data for mining sector brief")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--symbols", nargs='+', help="Additional symbols to track")
    
    args = parser.parse_args()
    
    collector = DailyMarketCollector()
    
    if args.symbols:
        collector.canadian_mining_symbols.extend(args.symbols)
    
    # Collect data
    data = collector.collect_daily_data()
    
    # Save data
    output_path = collector.save_daily_data(data, args.output)
    
    # Print summary
    summary = data['market_summary']
    print(f"\n📊 Daily Market Summary:")
    print(f"Market Sentiment: {summary['market_sentiment']}")
    print(f"Gainers vs Decliners: {summary['gainers_vs_decliners']}")
    print(f"News Articles: {summary['total_news_articles']}")
    print(f"Breaking News: {summary['breaking_news_count']}")
    
    if summary['top_gainer']:
        print(f"Top Gainer: {summary['top_gainer']['symbol']} +{summary['top_gainer']['change_pct']:.1f}%")
    
    if summary['top_decliner']:
        print(f"Top Decliner: {summary['top_decliner']['symbol']} {summary['top_decliner']['change_pct']:.1f}%")