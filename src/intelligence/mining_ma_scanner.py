#!/usr/bin/env python3
"""
Mining M&A News Scanner
Scans for mergers, acquisitions, takeovers, and partnerships in mining sector
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import yfinance as yf

class MiningMAScanner:
    def __init__(self):
        self.ma_keywords = [
            'acquisition', 'merger', 'takeover', 'buyout', 'purchase',
            'joint venture', 'partnership', 'strategic investment',
            'consolidation', 'combination', 'deal', 'transaction',
            'bid', 'offer', 'acquire', 'merge', 'buy', 'sells to',
            'agrees to buy', 'to acquire', 'signs agreement'
        ]
        
        self.mining_companies = [
            'barrick', 'newmont', 'agnico eagle', 'kinross', 'franco-nevada',
            'first quantum', 'lundin', 'hudbay', 'eldorado', 'iamgold',
            'centerra', 'torex', 'seabridge', 'alamos', 'calibre',
            'mag silver', 'new gold', 'osisko', 'yamana', 'kirkland lake',
            'goldcorp', 'placer dome', 'anglogold', 'harmony', 'sibanye',
            'northern star', 'evolution', 'newcrest', 'rio tinto', 'bhp',
            'vale', 'glencore', 'antofagasta', 'freeport', 'southern copper'
        ]
        
        self.ma_news = []
        
    def scan_rss_feeds(self):
        """Scan RSS feeds for M&A news"""
        
        print("📰 Scanning RSS feeds for M&A activity...")
        
        feeds = [
            ('Mining.com', 'https://www.mining.com/feed/'),
            ('Kitco News', 'https://www.kitco.com/rss/KitcoNews.xml'),
            ('Reuters Business', 'https://feeds.reuters.com/reuters/businessNews'),
            ('Bloomberg Mining', 'https://feeds.bloomberg.com/bview/news.rss'),
            ('Mining Journal', 'https://feeds.feedburner.com/mining-journal')
        ]
        
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        for source_name, feed_url in feeds:
            try:
                print(f"  🔍 Checking {source_name}...")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:50]:  # Check last 50 items
                    try:
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        content = title + ' ' + summary
                        
                        # Check for M&A keywords
                        ma_mentions = [kw for kw in self.ma_keywords if kw in content]
                        
                        if ma_mentions:
                            # Check for mining company mentions
                            mining_mentions = [comp for comp in self.mining_companies if comp in content]
                            
                            if mining_mentions:
                                # Check if from this month
                                pub_date = entry.get('published_parsed')
                                if pub_date and pub_date[1] == current_month and pub_date[0] == current_year:
                                    
                                    # Extract financial figures if any
                                    financial_figures = self.extract_deal_value(entry.get('title', '') + ' ' + entry.get('summary', ''))
                                    
                                    ma_item = {
                                        'title': entry.get('title', ''),
                                        'summary': entry.get('summary', '')[:300] + '...' if len(entry.get('summary', '')) > 300 else entry.get('summary', ''),
                                        'url': entry.get('link', ''),
                                        'published': entry.get('published', ''),
                                        'source': source_name,
                                        'ma_keywords': ma_mentions,
                                        'companies_involved': mining_mentions,
                                        'deal_value': financial_figures,
                                        'relevance_score': len(ma_mentions) * 5 + len(mining_mentions) * 3
                                    }
                                    
                                    self.ma_news.append(ma_item)
                    
                    except Exception as e:
                        continue
                
                print(f"    ✓ Found {len([item for item in self.ma_news if item['source'] == source_name])} M&A items")
                
            except Exception as e:
                print(f"    ✗ Error with {source_name}: {e}")
                continue
        
        print(f"📊 Total M&A news items found: {len(self.ma_news)}")
        
    def extract_deal_value(self, text):
        """Extract deal values from text"""
        
        # Patterns for deal values
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|M|B)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion)\s*(?:dollar|USD|CAD)',
            r'C?\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'valued?\s+at.*?\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'worth.*?\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        ]
        
        extracted_values = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_values.extend(match)
                else:
                    extracted_values.append(match)
        
        return extracted_values[:3] if extracted_values else []
    
    def search_recent_ma_news(self):
        """Search for recent M&A news through web scraping"""
        
        print("🔍 Searching recent M&A news...")
        
        # Search Mining.com specifically
        try:
            search_terms = ['acquisition', 'merger', 'takeover', 'deal']
            
            for term in search_terms:
                search_url = f"https://www.mining.com/?s={term}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for article links
                    articles = soup.find_all('a', href=True)
                    
                    for article in articles[:10]:
                        title = article.get_text(strip=True)
                        href = article.get('href', '')
                        
                        if len(title) > 20 and any(kw in title.lower() for kw in self.ma_keywords):
                            # Check for mining mentions
                            mining_mentions = [comp for comp in self.mining_companies if comp in title.lower()]
                            
                            if mining_mentions:
                                # Check if not already found
                                if not any(existing['url'] == href for existing in self.ma_news):
                                    
                                    ma_item = {
                                        'title': title,
                                        'summary': f'Found via search for "{term}"',
                                        'url': href,
                                        'published': 'Recent',
                                        'source': 'Mining.com Search',
                                        'ma_keywords': [kw for kw in self.ma_keywords if kw in title.lower()],
                                        'companies_involved': mining_mentions,
                                        'deal_value': self.extract_deal_value(title),
                                        'relevance_score': len(mining_mentions) * 5
                                    }
                                    
                                    self.ma_news.append(ma_item)
        
        except Exception as e:
            print(f"✗ Error in web search: {e}")
    
    def get_stock_impact_data(self):
        """Get stock price impact for companies involved in M&A"""
        
        print("📈 Analyzing stock price impacts...")
        
        # Extract unique companies and try to find their tickers
        company_tickers = {
            'agnico eagle': 'AEM.TO',
            'barrick': 'ABX.TO', 
            'kinross': 'K.TO',
            'franco-nevada': 'FNV.TO',
            'first quantum': 'FM.TO',
            'lundin': 'LUN.TO',
            'hudbay': 'HBM.TO',
            'eldorado': 'ELD.TO',
            'newmont': 'NEM',
            'freeport': 'FCX'
        }
        
        for ma_item in self.ma_news:
            companies = ma_item['companies_involved']
            
            for company in companies:
                if company in company_tickers:
                    ticker = company_tickers[company]
                    
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="5d")
                        
                        if not hist.empty:
                            current_price = hist['Close'][-1]
                            week_ago_price = hist['Close'][0] if len(hist) > 1 else current_price
                            change_percent = ((current_price - week_ago_price) / week_ago_price) * 100
                            
                            ma_item[f'{company}_stock_impact'] = {
                                'ticker': ticker,
                                'current_price': round(float(current_price), 2),
                                'weekly_change': round(change_percent, 1),
                                'volume': int(hist['Volume'][-1]) if not hist['Volume'].empty else 0
                            }
                    
                    except Exception as e:
                        continue
    
    def generate_ma_report(self):
        """Generate M&A activity report"""
        
        # Sort by relevance and date
        self.ma_news.sort(key=lambda x: (x['relevance_score'], x['published']), reverse=True)
        
        report = []
        report.append("💼 MINING M&A ACTIVITY - JULY 2025")
        report.append("=" * 45)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report.append(f"📊 Total M&A items found: {len(self.ma_news)}")
        report.append("")
        
        if not self.ma_news:
            report.append("📰 No significant M&A activity found in RSS feeds for July 2025")
            report.append("")
            report.append("💡 This could mean:")
            report.append("• Quiet month for mining M&A")
            report.append("• News not yet reflected in RSS feeds") 
            report.append("• Need broader search sources")
            report.append("")
            report.append("🔍 Recommended next steps:")
            report.append("• Check Bloomberg Terminal for recent deals")
            report.append("• Monitor TSX/NYSE press releases")
            report.append("• Search investment banking news")
            report.append("• Check mining conference announcements")
        else:
            # Categorize by deal type
            acquisitions = [item for item in self.ma_news if any(kw in item['ma_keywords'] for kw in ['acquisition', 'acquire', 'purchase', 'buy'])]
            mergers = [item for item in self.ma_news if any(kw in item['ma_keywords'] for kw in ['merger', 'merge', 'combination'])]
            partnerships = [item for item in self.ma_news if any(kw in item['ma_keywords'] for kw in ['partnership', 'joint venture', 'strategic'])]
            
            # Summary stats
            report.append("📊 M&A ACTIVITY BREAKDOWN")
            report.append("-" * 26)
            report.append(f"• Acquisitions: {len(acquisitions)}")
            report.append(f"• Mergers: {len(mergers)}")
            report.append(f"• Partnerships/JVs: {len(partnerships)}")
            report.append("")
            
            # Major deals
            if self.ma_news:
                report.append("🎯 MAJOR M&A TRANSACTIONS")
                report.append("-" * 27)
                
                for i, item in enumerate(self.ma_news[:10], 1):
                    report.append(f"{i}. {item['title']}")
                    report.append(f"   📅 {item['published']}")
                    report.append(f"   🏢 Companies: {', '.join(item['companies_involved'])}")
                    report.append(f"   🔗 Source: {item['source']}")
                    
                    if item['deal_value']:
                        report.append(f"   💰 Deal Value: {', '.join(item['deal_value'])}")
                    
                    # Stock impact if available
                    stock_impacts = {k: v for k, v in item.items() if 'stock_impact' in k}
                    if stock_impacts:
                        for company, impact in stock_impacts.items():
                            company_name = company.replace('_stock_impact', '')
                            report.append(f"   📈 {company_name.title()}: {impact['ticker']} ${impact['current_price']} ({impact['weekly_change']:+.1f}%)")
                    
                    report.append("")
        
        # Market context
        report.append("🌍 MARKET CONTEXT")
        report.append("-" * 15)
        report.append("• Mining sector consolidation trends")
        report.append("• Rising commodity prices driving activity")
        report.append("• ESG requirements favoring larger operators")
        report.append("• Geographic diversification strategies")
        report.append("")
        
        report.append("🔗 DATA SOURCES")
        report.append("-" * 13)
        sources = list(set(item['source'] for item in self.ma_news))
        for source in sources:
            count = len([item for item in self.ma_news if item['source'] == source])
            report.append(f"• {source}: {count} items")
        
        return "\n".join(report)
    
    def run_ma_analysis(self):
        """Run complete M&A analysis"""
        
        print("🚀 Starting Mining M&A Analysis for July 2025...")
        print("=" * 50)
        
        # Scan all sources
        self.scan_rss_feeds()
        self.search_recent_ma_news()
        
        # Analyze stock impacts
        self.get_stock_impact_data()
        
        # Generate report
        report = self.generate_ma_report()
        
        # Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON data
        json_filename = f"mining_ma_analysis_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(self.ma_news, f, indent=2, default=str)
        
        # Save report
        report_filename = f"mining_ma_report_{timestamp}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"\n📁 M&A data saved to: {json_filename}")
        print(f"📁 M&A report saved to: {report_filename}")
        
        return report, self.ma_news

if __name__ == "__main__":
    scanner = MiningMAScanner()
    report, data = scanner.run_ma_analysis()
    
    print("\n" + report)
    
    print("\n✅ Mining M&A analysis completed!")
    print("💡 For real-time M&A monitoring, run this daily")