#!/usr/bin/env python3
"""
Comprehensive Business Intelligence Scanner
Focuses on guidance, production, insider activity, trade data, and Canadian economics
"""

import asyncio
import json
import requests
import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
import feedparser
import logging
from crawl4ai import AsyncWebCrawler
import re
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveBusinessIntel:
    def __init__(self):
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.db_path = "mining_companies.db"
        self.report_data = {
            "guidance_updates": [],
            "production_reports": [],
            "insider_activity": [],
            "trade_data": {},
            "canadian_economics": {},
            "earnings_calendar": [],
            "analyst_revisions": []
        }

    async def scan_guidance_updates(self) -> List[Dict[str, Any]]:
        """Scan for recent guidance updates from TSX mining companies"""
        
        logger.info("Scanning for guidance updates...")
        
        guidance_updates = []
        
        # Get top companies
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, name, investor_relations_url, news_url
            FROM companies 
            WHERE market_cap > 1000000000  -- Focus on companies > $1B market cap
            ORDER BY market_cap DESC
            LIMIT 10
        ''')
        companies = cursor.fetchall()
        conn.close()
        
        # Guidance keywords to look for
        guidance_keywords = [
            'guidance', 'outlook', 'forecast', 'expects', 'anticipates',
            'projects', 'targets', 'revised', 'updated', 'reaffirms',
            'raises', 'lowers', 'maintains', 'full year', 'fy 2025',
            'production guidance', 'cost guidance', 'capex guidance'
        ]
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for symbol, name, ir_url, news_url in companies:
                logger.info(f"Checking guidance for {symbol}...")
                
                urls_to_check = [url for url in [ir_url, news_url] if url]
                
                for url in urls_to_check:
                    try:
                        result = await crawler.arun(url=url, word_count_threshold=500)
                        
                        if result.markdown:
                            content = result.markdown.lower()
                            
                            # Look for guidance-related content
                            for keyword in guidance_keywords:
                                if keyword in content:
                                    # Extract surrounding context
                                    guidance_context = self.extract_guidance_context(content, keyword)
                                    
                                    if guidance_context:
                                        guidance_updates.append({
                                            'company_symbol': symbol,
                                            'company_name': name,
                                            'keyword_found': keyword,
                                            'context': guidance_context,
                                            'source_url': url,
                                            'extracted_date': self.today,
                                            'financial_figures': self.extract_financial_figures(guidance_context)
                                        })
                                        break  # Found guidance, move to next company
                    
                    except Exception as e:
                        logger.warning(f"Error checking guidance for {symbol}: {str(e)}")
                        continue
                
                await asyncio.sleep(1)  # Rate limiting
        
        return guidance_updates

    def extract_guidance_context(self, content: str, keyword: str) -> str:
        """Extract context around guidance keywords"""
        
        # Find the keyword and extract surrounding sentences
        keyword_index = content.find(keyword)
        if keyword_index == -1:
            return ""
        
        # Get ~200 characters before and after the keyword
        start = max(0, keyword_index - 200)
        end = min(len(content), keyword_index + 200)
        
        context = content[start:end].strip()
        
        # Clean up the context
        sentences = context.split('.')
        if len(sentences) >= 3:
            # Return the middle sentences that likely contain the guidance
            return '. '.join(sentences[1:-1]).strip()
        
        return context

    def extract_financial_figures(self, text: str) -> List[str]:
        """Extract financial figures from guidance text"""
        
        # Patterns for financial figures
        patterns = [
            r'\$[\d,]+(?:\.\d+)?\s*(?:million|billion|M|B)',
            r'[\d,]+(?:\.\d+)?\s*(?:million|billion|M|B)\s*(?:tonnes|tons|ounces|oz)',
            r'[\d,]+(?:\.\d+)?%',
            r'[\d,]+(?:\.\d+)?\s*(?:to|-)?\s*[\d,]+(?:\.\d+)?\s*(?:million|billion|M|B)'
        ]
        
        figures = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            figures.extend(matches)
        
        return figures

    async def scan_production_reports(self) -> List[Dict[str, Any]]:
        """Scan for recent production reports and operational updates"""
        
        logger.info("Scanning for production reports...")
        
        production_reports = []
        
        # Production-related keywords
        production_keywords = [
            'production', 'produced', 'output', 'mining', 'processed',
            'recovery', 'grade', 'tonnage', 'mill', 'plant', 'operations',
            'quarterly production', 'monthly production', 'annual production',
            'record production', 'production update'
        ]
        
        # Get mining news from industry sources
        industry_sources = [
            'https://www.mining.com/feed/',
            'https://www.kitco.com/rss/KitcoNews.xml'
        ]
        
        # Scan RSS feeds for production news
        for feed_url in industry_sources:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Latest 10 items
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()
                    content = title + ' ' + summary
                    
                    # Check for production keywords
                    production_mentions = [kw for kw in production_keywords if kw in content]
                    
                    if production_mentions:
                        # Check for TSX company mentions
                        tsx_mentions = self.find_tsx_company_mentions(content)
                        
                        if tsx_mentions:
                            production_reports.append({
                                'title': entry.get('title', ''),
                                'summary': entry.get('summary', ''),
                                'published': entry.get('published', ''),
                                'link': entry.get('link', ''),
                                'production_keywords': production_mentions,
                                'tsx_companies': tsx_mentions,
                                'source': feed_url,
                                'production_figures': self.extract_production_figures(content)
                            })
            
            except Exception as e:
                logger.warning(f"Error scanning production from {feed_url}: {str(e)}")
        
        return production_reports

    def extract_production_figures(self, text: str) -> List[str]:
        """Extract production figures from text"""
        
        patterns = [
            r'[\d,]+(?:\.\d+)?\s*(?:tonnes|tons|ounces|oz|pounds|lbs)',
            r'[\d,]+(?:\.\d+)?\s*(?:g/t|oz/t)',
            r'[\d,]+(?:\.\d+)?%\s*(?:recovery|grade)',
            r'[\d,]+(?:\.\d+)?\s*(?:tpd|tonne.*day|ton.*day)'
        ]
        
        figures = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            figures.extend(matches)
        
        return figures

    def find_tsx_company_mentions(self, content: str) -> List[str]:
        """Find TSX company mentions in content"""
        
        companies = [
            'barrick', 'agnico eagle', 'kinross', 'franco-nevada', 'first quantum',
            'lundin mining', 'hudbay', 'eldorado', 'iamgold', 'newmont',
            'canadian natural', 'suncor', 'imperial oil', 'cenovus'
        ]
        
        mentions = []
        for company in companies:
            if company in content:
                mentions.append(company)
        
        return mentions

    async def get_insider_activity(self) -> List[Dict[str, Any]]:
        """Get recent insider trading activity"""
        
        logger.info("Scanning insider activity...")
        
        insider_activity = []
        
        # Get top 10 companies
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, name FROM companies 
            ORDER BY market_cap DESC LIMIT 10
        ''')
        companies = cursor.fetchall()
        conn.close()
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for symbol, name in companies:
                try:
                    # Canadian Insider website for insider trading
                    clean_symbol = symbol.replace('.TO', '').replace('.V', '')
                    insider_url = f"https://www.canadianinsider.com/company?ticker={clean_symbol}"
                    
                    result = await crawler.arun(url=insider_url, word_count_threshold=100)
                    
                    if result.markdown:
                        insider_data = self.parse_insider_data(result.markdown, symbol, name)
                        if insider_data:
                            insider_activity.extend(insider_data)
                
                except Exception as e:
                    logger.warning(f"Error getting insider data for {symbol}: {str(e)}")
                    continue
                
                await asyncio.sleep(2)  # Rate limiting
        
        return insider_activity

    def parse_insider_data(self, content: str, symbol: str, company_name: str) -> List[Dict[str, Any]]:
        """Parse insider trading data from content"""
        
        insider_transactions = []
        
        # Look for insider transaction patterns
        patterns = [
            r'((?:Buy|Sell|Exercise))\s+([0-9,]+)\s+.*?\$([0-9,.]+)',
            r'(Director|Officer|CEO|CFO|President).*?(Buy|Sell).*?([0-9,]+).*?\$([0-9,.]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if len(match) >= 3:
                    insider_transactions.append({
                        'company_symbol': symbol,
                        'company_name': company_name,
                        'transaction_type': match[0] if 'buy' in match[0].lower() or 'sell' in match[0].lower() else match[1],
                        'shares': match[1] if len(match) == 3 else match[2],
                        'value': match[2] if len(match) == 3 else match[3],
                        'insider_type': match[0] if len(match) == 4 else 'Unknown',
                        'extracted_date': self.today
                    })
        
        return insider_transactions

    def get_canadian_trade_data(self) -> Dict[str, Any]:
        """Get Canadian mining trade data"""
        
        logger.info("Fetching Canadian trade data...")
        
        trade_data = {}
        
        try:
            # Statistics Canada API for trade data
            # Note: This is a simplified example - real implementation would need proper API access
            
            # For now, get exchange rate and basic economic indicators
            usd_cad_url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=5"
            response = requests.get(usd_cad_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('observations'):
                    trade_data['exchange_rates'] = {
                        'current_usd_cad': data['observations'][-1]['FXUSDCAD']['v'],
                        'previous_week': data['observations'][0]['FXUSDCAD']['v'] if len(data['observations']) > 4 else None,
                        'trend': 'strengthening' if float(data['observations'][-1]['FXUSDCAD']['v']) < float(data['observations'][0]['FXUSDCAD']['v']) else 'weakening'
                    }
        
        except Exception as e:
            logger.warning(f"Error fetching trade data: {str(e)}")
        
        # Add commodity export context
        try:
            # Get gold prices for export context
            gold = yf.Ticker("GC=F")
            gold_history = gold.history(period="5d")
            
            if not gold_history.empty:
                current_gold = gold_history['Close'].iloc[-1]
                week_ago_gold = gold_history['Close'].iloc[0] if len(gold_history) > 4 else current_gold
                
                trade_data['commodity_exports'] = {
                    'gold_price_usd': float(current_gold),
                    'gold_weekly_change': float((current_gold - week_ago_gold) / week_ago_gold * 100),
                    'export_competitiveness': 'favorable' if trade_data.get('exchange_rates', {}).get('trend') == 'weakening' else 'neutral'
                }
        
        except Exception as e:
            logger.warning(f"Error fetching commodity data: {str(e)}")
        
        return trade_data

    def get_canadian_economic_indicators(self) -> Dict[str, Any]:
        """Get key Canadian economic indicators affecting mining"""
        
        logger.info("Fetching Canadian economic indicators...")
        
        indicators = {}
        
        try:
            # Bank of Canada key interest rate
            interest_rate_url = "https://www.bankofcanada.ca/valet/observations/V122530/json?recent=1"
            response = requests.get(interest_rate_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('observations'):
                    indicators['bank_of_canada_rate'] = {
                        'current_rate': data['observations'][0]['V122530']['v'],
                        'date': data['observations'][0]['d']
                    }
        
        except Exception as e:
            logger.warning(f"Error fetching BoC rate: {str(e)}")
        
        try:
            # TSX Composite Index for market context
            tsx = yf.Ticker("^GSPTSE")
            tsx_data = tsx.history(period="5d")
            
            if not tsx_data.empty:
                current_tsx = tsx_data['Close'].iloc[-1]
                week_ago_tsx = tsx_data['Close'].iloc[0] if len(tsx_data) > 4 else current_tsx
                
                indicators['tsx_composite'] = {
                    'current_level': float(current_tsx),
                    'weekly_change_percent': float((current_tsx - week_ago_tsx) / week_ago_tsx * 100),
                    'trend': 'bullish' if current_tsx > week_ago_tsx else 'bearish'
                }
        
        except Exception as e:
            logger.warning(f"Error fetching TSX data: {str(e)}")
        
        return indicators

    async def get_earnings_calendar(self) -> List[Dict[str, Any]]:
        """Get upcoming earnings calendar for TSX mining companies"""
        
        logger.info("Fetching earnings calendar...")
        
        earnings_calendar = []
        
        # Get our companies
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, name FROM companies ORDER BY market_cap DESC LIMIT 15')
        companies = cursor.fetchall()
        conn.close()
        
        for symbol, name in companies:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get basic info which sometimes includes earnings date
                info = ticker.info
                
                if info and 'earningsDate' in info:
                    earnings_date = info['earningsDate']
                    if earnings_date:
                        # Convert timestamp to date
                        earnings_calendar.append({
                            'company_symbol': symbol,
                            'company_name': name,
                            'earnings_date': str(earnings_date),
                            'next_earnings': 'upcoming' if earnings_date > datetime.now() else 'recent'
                        })
            
            except Exception as e:
                logger.warning(f"Error getting earnings calendar for {symbol}: {str(e)}")
                continue
        
        return earnings_calendar

    async def generate_comprehensive_intel_report(self) -> str:
        """Generate comprehensive business intelligence report"""
        
        logger.info("Generating comprehensive business intelligence report...")
        
        try:
            # Gather all intelligence
            self.report_data['guidance_updates'] = await self.scan_guidance_updates()
            self.report_data['production_reports'] = await self.scan_production_reports()
            self.report_data['insider_activity'] = await self.get_insider_activity()
            self.report_data['trade_data'] = self.get_canadian_trade_data()
            self.report_data['canadian_economics'] = self.get_canadian_economic_indicators()
            self.report_data['earnings_calendar'] = await self.get_earnings_calendar()
            
            # Generate formatted report
            report = self.format_intel_report()
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating intel report: {str(e)}")
            return f"Error generating report: {str(e)}"

    def format_intel_report(self) -> str:
        """Format the business intelligence report"""
        
        report = []
        report.append("🔍 COMPREHENSIVE TSX MINING BUSINESS INTELLIGENCE")
        report.append("=" * 65)
        report.append(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
        report.append(f"⏰ Generated at {datetime.now().strftime('%H:%M UTC')}")
        report.append("")
        
        # Guidance Updates
        if self.report_data['guidance_updates']:
            report.append("📊 GUIDANCE UPDATES & OUTLOOK")
            report.append("-" * 30)
            
            for guidance in self.report_data['guidance_updates'][:5]:
                report.append(f"🎯 {guidance['company_symbol']} - {guidance['company_name']}")
                report.append(f"   Keyword: {guidance['keyword_found']}")
                report.append(f"   Context: {guidance['context'][:150]}...")
                if guidance['financial_figures']:
                    report.append(f"   Figures: {', '.join(guidance['financial_figures'][:3])}")
                report.append("")
        
        # Production Reports
        if self.report_data['production_reports']:
            report.append("⚙️ PRODUCTION REPORTS & OPERATIONAL UPDATES")
            report.append("-" * 45)
            
            for production in self.report_data['production_reports'][:5]:
                report.append(f"🏭 {production['title']}")
                report.append(f"   Companies: {', '.join(production['tsx_companies'])}")
                if production['production_figures']:
                    report.append(f"   Figures: {', '.join(production['production_figures'][:3])}")
                report.append(f"   Published: {production['published']}")
                report.append("")
        
        # Insider Activity
        if self.report_data['insider_activity']:
            report.append("👔 INSIDER TRADING ACTIVITY")
            report.append("-" * 25)
            
            for insider in self.report_data['insider_activity'][:5]:
                report.append(f"📈 {insider['company_symbol']} - {insider['transaction_type']}")
                report.append(f"   Shares: {insider['shares']}")
                report.append(f"   Value: ${insider['value']}")
                if 'insider_type' in insider:
                    report.append(f"   Insider: {insider['insider_type']}")
                report.append("")
        
        # Canadian Trade Data
        if self.report_data['trade_data']:
            report.append("🇨🇦 CANADIAN TRADE & EXPORT CONTEXT")
            report.append("-" * 35)
            
            trade = self.report_data['trade_data']
            
            if 'exchange_rates' in trade:
                fx = trade['exchange_rates']
                report.append(f"💱 USD/CAD: {fx['current_usd_cad']} ({fx['trend']})")
                if fx.get('previous_week'):
                    report.append(f"   Weekly change from {fx['previous_week']}")
            
            if 'commodity_exports' in trade:
                commodities = trade['commodity_exports']
                report.append(f"🥇 Gold: ${commodities['gold_price_usd']:.2f} ({commodities['gold_weekly_change']:+.1f}%)")
                report.append(f"   Export competitiveness: {commodities['export_competitiveness']}")
            
            report.append("")
        
        # Canadian Economic Indicators
        if self.report_data['canadian_economics']:
            report.append("📈 CANADIAN ECONOMIC INDICATORS")
            report.append("-" * 32)
            
            econ = self.report_data['canadian_economics']
            
            if 'bank_of_canada_rate' in econ:
                boc = econ['bank_of_canada_rate']
                report.append(f"🏦 Bank of Canada Rate: {boc['current_rate']}%")
                report.append(f"   As of: {boc['date']}")
            
            if 'tsx_composite' in econ:
                tsx = econ['tsx_composite']
                report.append(f"📊 TSX Composite: {tsx['current_level']:.0f} ({tsx['weekly_change_percent']:+.1f}%)")
                report.append(f"   Trend: {tsx['trend']}")
            
            report.append("")
        
        # Earnings Calendar
        if self.report_data['earnings_calendar']:
            report.append("📅 UPCOMING EARNINGS CALENDAR")
            report.append("-" * 28)
            
            upcoming_earnings = [e for e in self.report_data['earnings_calendar'] if e['next_earnings'] == 'upcoming']
            
            if upcoming_earnings:
                for earnings in upcoming_earnings[:5]:
                    report.append(f"📊 {earnings['company_symbol']} - {earnings['company_name']}")
                    report.append(f"   Earnings Date: {earnings['earnings_date']}")
                    report.append("")
            else:
                report.append("• No upcoming earnings dates available")
                report.append("")
        
        # Summary
        report.append("📋 INTELLIGENCE SUMMARY")
        report.append("-" * 22)
        report.append(f"• Guidance updates found: {len(self.report_data['guidance_updates'])}")
        report.append(f"• Production reports: {len(self.report_data['production_reports'])}")
        report.append(f"• Insider transactions: {len(self.report_data['insider_activity'])}")
        report.append(f"• Economic indicators: {len(self.report_data['canadian_economics'])}")
        report.append("")
        
        report.append("🔗 Data Sources: Company IR pages, Mining.com, Kitco, Bank of Canada,")
        report.append("   Canadian Insider, Yahoo Finance, Statistics Canada")
        
        return "\n".join(report)

    def save_intel_report(self, report_text: str) -> tuple:
        """Save intelligence report to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON
        json_filename = f"business_intelligence_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save formatted report
        text_filename = f"business_intelligence_report_{timestamp}.txt"
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return json_filename, text_filename

async def main():
    """Generate comprehensive business intelligence report"""
    
    intel = ComprehensiveBusinessIntel()
    
    try:
        # Generate the report
        report_text = await intel.generate_comprehensive_intel_report()
        
        # Save to files
        json_file, text_file = intel.save_intel_report(report_text)
        
        # Display the report
        print(report_text)
        
        print("\n" + "="*65)
        print("📁 FILES SAVED:")
        print(f"• Detailed data: {json_file}")
        print(f"• Formatted report: {text_file}")
        print("")
        print("✅ Comprehensive business intelligence report completed!")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate intel report: {str(e)}")
        print(f"❌ Intel report generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n🧠 Business intelligence ready for strategic decision making!")
    else:
        print("\n💥 Intelligence gathering encountered errors.")