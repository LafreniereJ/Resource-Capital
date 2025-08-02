#!/usr/bin/env python3
"""
Comprehensive Agnico Eagle Analysis
Combines multiple data sources for complete operational intelligence
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup
import re

class AgnicoEagleAnalyzer:
    def __init__(self):
        self.symbol = "AEM.TO"
        self.company_name = "Agnico Eagle Mines Limited"
        self.website = "https://www.agnicoeagle.com"
        self.ir_url = "https://www.agnicoeagle.com/English/investor-relations/"
        
        # Initialize data storage
        self.data = {
            'stock_performance': {},
            'operational_data': {},
            'projects': [],
            'production_data': {},
            'financial_metrics': {},
            'insider_transactions': [],
            'guidance': {},
            'sentiment': {},
            'market_comparison': {}
        }
    
    def get_stock_performance(self):
        """Get detailed stock performance data"""
        
        print("📈 Fetching stock performance data...")
        
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Get historical data for YTD analysis
            start_of_year = datetime(2025, 1, 1)
            hist = ticker.history(start=start_of_year)
            
            if not hist.empty:
                # Current data
                current_price = hist['Close'][-1]
                ytd_start_price = hist['Close'][0]
                ytd_return = ((current_price - ytd_start_price) / ytd_start_price) * 100
                
                # 52-week data
                info = ticker.info
                
                self.data['stock_performance'] = {
                    'current_price': round(float(current_price), 2),
                    'ytd_return_percent': round(ytd_return, 2),
                    'ytd_start_price': round(float(ytd_start_price), 2),
                    'market_cap': info.get('marketCap', 0),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                    'pe_ratio': info.get('forwardPE', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 0),
                    'avg_volume': info.get('averageVolume', 0),
                    'enterprise_value': info.get('enterpriseValue', 0)
                }
                
                print(f"✓ Current Price: ${current_price:.2f}")
                print(f"✓ YTD Return: {ytd_return:+.1f}%")
                
        except Exception as e:
            print(f"✗ Error fetching stock data: {e}")
    
    def get_financial_metrics(self):
        """Get key financial metrics from yfinance"""
        
        print("💰 Fetching financial metrics...")
        
        try:
            ticker = yf.Ticker(self.symbol)
            info = ticker.info
            
            # Get quarterly earnings data
            quarterly_earnings = ticker.quarterly_earnings
            
            self.data['financial_metrics'] = {
                'revenue_ttm': info.get('totalRevenue', 0),
                'gross_profit': info.get('grossProfits', 0),
                'operating_margin': info.get('operatingMargins', 0),
                'profit_margin': info.get('profitMargins', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'book_value': info.get('bookValue', 0),
                'cash_per_share': info.get('totalCashPerShare', 0),
                'free_cash_flow': info.get('freeCashflow', 0),
                'ebitda': info.get('ebitda', 0)
            }
            
            if not quarterly_earnings.empty:
                latest_quarter_revenue = quarterly_earnings.iloc[0, 0] if len(quarterly_earnings) > 0 else 0
                self.data['financial_metrics']['latest_quarter_revenue'] = latest_quarter_revenue
            
            print(f"✓ Revenue TTM: ${self.data['financial_metrics']['revenue_ttm']:,}")
            print(f"✓ Market Cap: ${self.data['stock_performance']['market_cap']:,}")
            
        except Exception as e:
            print(f"✗ Error fetching financial metrics: {e}")
    
    def get_gold_correlation(self):
        """Calculate correlation with gold price"""
        
        print("🥇 Analyzing gold correlation...")
        
        try:
            # Get AEM and gold data for correlation analysis
            aem = yf.Ticker(self.symbol)
            gold = yf.Ticker("GC=F")
            
            start_date = datetime(2025, 1, 1)
            
            aem_hist = aem.history(start=start_date)
            gold_hist = gold.history(start=start_date)
            
            if not aem_hist.empty and not gold_hist.empty:
                # Align dates and calculate correlation
                aem_returns = aem_hist['Close'].pct_change().dropna()
                gold_returns = gold_hist['Close'].pct_change().dropna()
                
                # Find common dates
                common_dates = aem_returns.index.intersection(gold_returns.index)
                
                if len(common_dates) > 10:
                    aem_aligned = aem_returns.loc[common_dates]
                    gold_aligned = gold_returns.loc[common_dates]
                    
                    correlation = aem_aligned.corr(gold_aligned)
                    
                    # Current gold price
                    current_gold = gold_hist['Close'][-1]
                    gold_ytd_start = gold_hist['Close'][0]
                    gold_ytd_return = ((current_gold - gold_ytd_start) / gold_ytd_start) * 100
                    
                    self.data['market_comparison'] = {
                        'gold_correlation': round(correlation, 3),
                        'current_gold_price': round(float(current_gold), 2),
                        'gold_ytd_return': round(gold_ytd_return, 2),
                        'relative_performance': round(self.data['stock_performance']['ytd_return_percent'] - gold_ytd_return, 2)
                    }
                    
                    print(f"✓ Gold Correlation: {correlation:.3f}")
                    print(f"✓ Gold YTD: {gold_ytd_return:+.1f}%")
                    print(f"✓ Relative Performance: {self.data['market_comparison']['relative_performance']:+.1f}%")
        
        except Exception as e:
            print(f"✗ Error calculating gold correlation: {e}")
    
    def scrape_investor_relations(self):
        """Scrape investor relations page for operational data"""
        
        print("🔍 Scraping investor relations data...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try to get recent news releases
            news_urls = [
                "https://www.agnicoeagle.com/English/investor-relations/news-releases/default.aspx",
                "https://www.agnicoeagle.com/English/operations/default.aspx"
            ]
            
            for url in news_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for production data patterns
                        text_content = soup.get_text().lower()
                        
                        # Extract production figures (ounces)
                        production_patterns = [
                            r'(\d{1,3}(?:,\d{3})*)\s*(?:ounces?|oz)',
                            r'(\d{1,3}(?:,\d{3})*)\s*(?:tonnes?|tons)',
                            r'aisc.*?\$(\d{1,4})',
                            r'guidance.*?(\d{1,3}(?:,\d{3})*)',
                            r'production.*?(\d{1,3}(?:,\d{3})*)'
                        ]
                        
                        extracted_data = {}
                        for pattern in production_patterns:
                            matches = re.findall(pattern, text_content)
                            if matches:
                                extracted_data[pattern] = matches[:5]  # Top 5 matches
                        
                        if extracted_data:
                            self.data['operational_data']['scraped_data'] = extracted_data
                            print(f"✓ Extracted data from {url}")
                            break
                
                except Exception as e:
                    print(f"✗ Error scraping {url}: {e}")
                    continue
        
        except Exception as e:
            print(f"✗ Error in IR scraping: {e}")
    
    def get_known_operational_data(self):
        """Add known operational data for Agnico Eagle (2024/2025 data)"""
        
        print("📊 Adding known operational data...")
        
        # Known data from public sources
        self.data['operational_data'] = {
            'major_operations': [
                {
                    'name': 'Canadian Malartic',
                    'location': 'Quebec, Canada',
                    'type': 'Open pit',
                    'status': 'Operating'
                },
                {
                    'name': 'LaRonde Complex',
                    'location': 'Quebec, Canada', 
                    'type': 'Underground',
                    'status': 'Operating'
                },
                {
                    'name': 'Meadowbank Complex',
                    'location': 'Nunavut, Canada',
                    'type': 'Open pit',
                    'status': 'Operating'
                },
                {
                    'name': 'Detour Lake',
                    'location': 'Ontario, Canada',
                    'type': 'Open pit',
                    'status': 'Operating'
                },
                {
                    'name': 'Fosterville',
                    'location': 'Australia',
                    'type': 'Underground',
                    'status': 'Operating'
                },
                {
                    'name': 'Macassa',
                    'location': 'Ontario, Canada',
                    'type': 'Underground',
                    'status': 'Operating'
                }
            ],
            'total_operations': 8,
            'countries': ['Canada', 'Australia', 'Finland', 'Mexico'],
            'primary_commodity': 'Gold',
            'secondary_commodities': ['Silver', 'Zinc', 'Copper']
        }
        
        # Estimated production data (would need real API access for exact figures)
        self.data['production_data'] = {
            'estimated_2024_production_oz': 3100000,  # ~3.1M oz (estimate)
            'estimated_2025_guidance_oz': 3200000,    # ~3.2M oz (estimate)
            'estimated_aisc_per_oz': 1350,           # ~$1,350/oz (estimate)
            'reserves_moz': 48.6,                    # Million ounces (approximate)
            'resources_moz': 108.4                   # Million ounces (approximate)
        }
        
        print("✓ Added operational baseline data")
    
    def check_insider_transactions(self):
        """Check for recent insider transactions"""
        
        print("👔 Checking insider transactions...")
        
        # Note: Real implementation would use Canadian Insider API
        # For now, we'll structure the data format
        self.data['insider_transactions'] = {
            'data_source': 'Canadian Insider (requires API access)',
            'recent_transactions': [],
            'note': 'Need access to Canadian Insider database for real-time data'
        }
        
        print("⚠️  Insider data requires Canadian Insider API access")
    
    def analyze_recent_guidance(self):
        """Analyze recent guidance updates"""
        
        print("🎯 Analyzing guidance updates...")
        
        # Structure for guidance data (would need company filings API)
        self.data['guidance'] = {
            '2025_production_guidance': {
                'gold_ounces': '3.15 - 3.35 million oz (estimated)',
                'aisc_per_oz': '$1,320 - $1,420 (estimated)',
                'capital_expenditure': 'To be determined from filings'
            },
            'data_source': 'Company press releases and SEDAR+ filings',
            'last_updated': 'Requires real-time access to company communications'
        }
        
        print("⚠️  Guidance data requires SEDAR+ API access")
    
    def calculate_sentiment_indicators(self):
        """Calculate basic sentiment indicators"""
        
        print("📊 Calculating sentiment indicators...")
        
        # Basic sentiment from numerical data
        stock_perf = self.data['stock_performance']
        
        if stock_perf:
            # Performance-based sentiment
            ytd_performance = stock_perf.get('ytd_return_percent', 0)
            relative_gold_perf = self.data['market_comparison'].get('relative_performance', 0)
            
            # Simple sentiment scoring
            sentiment_score = 0
            
            if ytd_performance > 10:
                sentiment_score += 2
            elif ytd_performance > 0:
                sentiment_score += 1
            elif ytd_performance < -10:
                sentiment_score -= 2
            elif ytd_performance < 0:
                sentiment_score -= 1
            
            if relative_gold_perf > 5:
                sentiment_score += 1
            elif relative_gold_perf < -5:
                sentiment_score -= 1
            
            sentiment_levels = {
                -3: 'Very Negative',
                -2: 'Negative', 
                -1: 'Slightly Negative',
                0: 'Neutral',
                1: 'Slightly Positive',
                2: 'Positive',
                3: 'Very Positive'
            }
            
            self.data['sentiment'] = {
                'numerical_sentiment_score': sentiment_score,
                'sentiment_level': sentiment_levels.get(sentiment_score, 'Neutral'),
                'ytd_performance_factor': ytd_performance,
                'gold_relative_factor': relative_gold_perf,
                'note': 'Sentiment based on numerical performance metrics'
            }
            
            print(f"✓ Sentiment: {sentiment_levels.get(sentiment_score, 'Neutral')}")
    
    def generate_comprehensive_report(self):
        """Generate the comprehensive report"""
        
        print("\n" + "="*60)
        print("🔍 AGNICO EAGLE COMPREHENSIVE ANALYSIS")
        print("="*60)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🏢 Company: {self.company_name}")
        print(f"📊 Symbol: {self.symbol}")
        print("")
        
        # Stock Performance
        if self.data['stock_performance']:
            print("📈 STOCK PERFORMANCE")
            print("-" * 20)
            perf = self.data['stock_performance']
            print(f"Current Price: ${perf['current_price']}")
            print(f"YTD Return: {perf['ytd_return_percent']:+.1f}%")
            print(f"Market Cap: ${perf['market_cap']:,}")
            print(f"52W High: ${perf['fifty_two_week_high']}")
            print(f"52W Low: ${perf['fifty_two_week_low']}")
            if perf['pe_ratio']:
                print(f"P/E Ratio: {perf['pe_ratio']:.1f}")
            if perf['dividend_yield']:
                print(f"Dividend Yield: {perf['dividend_yield']:.2%}")
            print("")
        
        # Financial Metrics
        if self.data['financial_metrics']:
            print("💰 FINANCIAL METRICS")
            print("-" * 20)
            fin = self.data['financial_metrics']
            if fin['revenue_ttm']:
                print(f"Revenue (TTM): ${fin['revenue_ttm']:,}")
            if fin['ebitda']:
                print(f"EBITDA: ${fin['ebitda']:,}")
            if fin['free_cash_flow']:
                print(f"Free Cash Flow: ${fin['free_cash_flow']:,}")
            if fin['operating_margin']:
                print(f"Operating Margin: {fin['operating_margin']:.1%}")
            if fin['return_on_equity']:
                print(f"ROE: {fin['return_on_equity']:.1%}")
            print("")
        
        # Gold Correlation
        if self.data['market_comparison']:
            print("🥇 GOLD MARKET ANALYSIS")
            print("-" * 22)
            gold = self.data['market_comparison']
            print(f"Gold Price: ${gold['current_gold_price']}")
            print(f"Gold YTD: {gold['gold_ytd_return']:+.1f}%")
            print(f"AEM vs Gold: {gold['relative_performance']:+.1f}%")
            print(f"Correlation: {gold['gold_correlation']:.3f}")
            print("")
        
        # Operations
        if self.data['operational_data']:
            print("⚙️ OPERATIONS OVERVIEW")
            print("-" * 21)
            ops = self.data['operational_data']
            
            if 'major_operations' in ops:
                print(f"Total Operations: {ops['total_operations']}")
                print(f"Countries: {', '.join(ops['countries'])}")
                print(f"Primary Commodity: {ops['primary_commodity']}")
                print("")
                print("Major Operations:")
                for op in ops['major_operations']:
                    print(f"• {op['name']} ({op['location']}) - {op['type']}")
                print("")
        
        # Production Data
        if self.data['production_data']:
            print("📊 PRODUCTION DATA (ESTIMATES)")
            print("-" * 31)
            prod = self.data['production_data']
            print(f"2024 Production (est.): {prod['estimated_2024_production_oz']:,} oz")
            print(f"2025 Guidance (est.): {prod['estimated_2025_guidance_oz']:,} oz")
            print(f"AISC (est.): ${prod['estimated_aisc_per_oz']}/oz")
            print(f"Reserves: {prod['reserves_moz']} Moz")
            print(f"Resources: {prod['resources_moz']} Moz")
            print("")
        
        # Sentiment
        if self.data['sentiment']:
            print("📊 MARKET SENTIMENT")
            print("-" * 17)
            sent = self.data['sentiment']
            print(f"Sentiment Level: {sent['sentiment_level']}")
            print(f"Score: {sent['numerical_sentiment_score']}/3")
            print(f"YTD Factor: {sent['ytd_performance_factor']:+.1f}%")
            print(f"vs Gold Factor: {sent['gold_relative_factor']:+.1f}%")
            print("")
        
        # Data Requirements
        print("🔗 DATA SOURCE REQUIREMENTS")
        print("-" * 28)
        print("For complete analysis, need access to:")
        print("• SEDAR+ API - Financial filings, guidance updates")
        print("• Canadian Insider API - Real-time insider transactions")
        print("• Company IR API - Production data, project updates")
        print("• Mining industry databases - AISC benchmarks")
        print("• Social sentiment APIs - Reddit, Twitter analysis")
        print("")
        
        return self.data
    
    def run_analysis(self):
        """Run the complete analysis"""
        
        print("🚀 Starting Agnico Eagle comprehensive analysis...")
        print("")
        
        # Execute all analysis steps
        self.get_stock_performance()
        self.get_financial_metrics()
        self.get_gold_correlation()
        self.get_known_operational_data()
        self.scrape_investor_relations()
        self.check_insider_transactions()
        self.analyze_recent_guidance()
        self.calculate_sentiment_indicators()
        
        # Generate final report
        return self.generate_comprehensive_report()

if __name__ == "__main__":
    analyzer = AgnicoEagleAnalyzer()
    data = analyzer.run_analysis()
    
    # Save data to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agnico_eagle_analysis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"📁 Analysis saved to: {filename}")
    print("✅ Agnico Eagle comprehensive analysis completed!")