#!/usr/bin/env python3
"""
Daily TSX Mining Report Generator
Comprehensive report focusing on today's important news and updates for all TSX mining companies
"""

import asyncio
import json
import requests
import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import feedparser
import logging
from crawl4ai import AsyncWebCrawler
from ..processors.pattern_based_extractor import PatternBasedExtractor
from ..processors.comprehensive_data_aggregator import ComprehensiveDataAggregator
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DailyNewsItem:
    """Structure for daily news items"""
    company_symbol: str
    company_name: str
    title: str
    content: str
    date: str
    source: str
    category: str  # earnings, operational, corporate, acquisition, guidance
    relevance_score: int
    financial_impact: str  # positive, negative, neutral
    key_metrics: Dict[str, Any]
    url: str
    social_mentions: int = 0

class DailyTSXMiningReport:
    def __init__(self):
        self.aggregator = ComprehensiveDataAggregator()
        self.extractor = PatternBasedExtractor()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.report_data = {
            "report_date": self.today,
            "companies_analyzed": 0,
            "high_impact_news": [],
            "market_movers": [],
            "earnings_updates": [],
            "operational_news": [],
            "acquisition_activity": [],
            "commodity_context": {},
            "social_sentiment_leaders": [],
            "insider_activity": [],
            "summary_stats": {}
        }

    async def get_all_tsx_mining_companies(self) -> List[Dict[str, str]]:
        """Get all TSX mining companies from database"""
        
        conn = sqlite3.connect(self.aggregator.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, website, investor_relations_url, news_url, market_cap
            FROM companies 
            WHERE website IS NOT NULL AND website != ''
            ORDER BY market_cap DESC
        ''')
        
        companies = [
            {
                "symbol": row[0],
                "name": row[1],
                "website": row[2],
                "investor_relations_url": row[3],
                "news_url": row[4],
                "market_cap": row[5] or 0
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        logger.info(f"Found {len(companies)} TSX mining companies for analysis")
        return companies

    async def get_todays_stock_movements(self, companies: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """Get today's stock price movements for all companies"""
        
        logger.info("Fetching today's stock movements...")
        
        stock_movements = {}
        symbols = [company["symbol"] for company in companies]
        
        # Batch download for efficiency
        try:
            # Get 2-day data to calculate today's change
            data = yf.download(symbols, period="2d", interval="1d", group_by='ticker', progress=False)
            
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
                            
                            stock_movements[symbol] = {
                                'company_name': company['name'],
                                'current_price': float(today_close),
                                'price_change': float(price_change),
                                'percent_change': float(percent_change),
                                'volume': int(volume),
                                'market_cap': company['market_cap']
                            }
                            
                            logger.debug(f"{symbol}: {percent_change:.2f}% change")
                
                except Exception as e:
                    logger.warning(f"Error processing stock data for {symbol}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching batch stock data: {str(e)}")
        
        logger.info(f"Retrieved stock movements for {len(stock_movements)} companies")
        return stock_movements

    async def scan_company_news_releases(self, companies: List[Dict[str, str]]) -> List[DailyNewsItem]:
        """Scan all company news releases for today's updates"""
        
        logger.info("Scanning company news releases...")
        
        news_items = []
        today_date = datetime.now()
        week_ago = today_date - timedelta(days=7)
        
        async with AsyncWebCrawler(headless=True) as crawler:
            
            for i, company in enumerate(companies):
                logger.info(f"Scanning news for {company['symbol']} ({i+1}/{len(companies)})")
                
                # URLs to check for news
                urls_to_check = []
                
                if company.get('news_url'):
                    urls_to_check.append(('news_page', company['news_url']))
                if company.get('investor_relations_url'):
                    urls_to_check.append(('investor_relations', company['investor_relations_url']))
                if company.get('website'):
                    urls_to_check.append(('main_website', company['website']))
                
                for url_type, url in urls_to_check:
                    try:
                        result = await crawler.arun(url=url, word_count_threshold=200)
                        
                        if result.markdown and len(result.markdown) > 1000:
                            # Extract news items using our enhanced extractor
                            extracted_news = self.extractor.extract_news_items(result.markdown, url)
                            
                            for news_item in extracted_news:
                                # Check if news is recent (within last week)
                                try:
                                    news_date = datetime.strptime(news_item.date, "%Y-%m-%d")
                                    if news_date >= week_ago:
                                        
                                        # Extract financial metrics from content
                                        financial_data = self.extractor.extract_financial_data(news_item.content)
                                        operational_data = self.extractor.extract_operational_data(news_item.content)
                                        
                                        daily_news = DailyNewsItem(
                                            company_symbol=company['symbol'],
                                            company_name=company['name'],
                                            title=news_item.title,
                                            content=news_item.content,
                                            date=news_item.date,
                                            source=url_type,
                                            category=news_item.category,
                                            relevance_score=news_item.relevance_score,
                                            financial_impact=news_item.financial_impact or 'neutral',
                                            key_metrics={
                                                'financial': asdict(financial_data),
                                                'operational': asdict(operational_data)
                                            },
                                            url=url
                                        )
                                        
                                        news_items.append(daily_news)
                                        logger.debug(f"Found recent news for {company['symbol']}: {news_item.title[:50]}...")
                                
                                except ValueError:
                                    # Skip items with invalid dates
                                    continue
                    
                    except Exception as e:
                        logger.warning(f"Error scanning {url_type} for {company['symbol']}: {str(e)}")
                        continue
                
                # Rate limiting
                await asyncio.sleep(1)
                
                # Progress update every 5 companies
                if (i + 1) % 5 == 0:
                    logger.info(f"Progress: {i+1}/{len(companies)} companies scanned, {len(news_items)} news items found")
        
        logger.info(f"Completed news scanning: {len(news_items)} recent news items found")
        return news_items

    async def get_mining_industry_news(self) -> List[Dict[str, Any]]:
        """Get today's mining industry news from external sources"""
        
        logger.info("Fetching mining industry news...")
        
        industry_news = []
        
        # RSS feeds for mining news
        rss_feeds = [
            ('Mining.com', 'https://www.mining.com/feed/'),
            ('Kitco News', 'https://www.kitco.com/rss/KitcoNews.xml'),
            ('Mining Journal', 'https://feeds.feedburner.com/mining-journal'),
        ]
        
        today_date = datetime.now().date()
        
        for source_name, feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    try:
                        # Parse publication date
                        pub_date = datetime(*entry.published_parsed[:6]).date()
                        
                        # Only include today's news
                        if pub_date >= today_date - timedelta(days=1):  # Today and yesterday
                            
                            # Check if mentions any TSX companies
                            content = entry.get('summary', '') + ' ' + entry.get('title', '')
                            tsx_mentions = self.find_tsx_mentions(content)
                            
                            news_item = {
                                'title': entry.get('title', ''),
                                'summary': entry.get('summary', ''),
                                'link': entry.get('link', ''),
                                'published': entry.get('published', ''),
                                'source': source_name,
                                'tsx_companies_mentioned': tsx_mentions,
                                'relevance_score': len(tsx_mentions) * 10 + (20 if 'canada' in content.lower() else 0)
                            }
                            
                            industry_news.append(news_item)
                    
                    except Exception as e:
                        logger.warning(f"Error parsing news entry from {source_name}: {str(e)}")
                        continue
            
            except Exception as e:
                logger.error(f"Error fetching RSS feed {source_name}: {str(e)}")
                continue
        
        # Also scrape Northern Miner for Canadian mining news
        try:
            async with AsyncWebCrawler(headless=True) as crawler:
                result = await crawler.arun(url="https://www.northernminer.com/", word_count_threshold=500)
                
                if result.markdown:
                    northern_miner_news = self.extract_northern_miner_news(result.markdown)
                    industry_news.extend(northern_miner_news)
        
        except Exception as e:
            logger.error(f"Error scraping Northern Miner: {str(e)}")
        
        logger.info(f"Found {len(industry_news)} industry news items")
        return industry_news

    def find_tsx_mentions(self, content: str) -> List[str]:
        """Find TSX company mentions in content"""
        
        # Common TSX mining company symbols and names
        tsx_companies = {
            'ABX.TO': 'Barrick Gold', 'AEM.TO': 'Agnico Eagle', 'K.TO': 'Kinross',
            'FNV.TO': 'Franco-Nevada', 'FM.TO': 'First Quantum', 'LUN.TO': 'Lundin Mining',
            'HBM.TO': 'Hudbay Minerals', 'ELD.TO': 'Eldorado Gold', 'CG.TO': 'Centerra Gold',
            'IMG.TO': 'Iamgold', 'TXG.TO': 'Torex Gold', 'SEA.TO': 'Seabridge Gold',
            'AGI.TO': 'Alamos Gold', 'CXB.TO': 'Calibre Mining', 'MAG.TO': 'MAG Silver',
            'NGD.TO': 'New Gold', 'CNQ.TO': 'Canadian Natural', 'SU.TO': 'Suncor',
            'IMO.TO': 'Imperial Oil', 'CVE.TO': 'Cenovus', 'TOU.TO': 'Tourmaline'
        }
        
        mentions = []
        content_lower = content.lower()
        
        for symbol, company_name in tsx_companies.items():
            if (symbol.lower() in content_lower or 
                company_name.lower() in content_lower or
                symbol.replace('.TO', '').lower() in content_lower):
                mentions.append(symbol)
        
        return list(set(mentions))  # Remove duplicates

    def extract_northern_miner_news(self, content: str) -> List[Dict[str, Any]]:
        """Extract news items from Northern Miner content"""
        
        news_items = []
        
        # Look for article patterns
        article_patterns = [
            r'((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4})[^.]*([^.]*(?:mining|gold|silver|copper|nickel)[^.]*)',
            r'([A-Z][a-zA-Z\s]+(?:mining|mines|gold|resources))[^.]*([^.]{50,200})'
        ]
        
        for pattern in article_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if len(match) == 2:
                    # Find TSX mentions in this article
                    tsx_mentions = self.find_tsx_mentions(match[1])
                    
                    if tsx_mentions:  # Only include if mentions TSX companies
                        news_item = {
                            'title': match[1][:100] + '...',
                            'summary': match[1],
                            'link': 'https://www.northernminer.com/',
                            'published': match[0] if re.match(r'\w+\s+\d+', match[0]) else 'Today',
                            'source': 'Northern Miner',
                            'tsx_companies_mentioned': tsx_mentions,
                            'relevance_score': len(tsx_mentions) * 15
                        }
                        news_items.append(news_item)
        
        return news_items[:10]  # Return top 10 most relevant

    async def get_social_sentiment_snapshot(self, companies: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get social sentiment snapshot for top companies"""
        
        logger.info("Getting social sentiment snapshot...")
        
        sentiment_data = {}
        
        # Focus on top 10 companies by market cap for social analysis
        top_companies = sorted(companies, key=lambda x: x['market_cap'], reverse=True)[:10]
        
        for company in top_companies:
            try:
                sentiment = await self.aggregator.get_reddit_sentiment(company['symbol'], company['name'])
                
                if sentiment and sentiment.get('total_mentions', 0) > 0:
                    sentiment_data[company['symbol']] = {
                        'company_name': company['name'],
                        'total_mentions': sentiment.get('total_mentions', 0),
                        'sentiment': sentiment.get('sentiment_indicators', {}).get('sentiment', 'neutral'),
                        'confidence': sentiment.get('sentiment_indicators', {}).get('confidence', 0)
                    }
            
            except Exception as e:
                logger.warning(f"Error getting sentiment for {company['symbol']}: {str(e)}")
                continue
            
            await asyncio.sleep(1)  # Rate limiting
        
        return sentiment_data

    def analyze_market_movers(self, stock_movements: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify significant market movers"""
        
        movers = []
        
        for symbol, data in stock_movements.items():
            percent_change = abs(data['percent_change'])
            
            # Significant moves: >5% for large caps, >10% for small caps
            market_cap = data['market_cap']
            threshold = 5 if market_cap > 1000000000 else 10  # $1B threshold
            
            if percent_change >= threshold:
                mover_data = {
                    'symbol': symbol,
                    'company_name': data['company_name'],
                    'percent_change': data['percent_change'],
                    'price_change': data['price_change'],
                    'current_price': data['current_price'],
                    'volume': data['volume'],
                    'market_cap': market_cap,
                    'significance': 'major' if percent_change >= threshold * 2 else 'notable'
                }
                movers.append(mover_data)
        
        # Sort by percent change (absolute value)
        movers.sort(key=lambda x: abs(x['percent_change']), reverse=True)
        
        return movers

    def categorize_news_by_type(self, news_items: List[DailyNewsItem]) -> None:
        """Categorize news items by type"""
        
        for news_item in news_items:
            category = news_item.category
            
            if category == 'earnings' or 'earnings' in news_item.title.lower():
                self.report_data['earnings_updates'].append(asdict(news_item))
            elif category == 'operational' or any(word in news_item.title.lower() for word in ['production', 'mining', 'operation']):
                self.report_data['operational_news'].append(asdict(news_item))
            elif category == 'corporate' or any(word in news_item.title.lower() for word in ['acquisition', 'merger', 'takeover']):
                self.report_data['acquisition_activity'].append(asdict(news_item))
            
            # High impact news (relevance score >= 70)
            if news_item.relevance_score >= 70:
                self.report_data['high_impact_news'].append(asdict(news_item))

    async def generate_daily_report(self) -> str:
        """Generate comprehensive daily mining report"""
        
        print("🔍 GENERATING DAILY TSX MINING REPORT")
        print("=" * 50)
        print(f"📅 Report Date: {self.today}")
        print()
        
        try:
            # Step 1: Get all TSX mining companies
            companies = await self.get_all_tsx_mining_companies()
            self.report_data['companies_analyzed'] = len(companies)
            
            # Step 2: Get today's stock movements
            stock_movements = await self.get_todays_stock_movements(companies)
            market_movers = self.analyze_market_movers(stock_movements)
            self.report_data['market_movers'] = market_movers
            
            # Step 3: Scan company news releases
            news_items = await self.scan_company_news_releases(companies)
            self.categorize_news_by_type(news_items)
            
            # Step 4: Get industry news
            industry_news = await self.get_mining_industry_news()
            
            # Step 5: Get social sentiment
            social_sentiment = await self.get_social_sentiment_snapshot(companies)
            self.report_data['social_sentiment_leaders'] = social_sentiment
            
            # Step 6: Get commodity context
            commodity_data = await self.aggregator.get_bank_of_canada_data()
            self.report_data['commodity_context'] = commodity_data
            
            # Generate summary statistics
            self.report_data['summary_stats'] = {
                'total_companies_analyzed': len(companies),
                'companies_with_price_changes': len(stock_movements),
                'significant_movers': len(market_movers),
                'total_news_items': len(news_items),
                'high_impact_news_count': len(self.report_data['high_impact_news']),
                'companies_with_social_mentions': len(social_sentiment),
                'industry_news_items': len(industry_news)
            }
            
            # Generate formatted report
            report = self.format_daily_report(industry_news)
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return f"Error generating report: {str(e)}"

    def format_daily_report(self, industry_news: List[Dict[str, Any]]) -> str:
        """Format the daily report in a readable format"""
        
        report = []
        report.append("📈 DAILY TSX MINING REPORT")
        report.append("=" * 60)
        report.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
        report.append(f"⏰ Generated at {datetime.now().strftime('%H:%M UTC')}")
        report.append("")
        
        # Executive Summary
        report.append("🎯 EXECUTIVE SUMMARY")
        report.append("-" * 20)
        stats = self.report_data['summary_stats']
        report.append(f"• {stats['total_companies_analyzed']} TSX mining companies analyzed")
        report.append(f"• {stats['significant_movers']} significant price movers (>5%)")
        report.append(f"• {stats['high_impact_news_count']} high-impact news items")
        report.append(f"• {stats['industry_news_items']} industry news stories")
        report.append(f"• {stats['companies_with_social_mentions']} companies trending on social media")
        report.append("")
        
        # Market Movers
        if self.report_data['market_movers']:
            report.append("📊 TOP MARKET MOVERS TODAY")
            report.append("-" * 25)
            
            for i, mover in enumerate(self.report_data['market_movers'][:10]):
                direction = "📈" if mover['percent_change'] > 0 else "📉"
                significance = "🔥" if mover['significance'] == 'major' else "⚡"
                
                report.append(f"{i+1}. {significance} {mover['symbol']} - {mover['company_name']}")
                report.append(f"   {direction} {mover['percent_change']:+.2f}% (${mover['current_price']:.2f})")
                report.append(f"   Volume: {mover['volume']:,} shares")
                report.append("")
        
        # High Impact News
        if self.report_data['high_impact_news']:
            report.append("🚨 HIGH-IMPACT NEWS & UPDATES")
            report.append("-" * 30)
            
            for news in self.report_data['high_impact_news'][:5]:
                impact_emoji = "📈" if news['financial_impact'] == 'positive' else "📉" if news['financial_impact'] == 'negative' else "📊"
                
                report.append(f"{impact_emoji} {news['company_symbol']} - {news['company_name']}")
                report.append(f"   📰 {news['title']}")
                report.append(f"   📅 {news['date']} | 🎯 Relevance: {news['relevance_score']}/100")
                report.append(f"   💼 Category: {news['category'].title()}")
                if news['key_metrics']['financial']:
                    financial = news['key_metrics']['financial']
                    metrics = [f"{k}: {v}" for k, v in financial.items() if v is not None]
                    if metrics:
                        report.append(f"   💰 Key metrics: {', '.join(metrics[:3])}")
                report.append("")
        
        # Earnings Updates
        if self.report_data['earnings_updates']:
            report.append("💼 EARNINGS & FINANCIAL UPDATES")
            report.append("-" * 30)
            
            for earnings in self.report_data['earnings_updates'][:5]:
                report.append(f"• {earnings['company_symbol']} - {earnings['title']}")
                report.append(f"  📅 {earnings['date']} | Impact: {earnings['financial_impact']}")
                report.append("")
        
        # Operational News
        if self.report_data['operational_news']:
            report.append("⚙️ OPERATIONAL UPDATES")
            report.append("-" * 20)
            
            for ops in self.report_data['operational_news'][:5]:
                report.append(f"• {ops['company_symbol']} - {ops['title'][:80]}...")
                report.append(f"  📅 {ops['date']}")
                report.append("")
        
        # Industry News
        if industry_news:
            report.append("🌍 MINING INDUSTRY NEWS")
            report.append("-" * 23)
            
            # Filter for high relevance industry news
            relevant_industry_news = [item for item in industry_news if item.get('relevance_score', 0) > 20]
            
            for news in relevant_industry_news[:5]:
                tsx_mentions = news.get('tsx_companies_mentioned', [])
                mentions_str = f" (mentions: {', '.join(tsx_mentions)})" if tsx_mentions else ""
                
                report.append(f"• {news['title']}")
                report.append(f"  🔗 Source: {news['source']}{mentions_str}")
                if news.get('published'):
                    report.append(f"  📅 {news['published']}")
                report.append("")
        
        # Social Sentiment Leaders
        if self.report_data['social_sentiment_leaders']:
            report.append("💬 SOCIAL SENTIMENT LEADERS")
            report.append("-" * 27)
            
            # Sort by mention count
            sorted_sentiment = sorted(
                self.report_data['social_sentiment_leaders'].items(),
                key=lambda x: x[1]['total_mentions'],
                reverse=True
            )
            
            for symbol, sentiment in sorted_sentiment[:5]:
                sentiment_emoji = "😊" if sentiment['sentiment'] == 'positive' else "😞" if sentiment['sentiment'] == 'negative' else "😐"
                
                report.append(f"• {symbol} - {sentiment['company_name']}")
                report.append(f"  {sentiment_emoji} {sentiment['total_mentions']} mentions | Sentiment: {sentiment['sentiment']}")
                report.append(f"  🎯 Confidence: {sentiment['confidence']:.0%}")
                report.append("")
        
        # Commodity Context
        if self.report_data['commodity_context']:
            report.append("🥇 COMMODITY & CURRENCY CONTEXT")
            report.append("-" * 32)
            
            commodity = self.report_data['commodity_context']
            if commodity.get('exchange_rates'):
                exchange = commodity['exchange_rates']
                report.append(f"• USD/CAD Exchange Rate: {exchange.get('usd_cad', 'N/A')}")
                report.append(f"  📅 Date: {exchange.get('date', 'N/A')}")
            
            if commodity.get('commodities'):
                commodities = commodity['commodities']
                if commodities.get('gold_usd'):
                    report.append(f"• Gold Price: ${commodities['gold_usd']} USD")
            report.append("")
        
        # Market Summary
        report.append("📋 MARKET SUMMARY")
        report.append("-" * 16)
        
        if self.report_data['market_movers']:
            avg_change = sum(abs(mover['percent_change']) for mover in self.report_data['market_movers']) / len(self.report_data['market_movers'])
            report.append(f"• Average move for significant movers: {avg_change:.1f}%")
        
        if self.report_data['high_impact_news']:
            report.append(f"• {len(self.report_data['high_impact_news'])} companies had high-impact news")
        
        positive_movers = len([m for m in self.report_data['market_movers'] if m['percent_change'] > 0])
        negative_movers = len([m for m in self.report_data['market_movers'] if m['percent_change'] < 0])
        
        if positive_movers or negative_movers:
            report.append(f"• Market sentiment: {positive_movers} up, {negative_movers} down")
        
        report.append("")
        report.append("📝 Report generated by TSX Mining Intelligence System")
        report.append(f"📊 Data sources: Yahoo Finance, Mining.com, Kitco, Northern Miner, Reddit, Bank of Canada")
        
        return "\n".join(report)

    async def save_daily_report(self, report_text: str) -> tuple[str, str]:
        """Save daily report to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON data
        json_filename = f"daily_tsx_mining_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save formatted text report
        text_filename = f"daily_tsx_mining_report_{timestamp}.txt"
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return json_filename, text_filename

async def main():
    """Generate today's comprehensive TSX mining report"""
    
    reporter = DailyTSXMiningReport()
    
    try:
        # Generate the daily report
        report_text = await reporter.generate_daily_report()
        
        # Save to files
        json_file, text_file = await reporter.save_daily_report(report_text)
        
        # Display the report
        print(report_text)
        
        print("\n" + "="*60)
        print("📁 FILES SAVED:")
        print(f"• Detailed data: {json_file}")
        print(f"• Formatted report: {text_file}")
        print("")
        print("✅ Daily TSX Mining Report completed successfully!")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate daily report: {str(e)}")
        print(f"❌ Report generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Daily mining intelligence report ready for LinkedIn posting!")
    else:
        print("\n💥 Report generation encountered errors.")