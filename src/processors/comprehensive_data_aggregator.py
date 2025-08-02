#!/usr/bin/env python3
"""
Comprehensive TSX Mining Data Aggregator
Integrates multiple free APIs and sources for complete mining company intelligence
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
from ..core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveData:
    """Complete data structure for mining company intelligence"""
    symbol: str
    company_name: str
    extraction_date: str
    
    # Financial Data
    stock_data: Dict[str, Any] = None
    financial_metrics: Dict[str, Any] = None
    analyst_data: Dict[str, Any] = None
    
    # News & Sentiment
    news_items: List[Dict[str, Any]] = None
    social_sentiment: Dict[str, Any] = None
    regulatory_filings: List[Dict[str, Any]] = None
    
    # Mining-Specific
    commodity_prices: Dict[str, Any] = None
    production_data: Dict[str, Any] = None
    insider_trading: List[Dict[str, Any]] = None
    
    # External Sources
    reddit_mentions: List[Dict[str, Any]] = None
    twitter_sentiment: Dict[str, Any] = None
    
    relevance_score: int = 0

class ComprehensiveDataAggregator:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        
        # API configurations (add your keys to config.py or environment variables)
        self.api_keys = {
            'alpha_vantage': 'YOUR_ALPHA_VANTAGE_KEY',  # Free 500 requests/day
            'polygon': 'YOUR_POLYGON_KEY',  # Free 5 calls/minute
            'fmp': 'YOUR_FMP_KEY',  # Free 250 requests/day
            'reddit_client_id': 'YOUR_REDDIT_CLIENT_ID',
            'reddit_client_secret': 'YOUR_REDDIT_CLIENT_SECRET'
        }
        
        # Free data sources
        self.free_sources = {
            'bank_of_canada': 'https://www.bankofcanada.ca/valet/',
            'tmx_market': 'https://www.tmx.com/',
            'sedar_plus': 'https://www.sedarplus.ca/csa-acvm/',
            'mining_rss': 'https://www.mining.com/feed/',
            'natural_resources_canada': 'https://www.nrcan.gc.ca/'
        }

    async def get_yahoo_finance_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive data from Yahoo Finance using yfinance"""
        
        logger.info(f"Fetching Yahoo Finance data for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period="5d")
            
            # Get financial statements
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
            
            # Get recommendations (handle potential errors)
            try:
                recommendations = ticker.recommendations
            except:
                recommendations = None
            
            # Get insider purchases (handle potential errors)  
            try:
                insider_purchases = ticker.insider_purchases
            except:
                insider_purchases = None
            
            yahoo_data = {
                'basic_info': {
                    'market_cap': info.get('marketCap'),
                    'enterprise_value': info.get('enterpriseValue'),
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'peg_ratio': info.get('pegRatio'),
                    'dividend_yield': info.get('dividendYield'),
                    'beta': info.get('beta'),
                    'current_price': info.get('currentPrice'),
                    '52_week_high': info.get('fiftyTwoWeekHigh'),
                    '52_week_low': info.get('fiftyTwoWeekLow')
                },
                'recent_performance': {
                    'latest_close': float(hist['Close'].iloc[-1]) if not hist.empty else None,
                    'volume': int(hist['Volume'].iloc[-1]) if not hist.empty else None,
                    '5_day_change': float((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100) if len(hist) >= 2 else None
                },
                'financial_statements': {
                    'has_financials': not financials.empty,
                    'has_balance_sheet': not balance_sheet.empty,
                    'has_cash_flow': not cash_flow.empty,
                    'latest_revenue': float(financials.loc['Total Revenue'].iloc[0]) if 'Total Revenue' in financials.index and not financials.empty else None,
                    'latest_net_income': float(financials.loc['Net Income'].iloc[0]) if 'Net Income' in financials.index and not financials.empty else None
                },
                'analyst_data': {
                    'recommendation': recommendations.iloc[-1].get('To Grade') if recommendations is not None and not recommendations.empty and len(recommendations) > 0 else None,
                    'target_price': info.get('targetMeanPrice'),
                    'analyst_count': info.get('numberOfAnalystOpinions')
                },
                'insider_activity': {
                    'recent_purchases': len(insider_purchases) if insider_purchases is not None else 0,
                    'insider_ownership': info.get('heldPercentInsiders')
                }
            }
            
            return yahoo_data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {str(e)}")
            return {}

    async def get_alpha_vantage_data(self, symbol: str) -> Dict[str, Any]:
        """Get data from Alpha Vantage API"""
        
        if self.api_keys['alpha_vantage'] == 'YOUR_ALPHA_VANTAGE_KEY':
            logger.warning("Alpha Vantage API key not configured")
            return {}
        
        logger.info(f"Fetching Alpha Vantage data for {symbol}")
        
        try:
            # Company overview
            overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.api_keys['alpha_vantage']}"
            overview_response = requests.get(overview_url, timeout=10)
            overview_data = overview_response.json()
            
            # Daily time series
            daily_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_keys['alpha_vantage']}"
            daily_response = requests.get(daily_url, timeout=10)
            daily_data = daily_response.json()
            
            # News sentiment
            news_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={self.api_keys['alpha_vantage']}"
            news_response = requests.get(news_url, timeout=10)
            news_data = news_response.json()
            
            return {
                'company_overview': overview_data,
                'daily_prices': daily_data.get('Time Series (Daily)', {}),
                'news_sentiment': news_data.get('feed', [])
            }
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
            return {}

    async def get_bank_of_canada_data(self) -> Dict[str, Any]:
        """Get commodity prices and exchange rates from Bank of Canada"""
        
        logger.info("Fetching Bank of Canada commodity data")
        
        try:
            # Exchange rates
            usd_cad_url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=1"
            usd_response = requests.get(usd_cad_url, timeout=10)
            usd_data = usd_response.json()
            
            # Commodity prices (if available)
            commodity_data = {}
            
            # Gold price (London PM fix in USD)
            try:
                gold_url = "https://www.bankofcanada.ca/valet/observations/V39079/json?recent=1"
                gold_response = requests.get(gold_url, timeout=10)
                gold_data = gold_response.json()
                commodity_data['gold_usd'] = gold_data['observations'][0]['V39079']['v'] if gold_data.get('observations') else None
            except:
                pass
            
            return {
                'exchange_rates': {
                    'usd_cad': usd_data['observations'][0]['FXUSDCAD']['v'] if usd_data.get('observations') else None,
                    'date': usd_data['observations'][0]['d'] if usd_data.get('observations') else None
                },
                'commodities': commodity_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching Bank of Canada data: {str(e)}")
            return {}

    async def get_mining_news_rss(self) -> List[Dict[str, Any]]:
        """Get mining industry news from RSS feeds"""
        
        logger.info("Fetching mining industry RSS feeds")
        
        news_items = []
        
        rss_feeds = [
            'https://www.mining.com/feed/',
            'https://www.kitco.com/rss/KitcoNews.xml',
            'https://feeds.feedburner.com/mining-journal',
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Latest 10 items per feed
                    news_item = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', ''),
                        'source': feed_url,
                        'tags': [tag.get('term', '') for tag in entry.get('tags', [])],
                    }
                    news_items.append(news_item)
                    
            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
        
        return news_items

    async def get_reddit_sentiment(self, symbol: str, company_name: str) -> Dict[str, Any]:
        """Get Reddit sentiment and mentions"""
        
        if not self.api_keys['reddit_client_id'] or self.api_keys['reddit_client_id'] == 'YOUR_REDDIT_CLIENT_ID':
            logger.info("Reddit API credentials not configured, using web scraping fallback")
            return await self.scrape_reddit_mentions(symbol, company_name)
        
        logger.info(f"Fetching Reddit sentiment for {symbol}")
        
        try:
            import praw
            
            reddit = praw.Reddit(
                client_id=self.api_keys['reddit_client_id'],
                client_secret=self.api_keys['reddit_client_secret'],
                user_agent='TSX Mining Tracker v1.0'
            )
            
            # Search multiple subreddits
            subreddits = ['CanadianInvestor', 'SecurityAnalysis', 'investing', 'stocks', 'mining']
            mentions = []
            
            for subreddit_name in subreddits:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Search for company mentions
                for submission in subreddit.search(f"{symbol} OR {company_name}", time_filter="month", limit=20):
                    mention = {
                        'title': submission.title,
                        'score': submission.score,
                        'num_comments': submission.num_comments,
                        'created_utc': submission.created_utc,
                        'url': submission.url,
                        'subreddit': subreddit_name,
                        'selftext': submission.selftext[:500]  # First 500 chars
                    }
                    mentions.append(mention)
            
            return {
                'total_mentions': len(mentions),
                'recent_mentions': mentions,
                'average_score': sum(m['score'] for m in mentions) / len(mentions) if mentions else 0,
                'subreddits_found': list(set(m['subreddit'] for m in mentions))
            }
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data for {symbol}: {str(e)}")
            return {}

    async def scrape_reddit_mentions(self, symbol: str, company_name: str) -> Dict[str, Any]:
        """Fallback: scrape Reddit mentions without API"""
        
        logger.info(f"Scraping Reddit mentions for {symbol}")
        
        async with AsyncWebCrawler(headless=True) as crawler:
            mentions = []
            
            # Search URLs for different subreddits
            search_urls = [
                f"https://www.reddit.com/r/CanadianInvestor/search/?q={symbol}&restrict_sr=1&sort=new&t=month",
                f"https://www.reddit.com/r/investing/search/?q={symbol}&restrict_sr=1&sort=new&t=month",
                f"https://www.reddit.com/search/?q={company_name}&t=month"
            ]
            
            for url in search_urls:
                try:
                    result = await crawler.arun(url=url, word_count_threshold=100)
                    
                    if result.markdown:
                        # Extract post information
                        posts = self.extract_reddit_posts(result.markdown, symbol, company_name)
                        mentions.extend(posts)
                        
                except Exception as e:
                    logger.error(f"Error scraping Reddit URL {url}: {str(e)}")
                
                await asyncio.sleep(2)  # Rate limiting
            
            return {
                'total_mentions': len(mentions),
                'recent_mentions': mentions[:20],  # Top 20 most recent
                'sentiment_indicators': self.analyze_reddit_sentiment(mentions)
            }

    def extract_reddit_posts(self, content: str, symbol: str, company_name: str) -> List[Dict[str, Any]]:
        """Extract Reddit posts from scraped content"""
        
        posts = []
        
        # Look for post patterns
        import re
        
        # Pattern for Reddit post titles and scores
        post_patterns = [
            r'(\d+)\s*points?[^r]*r/([a-zA-Z]+)[^•]*•[^•]*•([^¶]*)',
            r'([^¶]*(?:' + re.escape(symbol) + '|' + re.escape(company_name.lower()) + ')[^¶]*)'
        ]
        
        for pattern in post_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 3:
                    post = {
                        'score': match[0],
                        'subreddit': match[1],
                        'title': match[2][:200],
                        'relevance': 1 if symbol.lower() in match[2].lower() else 0.5
                    }
                    posts.append(post)
                elif isinstance(match, str) and (symbol.lower() in match.lower() or company_name.lower() in match.lower()):
                    post = {
                        'score': 'unknown',
                        'subreddit': 'unknown', 
                        'title': match[:200],
                        'relevance': 1 if symbol.lower() in match.lower() else 0.5
                    }
                    posts.append(post)
        
        return posts[:10]  # Return top 10 matches

    def analyze_reddit_sentiment(self, mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment from Reddit mentions"""
        
        if not mentions:
            return {}
        
        positive_words = ['bullish', 'buy', 'strong', 'good', 'great', 'excellent', 'positive', 'up', 'moon']
        negative_words = ['bearish', 'sell', 'weak', 'bad', 'terrible', 'negative', 'down', 'crash', 'dump']
        
        positive_score = 0
        negative_score = 0
        
        for mention in mentions:
            title_lower = mention.get('title', '').lower()
            
            for word in positive_words:
                if word in title_lower:
                    positive_score += 1
            
            for word in negative_words:
                if word in title_lower:
                    negative_score += 1
        
        total_score = positive_score + negative_score
        sentiment = 'neutral'
        
        if total_score > 0:
            if positive_score > negative_score * 1.2:
                sentiment = 'positive'
            elif negative_score > positive_score * 1.2:
                sentiment = 'negative'
        
        return {
            'sentiment': sentiment,
            'positive_mentions': positive_score,
            'negative_mentions': negative_score,
            'confidence': min(total_score / max(len(mentions), 1), 1.0)
        }

    async def get_tmx_insider_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get insider trading data from TMX"""
        
        logger.info(f"Fetching TMX insider data for {symbol}")
        
        # Clean symbol for TMX (remove .TO suffix)
        clean_symbol = symbol.replace('.TO', '').replace('.V', '')
        
        async with AsyncWebCrawler(headless=True) as crawler:
            try:
                # TMX insider trading URL
                url = f"https://www.tmx.com/quote/{clean_symbol}?locale=en#insider"
                
                result = await crawler.arun(url=url, word_count_threshold=100)
                
                if result.markdown:
                    insider_data = self.parse_insider_trading(result.markdown)
                    return insider_data
                
            except Exception as e:
                logger.error(f"Error fetching TMX insider data for {symbol}: {str(e)}")
        
        return []

    def parse_insider_trading(self, content: str) -> List[Dict[str, Any]]:
        """Parse insider trading information from TMX content"""
        
        insider_trades = []
        
        # Look for insider trading patterns
        import re
        
        # Pattern for insider transactions
        trade_patterns = [
            r'(\w+\s+\w+)\s+(Buy|Sell|Exercise)\s+([0-9,]+)\s+\$([0-9,.]+)',
            r'(Director|Officer|Insider)[^$]*\$([0-9,.]+)'
        ]
        
        for pattern in trade_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if len(match) == 4:
                    trade = {
                        'insider_name': match[0],
                        'transaction_type': match[1],
                        'shares': match[2].replace(',', ''),
                        'value': match[3].replace(',', '')
                    }
                    insider_trades.append(trade)
                elif len(match) == 2:
                    trade = {
                        'insider_type': match[0],
                        'transaction_value': match[1]
                    }
                    insider_trades.append(trade)
        
        return insider_trades

    async def aggregate_company_data(self, symbol: str, company_name: str) -> ComprehensiveData:
        """Aggregate all available data for a company"""
        
        logger.info(f"Starting comprehensive data aggregation for {symbol} - {company_name}")
        
        # Initialize comprehensive data structure
        comprehensive_data = ComprehensiveData(
            symbol=symbol,
            company_name=company_name,
            extraction_date=datetime.now().isoformat()
        )
        
        try:
            # Collect data from all sources in parallel
            tasks = [
                self.get_yahoo_finance_data(symbol),
                self.get_alpha_vantage_data(symbol),
                self.get_bank_of_canada_data(),
                self.get_mining_news_rss(),
                self.get_reddit_sentiment(symbol, company_name),
                self.get_tmx_insider_data(symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            comprehensive_data.stock_data = results[0] if not isinstance(results[0], Exception) else {}
            comprehensive_data.financial_metrics = results[1] if not isinstance(results[1], Exception) else {}
            comprehensive_data.commodity_prices = results[2] if not isinstance(results[2], Exception) else {}
            comprehensive_data.news_items = results[3] if not isinstance(results[3], Exception) else []
            comprehensive_data.social_sentiment = results[4] if not isinstance(results[4], Exception) else {}
            comprehensive_data.insider_trading = results[5] if not isinstance(results[5], Exception) else []
            
            # Calculate relevance score
            comprehensive_data.relevance_score = self.calculate_comprehensive_relevance(comprehensive_data)
            
            logger.info(f"Completed data aggregation for {symbol} - Relevance Score: {comprehensive_data.relevance_score}")
            
        except Exception as e:
            logger.error(f"Error aggregating data for {symbol}: {str(e)}")
        
        return comprehensive_data

    def calculate_comprehensive_relevance(self, data: ComprehensiveData) -> int:
        """Calculate comprehensive relevance score"""
        
        score = 0
        
        # Stock data relevance
        if data.stock_data and data.stock_data.get('basic_info'):
            basic_info = data.stock_data['basic_info']
            if basic_info.get('current_price'):
                score += 20
            if basic_info.get('pe_ratio'):
                score += 15
            if basic_info.get('dividend_yield'):
                score += 10
        
        # Recent performance
        if data.stock_data and data.stock_data.get('recent_performance'):
            perf = data.stock_data['recent_performance']
            if perf.get('5_day_change'):
                change = abs(perf['5_day_change'])
                if change > 5:  # >5% change is significant
                    score += 25
                elif change > 2:  # >2% change is notable
                    score += 15
        
        # News relevance
        if data.news_items:
            score += min(len(data.news_items) * 5, 30)  # Max 30 points for news
        
        # Social sentiment
        if data.social_sentiment:
            mentions = data.social_sentiment.get('total_mentions', 0)
            score += min(mentions * 2, 20)  # Max 20 points for social
        
        # Insider trading
        if data.insider_trading:
            score += len(data.insider_trading) * 5  # 5 points per insider trade
        
        return min(score, 100)  # Cap at 100

    async def process_all_companies(self, limit: int = None) -> List[ComprehensiveData]:
        """Process all companies in database"""
        
        # Get companies from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT symbol, name 
            FROM companies 
            WHERE website IS NOT NULL AND website != ''
            ORDER BY market_cap DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query)
        companies = cursor.fetchall()
        conn.close()
        
        logger.info(f"Processing {len(companies)} companies for comprehensive data aggregation")
        
        results = []
        
        for symbol, company_name in companies:
            try:
                logger.info(f"Processing {symbol} - {company_name}")
                
                comprehensive_data = await self.aggregate_company_data(symbol, company_name)
                results.append(comprehensive_data)
                
                # Rate limiting between companies
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {str(e)}")
        
        return results

    def save_comprehensive_data(self, results: List[ComprehensiveData]) -> str:
        """Save comprehensive data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_mining_data_{timestamp}.json"
        
        # Convert dataclasses to dictionaries
        data_for_json = []
        for result in results:
            data_dict = asdict(result)
            data_for_json.append(data_dict)
        
        # Save to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_for_json, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Comprehensive data saved to {filename}")
        return filename

    def generate_summary_report(self, results: List[ComprehensiveData]) -> str:
        """Generate comprehensive summary report"""
        
        if not results:
            return "No data to report."
        
        report = []
        report.append("COMPREHENSIVE TSX MINING DATA AGGREGATION REPORT")
        report.append("=" * 65)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Companies processed: {len(results)}")
        report.append("")
        
        # Top companies by relevance
        sorted_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
        
        report.append("TOP COMPANIES BY RELEVANCE:")
        report.append("-" * 30)
        
        for i, company in enumerate(sorted_results[:10]):
            report.append(f"{i+1}. {company.symbol} - {company.company_name}")
            report.append(f"   Relevance Score: {company.relevance_score}")
            
            # Show key metrics
            if company.stock_data and company.stock_data.get('basic_info'):
                basic = company.stock_data['basic_info']
                price = basic.get('current_price', 'N/A')
                pe = basic.get('pe_ratio', 'N/A')
                report.append(f"   Price: ${price}, P/E: {pe}")
            
            if company.social_sentiment:
                mentions = company.social_sentiment.get('total_mentions', 0)
                sentiment = company.social_sentiment.get('sentiment_indicators', {}).get('sentiment', 'neutral')
                report.append(f"   Social: {mentions} mentions, {sentiment} sentiment")
            
            report.append("")
        
        # Data source statistics
        report.append("DATA SOURCE STATISTICS:")
        report.append("-" * 25)
        
        companies_with_stock_data = sum(1 for r in results if r.stock_data)
        companies_with_news = sum(1 for r in results if r.news_items)
        companies_with_social = sum(1 for r in results if r.social_sentiment and r.social_sentiment.get('total_mentions', 0) > 0)
        companies_with_insider = sum(1 for r in results if r.insider_trading)
        
        report.append(f"• Companies with stock data: {companies_with_stock_data}/{len(results)}")
        report.append(f"• Companies with recent news: {companies_with_news}/{len(results)}")
        report.append(f"• Companies with social mentions: {companies_with_social}/{len(results)}")
        report.append(f"• Companies with insider trading: {companies_with_insider}/{len(results)}")
        report.append("")
        
        # High-impact recent events
        high_impact_companies = [r for r in results if r.relevance_score >= 70]
        
        if high_impact_companies:
            report.append("HIGH-IMPACT COMPANIES (Score ≥ 70):")
            report.append("-" * 35)
            
            for company in high_impact_companies:
                report.append(f"• {company.symbol}: {company.relevance_score} points")
                
                # Show what makes them high-impact
                factors = []
                if company.stock_data and company.stock_data.get('recent_performance'):
                    change = company.stock_data['recent_performance'].get('5_day_change')
                    if change and abs(change) > 5:
                        factors.append(f"{change:.1f}% price change")
                
                if company.news_items and len(company.news_items) > 5:
                    factors.append(f"{len(company.news_items)} recent news items")
                
                if company.social_sentiment and company.social_sentiment.get('total_mentions', 0) > 10:
                    factors.append(f"{company.social_sentiment['total_mentions']} social mentions")
                
                if factors:
                    report.append(f"  Factors: {', '.join(factors)}")
                
                report.append("")
        
        return "\n".join(report)

async def main():
    """Main execution function"""
    
    print("🚀 COMPREHENSIVE TSX MINING DATA AGGREGATION")
    print("=" * 60)
    
    aggregator = ComprehensiveDataAggregator()
    
    try:
        # Process a limited number of companies for testing
        results = await aggregator.process_all_companies(limit=3)
        
        if results:
            # Save results
            filename = aggregator.save_comprehensive_data(results)
            
            # Generate report
            report = aggregator.generate_summary_report(results)
            
            # Save report
            report_filename = filename.replace('.json', '_report.txt')
            with open(report_filename, 'w') as f:
                f.write(report)
            
            print(report)
            print(f"\nFiles saved:")
            print(f"• Comprehensive data: {filename}")
            print(f"• Summary report: {report_filename}")
            
            return True
        
        else:
            print("No data collected!")
            return False
    
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Install required packages
    try:
        import feedparser
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'feedparser', 'praw'])
    
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Comprehensive data aggregation completed successfully!")
    else:
        print("\n❌ Comprehensive data aggregation failed!")