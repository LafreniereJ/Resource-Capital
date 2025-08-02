#!/usr/bin/env python3
"""
Quick Daily TSX Mining Report
Focused on top companies and high-impact news for rapid daily updates
"""

import asyncio
import json
import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
import requests
import feedparser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickDailyReport:
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.db_path = "mining_companies.db"
        
    async def get_top_companies(self) -> list:
        """Get top 10 TSX mining companies by market cap"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, market_cap
            FROM companies 
            WHERE market_cap IS NOT NULL AND market_cap > 0
            ORDER BY market_cap DESC
            LIMIT 10
        ''')
        
        companies = cursor.fetchall()
        conn.close()
        
        return [{"symbol": row[0], "name": row[1], "market_cap": row[2]} for row in companies]

    def get_stock_movements(self, companies: list) -> dict:
        """Get today's stock movements quickly"""
        
        logger.info("Fetching stock movements for top companies...")
        
        symbols = [company["symbol"] for company in companies]
        movements = {}
        
        try:
            # Get 2-day data for change calculation
            data = yf.download(symbols, period="2d", progress=False, group_by='ticker')
            
            for company in companies:
                symbol = company["symbol"]
                try:
                    if symbol in data.columns.levels[0]:
                        ticker_data = data[symbol]
                        
                        if len(ticker_data) >= 2:
                            today_close = ticker_data['Close'].iloc[-1]
                            yesterday_close = ticker_data['Close'].iloc[-2]
                            
                            price_change = today_close - yesterday_close
                            percent_change = (price_change / yesterday_close) * 100
                            volume = ticker_data['Volume'].iloc[-1]
                            
                            movements[symbol] = {
                                'name': company['name'],
                                'price': float(today_close),
                                'change': float(price_change),
                                'percent_change': float(percent_change),
                                'volume': int(volume) if not pd.isna(volume) else 0,
                                'market_cap': company['market_cap']
                            }
                            
                except Exception as e:
                    logger.warning(f"Error processing {symbol}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching stock data: {str(e)}")
        
        return movements

    def get_mining_industry_news(self) -> list:
        """Get today's mining industry news from key sources"""
        
        logger.info("Fetching mining industry news...")
        
        news_items = []
        
        # Key RSS feeds
        feeds = [
            ('Mining.com', 'https://www.mining.com/feed/'),
            ('Kitco News', 'https://www.kitco.com/rss/KitcoNews.xml'),
        ]
        
        today = datetime.now().date()
        
        for source, feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:  # Top 5 from each source
                    try:
                        # Check if published today or yesterday
                        pub_date = datetime(*entry.published_parsed[:6]).date()
                        
                        if pub_date >= today - timedelta(days=1):
                            # Check for TSX/Canadian mining mentions
                            content = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                            
                            tsx_mentions = self.find_canadian_mining_mentions(content)
                            
                            if tsx_mentions or 'canada' in content:
                                news_items.append({
                                    'title': entry.get('title', ''),
                                    'summary': entry.get('summary', '')[:200] + '...',
                                    'source': source,
                                    'published': entry.get('published', ''),
                                    'link': entry.get('link', ''),
                                    'tsx_mentions': tsx_mentions,
                                    'relevance': len(tsx_mentions) * 10 + (20 if 'canada' in content else 0)
                                })
                    
                    except Exception:
                        continue
            
            except Exception as e:
                logger.warning(f"Error fetching {source}: {str(e)}")
        
        return sorted(news_items, key=lambda x: x['relevance'], reverse=True)

    def find_canadian_mining_mentions(self, content: str) -> list:
        """Find Canadian mining company mentions"""
        
        companies = {
            'barrick': 'ABX.TO', 'agnico eagle': 'AEM.TO', 'kinross': 'K.TO',
            'franco-nevada': 'FNV.TO', 'first quantum': 'FM.TO', 'lundin': 'LUN.TO',
            'hudbay': 'HBM.TO', 'eldorado': 'ELD.TO', 'iamgold': 'IMG.TO',
            'suncor': 'SU.TO', 'canadian natural': 'CNQ.TO', 'imperial oil': 'IMO.TO'
        }
        
        mentions = []
        for company_name, symbol in companies.items():
            if company_name in content or symbol.lower() in content:
                mentions.append(symbol)
        
        return list(set(mentions))

    def get_commodity_context(self) -> dict:
        """Get commodity prices and currency context"""
        
        logger.info("Fetching commodity context...")
        
        context = {}
        
        try:
            # Bank of Canada USD/CAD
            usd_cad_url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1"
            response = requests.get(usd_cad_url, timeout=5)
            data = response.json()
            
            if data.get('observations'):
                context['usd_cad'] = {
                    'rate': data['observations'][0]['FXUSDCAD']['v'],
                    'date': data['observations'][0]['d']
                }
        
        except Exception as e:
            logger.warning(f"Error fetching USD/CAD: {str(e)}")
        
        try:
            # Get gold price from Yahoo Finance
            gold = yf.Ticker("GC=F")
            gold_data = gold.history(period="1d")
            
            if not gold_data.empty:
                context['gold_usd'] = {
                    'price': float(gold_data['Close'].iloc[-1]),
                    'change': float(gold_data['Close'].iloc[-1] - gold_data['Open'].iloc[-1]) if len(gold_data) > 0 else 0
                }
        
        except Exception as e:
            logger.warning(f"Error fetching gold price: {str(e)}")
        
        return context

    def generate_quick_report(self) -> str:
        """Generate quick daily report"""
        
        logger.info("Generating quick daily report...")
        
        try:
            # Get data
            companies = asyncio.run(self.get_top_companies())
            stock_movements = self.get_stock_movements(companies)
            industry_news = self.get_mining_industry_news()
            commodity_context = self.get_commodity_context()
            
            # Generate report
            report = []
            report.append("📈 QUICK TSX MINING DAILY UPDATE")
            report.append("=" * 50)
            report.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
            report.append(f"⏰ {datetime.now().strftime('%H:%M UTC')}")
            report.append("")
            
            # Top market movers
            if stock_movements:
                # Sort by absolute percent change
                sorted_movers = sorted(
                    stock_movements.items(), 
                    key=lambda x: abs(x[1]['percent_change']), 
                    reverse=True
                )
                
                significant_movers = [(k, v) for k, v in sorted_movers if abs(v['percent_change']) >= 3]
                
                if significant_movers:
                    report.append("📊 SIGNIFICANT MOVERS (>3%)")
                    report.append("-" * 25)
                    
                    for symbol, data in significant_movers[:5]:
                        direction = "📈" if data['percent_change'] > 0 else "📉"
                        report.append(f"{direction} {symbol} - {data['name']}")
                        report.append(f"   ${data['price']:.2f} ({data['percent_change']:+.1f}%)")
                        report.append(f"   Volume: {data['volume']:,}")
                        report.append("")
                
                else:
                    report.append("📊 MARKET STATUS")
                    report.append("-" * 15)
                    report.append("• No significant moves (>3%) in top TSX mining stocks today")
                    report.append("• Market showing relative stability")
                    report.append("")
            
            # Industry news
            if industry_news:
                report.append("📰 KEY INDUSTRY NEWS")
                report.append("-" * 20)
                
                for news in industry_news[:3]:
                    report.append(f"• {news['title']}")
                    report.append(f"  🔗 {news['source']}")
                    if news['tsx_mentions']:
                        report.append(f"  📊 Mentions: {', '.join(news['tsx_mentions'])}")
                    report.append(f"  📅 {news['published']}")
                    report.append("")
            
            # Commodity context
            if commodity_context:
                report.append("🥇 COMMODITY CONTEXT")
                report.append("-" * 18)
                
                if 'usd_cad' in commodity_context:
                    usd_cad = commodity_context['usd_cad']
                    report.append(f"• USD/CAD: {usd_cad['rate']}")
                
                if 'gold_usd' in commodity_context:
                    gold = commodity_context['gold_usd']
                    direction = "📈" if gold['change'] > 0 else "📉" if gold['change'] < 0 else "➡️"
                    report.append(f"• Gold: ${gold['price']:.2f} {direction}")
                
                report.append("")
            
            # Market summary
            report.append("📋 QUICK SUMMARY")
            report.append("-" * 15)
            
            if stock_movements:
                positive_moves = len([m for m in stock_movements.values() if m['percent_change'] > 0])
                negative_moves = len([m for m in stock_movements.values() if m['percent_change'] < 0])
                report.append(f"• Market sentiment: {positive_moves} up, {negative_moves} down")
            
            if industry_news:
                canadian_mentions = sum(len(news['tsx_mentions']) for news in industry_news)
                report.append(f"• Industry focus: {len(industry_news)} news items, {canadian_mentions} TSX mentions")
            
            report.append("")
            report.append("⚡ Quick report - Full analysis available on request")
            report.append("📊 Data: Yahoo Finance, Mining.com, Kitco, Bank of Canada")
            
            return "\n".join(report)
        
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating quick report: {str(e)}"

    def save_report(self, report_text: str) -> str:
        """Save report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_tsx_mining_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return filename

def main():
    """Generate quick daily report"""
    
    # Fix pandas import issue
    import pandas as pd
    globals()['pd'] = pd
    
    reporter = QuickDailyReport()
    
    try:
        # Generate report
        report_text = reporter.generate_quick_report()
        
        # Save report
        filename = reporter.save_report(report_text)
        
        # Display report
        print(report_text)
        print(f"\n📁 Report saved to: {filename}")
        print("✅ Quick daily report completed!")
        
        return True
    
    except Exception as e:
        print(f"❌ Quick report failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🚀 Quick daily report ready for LinkedIn!")
    else:
        print("\n💥 Report generation failed.")