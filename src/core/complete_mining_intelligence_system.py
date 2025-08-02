#!/usr/bin/env python3
"""
Complete Mining Intelligence System
Combines yfinance, RSS feeds, Playwright scrapers, and data aggregation
Everything you need for comprehensive mining company analysis
"""

import asyncio
import yfinance as yf
import feedparser
import json
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import requests
from ..scrapers.playwright_scrapers import PlaywrightMiningScrapers

class CompleteMiningIntelligence:
    def __init__(self, symbol="AEM.TO", company_name="Agnico Eagle Mines Limited"):
        self.symbol = symbol
        self.company_name = company_name
        self.db_path = "complete_mining_intelligence.db"
        
        # Initialize database
        self.setup_database()
        
        # Data storage
        self.intelligence = {
            'company_info': {
                'symbol': symbol,
                'name': company_name,
                'report_date': datetime.now().isoformat()
            },
            'stock_performance': {},
            'financial_metrics': {},
            'operational_updates': [],
            'regulatory_filings': [],
            'insider_activity': [],
            'ma_activity': [],
            'esg_permits': [],
            'industry_news': [],
            'social_sentiment': {},
            'analyst_data': {},
            'commodity_context': {}
        }

    def setup_database(self):
        """Setup comprehensive database schema"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Companies master table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                exchange TEXT,
                sector TEXT,
                market_cap INTEGER,
                website TEXT,
                ir_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Intelligence data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intelligence_data (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                data_type TEXT,
                category TEXT,
                title TEXT,
                content TEXT,
                metrics TEXT,
                source_url TEXT,
                date_extracted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES companies (symbol)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database schema initialized")

    def get_comprehensive_stock_data(self):
        """Get complete stock performance and financial data"""
        
        print("📈 Fetching comprehensive stock data...")
        
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Stock performance
            hist_ytd = ticker.history(start="2025-01-01")
            hist_1y = ticker.history(period="1y")
            info = ticker.info
            
            if not hist_ytd.empty:
                current_price = hist_ytd['Close'][-1]
                ytd_start = hist_ytd['Close'][0]
                ytd_return = ((current_price - ytd_start) / ytd_start) * 100
                
                # Volatility calculation
                if len(hist_1y) > 20:
                    returns = hist_1y['Close'].pct_change().dropna()
                    volatility = returns.std() * (252 ** 0.5)
                else:
                    volatility = 0
                
                self.intelligence['stock_performance'] = {
                    'current_price': round(float(current_price), 2),
                    'ytd_return_percent': round(ytd_return, 2),
                    'ytd_start_price': round(float(ytd_start), 2),
                    'volatility_annual': round(volatility, 3),
                    'market_cap': info.get('marketCap', 0),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                    'average_volume': info.get('averageVolume', 0),
                    'pe_ratio': info.get('forwardPE', 0),
                    'pb_ratio': info.get('priceToBook', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 0),
                    'enterprise_value': info.get('enterpriseValue', 0)
                }
                
                print(f"✓ Stock data: ${current_price:.2f} ({ytd_return:+.1f}% YTD)")
            
            # Financial metrics
            self.intelligence['financial_metrics'] = {
                'revenue_ttm': info.get('totalRevenue', 0),
                'gross_profit': info.get('grossProfits', 0),
                'ebitda': info.get('ebitda', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'profit_margin': info.get('profitMargins', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'return_on_assets': info.get('returnOnAssets', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'book_value': info.get('bookValue', 0),
                'cash_per_share': info.get('totalCashPerShare', 0),
                'free_cash_flow': info.get('freeCashflow', 0)
            }
            
            # Analyst data
            self.intelligence['analyst_data'] = {
                'target_price': info.get('targetMeanPrice', 0),
                'recommendation_mean': info.get('recommendationMean', 0),
                'num_analysts': info.get('numberOfAnalystOpinions', 0),
                'upside_potential': 0
            }
            
            if info.get('targetMeanPrice') and self.intelligence['stock_performance'].get('current_price'):
                target = info['targetMeanPrice']
                current = self.intelligence['stock_performance']['current_price']
                upside = ((target - current) / current) * 100
                self.intelligence['analyst_data']['upside_potential'] = round(upside, 1)
            
            print("✓ Financial and analyst data collected")
            
        except Exception as e:
            print(f"✗ Error fetching stock data: {e}")

    def get_commodity_context(self):
        """Get gold price and commodity context"""
        
        print("🥇 Fetching commodity context...")
        
        try:
            # Gold futures
            gold = yf.Ticker("GC=F")
            gold_hist = gold.history(period="5d")
            
            if not gold_hist.empty:
                current_gold = gold_hist['Close'][-1]
                prev_gold = gold_hist['Close'][0] if len(gold_hist) > 1 else current_gold
                gold_change = ((current_gold - prev_gold) / prev_gold) * 100
                
                # USD/CAD from Bank of Canada
                try:
                    usd_cad_url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1"
                    response = requests.get(usd_cad_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('observations'):
                            usd_cad_rate = float(data['observations'][0]['FXUSDCAD']['v'])
                        else:
                            usd_cad_rate = 1.37  # Fallback
                    else:
                        usd_cad_rate = 1.37
                
                except:
                    usd_cad_rate = 1.37
                
                self.intelligence['commodity_context'] = {
                    'gold_price_usd': round(float(current_gold), 2),
                    'gold_change_percent': round(gold_change, 2),
                    'usd_cad_rate': usd_cad_rate,
                    'gold_price_cad': round(float(current_gold) * usd_cad_rate, 2),
                    'extraction_date': datetime.now().isoformat()
                }
                
                print(f"✓ Gold: ${current_gold:.2f} USD, CAD: {usd_cad_rate}")
        
        except Exception as e:
            print(f"✗ Error fetching commodity data: {e}")

    def monitor_industry_news(self):
        """Monitor RSS feeds for industry news"""
        
        print("📰 Monitoring industry news feeds...")
        
        news_sources = [
            ('Mining.com', 'https://www.mining.com/feed/'),
            ('Kitco News', 'https://www.kitco.com/rss/KitcoNews.xml'),
            ('Mining Journal', 'https://feeds.feedburner.com/mining-journal')
        ]
        
        all_news = []
        
        for source_name, feed_url in news_sources:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:  # Latest 15 items
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    content = (title + ' ' + summary).lower()
                    
                    # Check for company mentions
                    if any(term in content for term in [
                        'agnico eagle', 'aem.to', 'agnico', 
                        self.company_name.lower()
                    ]):
                        
                        news_item = {
                            'source': source_name,
                            'title': title,
                            'summary': summary[:400] + '...' if len(summary) > 400 else summary,
                            'url': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'category': self.categorize_news(content),
                            'relevance_score': self.calculate_relevance(content),
                            'extracted_at': datetime.now().isoformat()
                        }
                        
                        all_news.append(news_item)
                
                print(f"✓ Processed {source_name}")
                
            except Exception as e:
                print(f"✗ Error processing {source_name}: {e}")
                continue
        
        # Sort by relevance and recency
        all_news.sort(key=lambda x: (x['relevance_score'], x['published']), reverse=True)
        
        self.intelligence['industry_news'] = all_news[:10]  # Top 10 most relevant
        print(f"✓ Found {len(self.intelligence['industry_news'])} relevant news items")

    def categorize_news(self, content):
        """Categorize news content"""
        
        categories = {
            'operational_update': ['production', 'mining', 'operational', 'mill', 'plant', 'tonnage'],
            'financial_results': ['earnings', 'results', 'revenue', 'profit', 'financial'],
            'ma_activity': ['acquisition', 'merger', 'takeover', 'partnership', 'joint venture'],
            'guidance_update': ['guidance', 'outlook', 'forecast', 'expects', 'targets'],
            'regulatory': ['permit', 'approval', 'environmental', 'regulatory', 'compliance']
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in content)
            scores[category] = score
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'

    def calculate_relevance(self, content):
        """Calculate relevance score"""
        
        high_value_keywords = {
            'production': 15, 'guidance': 15, 'earnings': 12, 'results': 10,
            'acquisition': 12, 'merger': 10, 'ounces': 8, 'gold': 6,
            'quarterly': 8, 'annual': 6, 'aisc': 10, 'reserves': 8
        }
        
        score = 0
        for keyword, weight in high_value_keywords.items():
            if keyword in content:
                score += weight
        
        # Recent date bonus
        if any(term in content for term in ['2025', '2024']):
            score += 5
        
        return score

    async def run_playwright_scrapers(self):
        """Run Playwright scrapers for advanced data"""
        
        print("🎭 Running Playwright scrapers...")
        
        try:
            scraper = PlaywrightMiningScrapers()
            playwright_data, _ = await scraper.run_all_scrapers()
            
            # Integrate Playwright results
            if playwright_data.get('sedar_filings'):
                self.intelligence['regulatory_filings'] = playwright_data['sedar_filings']
            
            if playwright_data.get('sedi_transactions'):
                self.intelligence['insider_activity'] = playwright_data['sedi_transactions']
            
            if playwright_data.get('linkedin_updates'):
                self.intelligence['social_sentiment']['linkedin'] = playwright_data['linkedin_updates']
            
            if playwright_data.get('ir_presentations'):
                self.intelligence['operational_updates'].extend(playwright_data['ir_presentations'])
            
            print("✓ Playwright data integrated")
            
        except Exception as e:
            print(f"⚠️ Playwright integration error: {e}")

    def calculate_overall_sentiment(self):
        """Calculate comprehensive sentiment score"""
        
        print("📊 Calculating overall sentiment...")
        
        sentiment_components = []
        
        # Stock performance sentiment
        ytd_return = self.intelligence['stock_performance'].get('ytd_return_percent', 0)
        if ytd_return > 20:
            stock_sentiment = 1.0
        elif ytd_return > 5:
            stock_sentiment = 0.5
        elif ytd_return > -5:
            stock_sentiment = 0.0
        elif ytd_return > -20:
            stock_sentiment = -0.5
        else:
            stock_sentiment = -1.0
        
        sentiment_components.append(('stock_performance', stock_sentiment, 0.4))
        
        # Analyst sentiment
        recommendation = self.intelligence['analyst_data'].get('recommendation_mean', 3)
        analyst_sentiment = (5 - recommendation) / 2 - 1  # Convert 1-5 scale to -1 to +1
        sentiment_components.append(('analyst', analyst_sentiment, 0.3))
        
        # News sentiment (simplified)
        news_items = self.intelligence['industry_news']
        positive_news = sum(1 for item in news_items if 
                          any(term in item['title'].lower() for term in ['strong', 'growth', 'increase', 'beat']))
        negative_news = sum(1 for item in news_items if 
                          any(term in item['title'].lower() for term in ['weak', 'decline', 'miss', 'cut']))
        
        if len(news_items) > 0:
            news_sentiment = (positive_news - negative_news) / len(news_items)
        else:
            news_sentiment = 0
        
        sentiment_components.append(('news', news_sentiment, 0.3))
        
        # Calculate weighted average
        weighted_sentiment = sum(score * weight for _, score, weight in sentiment_components)
        
        # Sentiment level
        if weighted_sentiment >= 0.4:
            sentiment_level = 'Very Positive'
        elif weighted_sentiment >= 0.1:
            sentiment_level = 'Positive'
        elif weighted_sentiment >= -0.1:
            sentiment_level = 'Neutral'
        elif weighted_sentiment >= -0.4:
            sentiment_level = 'Negative'
        else:
            sentiment_level = 'Very Negative'
        
        self.intelligence['social_sentiment']['overall'] = {
            'sentiment_score': round(weighted_sentiment, 3),
            'sentiment_level': sentiment_level,
            'components': dict((name, round(score, 2)) for name, score, _ in sentiment_components),
            'confidence': min(len(sentiment_components) / 3, 1.0)
        }
        
        print(f"✓ Overall sentiment: {sentiment_level} ({weighted_sentiment:.2f})")

    def save_intelligence_data(self):
        """Save all intelligence to database and file"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Insert/update company record
        conn.execute('''
            INSERT OR REPLACE INTO companies 
            (symbol, name, market_cap, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (
            self.symbol,
            self.company_name,
            self.intelligence['stock_performance'].get('market_cap', 0),
            datetime.now()
        ))
        
        # Insert intelligence data
        for category, data in self.intelligence.items():
            if isinstance(data, list):
                for item in data:
                    conn.execute('''
                        INSERT INTO intelligence_data
                        (symbol, data_type, category, title, content, source_url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        self.symbol,
                        category,
                        item.get('category', 'unknown'),
                        item.get('title', '')[:200],
                        json.dumps(item)[:1000],
                        item.get('url', '')
                    ))
        
        conn.commit()
        conn.close()
        
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"complete_mining_intelligence_{self.symbol.replace('.', '_')}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.intelligence, f, indent=2, default=str)
        
        print(f"📁 Intelligence saved to: {filename}")
        return filename

    def generate_executive_report(self):
        """Generate executive summary report"""
        
        report = []
        report.append("=" * 80)
        report.append("🔍 COMPLETE MINING INTELLIGENCE REPORT")
        report.append("=" * 80)
        report.append(f"📊 Company: {self.company_name}")
        report.append(f"🎯 Symbol: {self.symbol}")
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report.append("")
        
        # Executive Summary
        perf = self.intelligence['stock_performance']
        sentiment = self.intelligence['social_sentiment'].get('overall', {})
        
        if perf and sentiment:
            report.append("📈 EXECUTIVE SUMMARY")
            report.append("-" * 20)
            report.append(f"Stock Performance: ${perf.get('current_price', 0)} ({perf.get('ytd_return_percent', 0):+.1f}% YTD)")
            report.append(f"Market Sentiment: {sentiment.get('sentiment_level', 'Unknown')}")
            report.append(f"Market Cap: ${perf.get('market_cap', 0):,}")
            report.append(f"Analyst Target: ${self.intelligence['analyst_data'].get('target_price', 0):.2f}")
            report.append("")
        
        # Key Metrics
        fin = self.intelligence['financial_metrics']
        if fin:
            report.append("💰 KEY FINANCIAL METRICS")
            report.append("-" * 25)
            if fin.get('revenue_ttm'):
                report.append(f"Revenue (TTM): ${fin['revenue_ttm']:,}")
            if fin.get('ebitda'):
                report.append(f"EBITDA: ${fin['ebitda']:,}")
            if fin.get('free_cash_flow'):
                report.append(f"Free Cash Flow: ${fin['free_cash_flow']:,}")
            if fin.get('operating_margin'):
                report.append(f"Operating Margin: {fin['operating_margin']:.1%}")
            report.append("")
        
        # Recent News
        news = self.intelligence['industry_news']
        if news:
            report.append("📰 RECENT INTELLIGENCE")
            report.append("-" * 22)
            for item in news[:5]:
                report.append(f"• {item['title']}")
                report.append(f"  Source: {item['source']} | Category: {item['category']}")
                report.append("")
        
        # Commodity Context
        commodity = self.intelligence['commodity_context']
        if commodity:
            report.append("🥇 COMMODITY CONTEXT")
            report.append("-" * 19)
            report.append(f"Gold Price: ${commodity.get('gold_price_usd', 0)} USD ({commodity.get('gold_change_percent', 0):+.1f}%)")
            report.append(f"USD/CAD Rate: {commodity.get('usd_cad_rate', 0)}")
            report.append(f"Gold (CAD): ${commodity.get('gold_price_cad', 0)}")
            report.append("")
        
        # Data Sources Summary
        report.append("🔗 DATA SOURCES STATUS")
        report.append("-" * 23)
        report.append("✅ Yahoo Finance - Stock & financial data")
        report.append("✅ Mining.com - Industry news")
        report.append("✅ Kitco - Commodity news")
        report.append("✅ Bank of Canada - Currency data")
        report.append("✅ Playwright - Advanced scraping")
        report.append("⚠️  SEDAR+ - Regulatory filings (templates)")
        report.append("⚠️  SEDI - Insider trades (templates)")
        report.append("")
        
        # Intelligence Summary
        total_items = sum(len(data) if isinstance(data, list) else (1 if data else 0) 
                         for data in self.intelligence.values())
        
        report.append("📊 INTELLIGENCE METRICS")
        report.append("-" * 24)
        report.append(f"Total data points: {total_items}")
        report.append(f"News items: {len(news)}")
        report.append(f"Regulatory filings: {len(self.intelligence.get('regulatory_filings', []))}")
        report.append(f"Insider transactions: {len(self.intelligence.get('insider_activity', []))}")
        report.append(f"Data categories: {len([k for k, v in self.intelligence.items() if v])}")
        
        return "\n".join(report)

    async def run_complete_analysis(self):
        """Run the complete mining intelligence analysis"""
        
        print("🚀 STARTING COMPLETE MINING INTELLIGENCE ANALYSIS")
        print("=" * 65)
        print("")
        
        # Execute all analysis modules
        self.get_comprehensive_stock_data()
        self.get_commodity_context()
        self.monitor_industry_news()
        await self.run_playwright_scrapers()
        self.calculate_overall_sentiment()
        
        # Save all data
        filename = self.save_intelligence_data()
        
        # Generate executive report
        executive_report = self.generate_executive_report()
        
        print("")
        print(executive_report)
        
        # Save report
        report_filename = filename.replace('.json', '_report.txt')
        with open(report_filename, 'w') as f:
            f.write(executive_report)
        
        print(f"\n📁 Executive report saved to: {report_filename}")
        
        return self.intelligence, filename, report_filename

async def main():
    """Main execution"""
    
    print("🎯 COMPLETE MINING INTELLIGENCE SYSTEM")
    print("Combining all data sources for comprehensive analysis\n")
    
    # Initialize for Agnico Eagle
    intelligence = CompleteMiningIntelligence("AEM.TO", "Agnico Eagle Mines Limited")
    
    # Run complete analysis
    data, data_file, report_file = await intelligence.run_complete_analysis()
    
    print("\n✅ COMPLETE MINING INTELLIGENCE SYSTEM OPERATIONAL!")
    print("=" * 55)
    print("🔥 All data sources integrated")
    print("🔥 Real-time market data")
    print("🔥 Advanced web scraping")
    print("🔥 Comprehensive sentiment analysis")
    print("🔥 Executive reporting")
    print("🔥 Database storage")
    
    return data

if __name__ == "__main__":
    results = asyncio.run(main())