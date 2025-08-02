#!/usr/bin/env python3
"""
Comprehensive Agnico Eagle Multi-Source Test
Tests extraction from official website, LinkedIn, news sources, and financial platforms
"""

import asyncio
import json
import sqlite3
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from crawl4ai import AsyncWebCrawler
from pattern_based_extractor import PatternBasedExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgnicoComprehensiveTest:
    def __init__(self):
        self.extractor = PatternBasedExtractor()
        self.results = {
            "company": "Agnico Eagle Mines Limited (AEM.TO)",
            "test_date": datetime.now().isoformat(),
            "sources_tested": [],
            "data_extracted": {},
            "insights": [],
            "linkedin_content": {},
            "news_aggregation": {},
            "financial_platforms": {}
        }
        
        # Agnico Eagle source URLs
        self.agnico_sources = {
            "official_website": "https://www.agnicoeagle.com",
            "investor_relations": "https://www.agnicoeagle.com/english/investors/overview/default.aspx",
            "news_releases": "https://www.agnicoeagle.com/english/news-and-media/news-releases/default.aspx",
            "financial_reports": "https://www.agnicoeagle.com/english/investors/financial-information/default.aspx",
            "operations": "https://www.agnicoeagle.com/english/operations-and-development-projects/overview/default.aspx",
            "sustainability": "https://www.agnicoeagle.com/english/sustainability/overview/default.aspx",
            
            # Social media and external sources
            "linkedin_company": "https://www.linkedin.com/company/agnico-eagle-mines-limited/",
            "linkedin_posts": "https://www.linkedin.com/company/agnico-eagle-mines-limited/posts/",
            "twitter": "https://twitter.com/AgnicoEagle",
            
            # Financial platforms
            "yahoo_finance": "https://finance.yahoo.com/quote/AEM.TO",
            "google_finance": "https://www.google.com/finance/quote/AEM:TSE",
            "morningstar": "https://www.morningstar.ca/ca/report/stocks/t.aspx?t=0P00000242",
            
            # News aggregators
            "mining_com": "https://www.mining.com/tag/agnico-eagle/",
            "kitco_news": "https://www.kitco.com/news/",
            "northern_miner": "https://www.northernminer.com/",
            
            # SEC/SEDAR filings
            "sedar_plus": "https://www.sedarplus.ca/csa-party/records/document.html?id=4df6a3abc458e45fc4b3066b3d4ab4c4db6c6e9f4a7e3c4a6b5f8e9d7c1a2b3c",
            "sec_edgar": "https://www.sec.gov/edgar/search/#/ciks=0000002809"
        }

    async def test_official_sources(self):
        """Test all official Agnico Eagle sources"""
        
        logger.info("Testing official Agnico Eagle sources...")
        
        official_sources = [
            "official_website", "investor_relations", "news_releases", 
            "financial_reports", "operations", "sustainability"
        ]
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for source_name in official_sources:
                url = self.agnico_sources[source_name]
                
                try:
                    logger.info(f"Testing {source_name}: {url}")
                    
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=100
                    )
                    
                    if result.markdown and len(result.markdown) > 500:
                        # Extract data using our enhanced extractor
                        content = result.markdown
                        
                        # Extract structured data
                        financial_data = self.extractor.extract_financial_data(content)
                        operational_data = self.extractor.extract_operational_data(content)
                        news_items = self.extractor.extract_news_items(content, url)
                        dates = self.extractor.extract_dates(content)
                        
                        # Store results
                        source_data = {
                            "url": url,
                            "content_length": len(content),
                            "financial_data": self._dataclass_to_dict(financial_data),
                            "operational_data": self._dataclass_to_dict(operational_data),
                            "news_items": [self._dataclass_to_dict(item) for item in news_items],
                            "dates_found": dates,
                            "key_insights": self._extract_key_insights(content),
                            "relevance_score": sum(item.relevance_score for item in news_items),
                            "status": "success"
                        }
                        
                        self.results["data_extracted"][source_name] = source_data
                        self.results["sources_tested"].append(source_name)
                        
                        logger.info(f"✓ {source_name}: {len(content)} chars, {len(news_items)} news items")
                        
                        # Show immediate insights
                        if news_items:
                            print(f"\n{source_name.upper()} - TOP FINDINGS:")
                            for item in news_items[:3]:
                                print(f"  • {item.title[:80]}...")
                                print(f"    Category: {item.category}, Score: {item.relevance_score}")
                    
                    else:
                        logger.warning(f"✗ {source_name}: Insufficient content")
                        self.results["data_extracted"][source_name] = {"status": "insufficient_content"}
                
                except Exception as e:
                    logger.error(f"✗ {source_name}: {str(e)}")
                    self.results["data_extracted"][source_name] = {"status": "error", "error": str(e)}
                
                await asyncio.sleep(2)  # Rate limiting

    async def test_linkedin_sources(self):
        """Test LinkedIn company page and posts"""
        
        logger.info("Testing LinkedIn sources...")
        
        linkedin_sources = ["linkedin_company", "linkedin_posts"]
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for source_name in linkedin_sources:
                url = self.agnico_sources[source_name]
                
                try:
                    logger.info(f"Testing LinkedIn {source_name}: {url}")
                    
                    # LinkedIn requires special handling due to login requirements
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=50,
                        wait_for="networkidle0"  # Wait for dynamic content
                    )
                    
                    if result.markdown:
                        content = result.markdown
                        
                        # Extract LinkedIn-specific data
                        linkedin_insights = self._extract_linkedin_insights(content)
                        
                        self.results["linkedin_content"][source_name] = {
                            "url": url,
                            "content_length": len(content),
                            "insights": linkedin_insights,
                            "posts_found": self._count_linkedin_posts(content),
                            "engagement_indicators": self._find_engagement_indicators(content),
                            "status": "success"
                        }
                        
                        logger.info(f"✓ LinkedIn {source_name}: {len(content)} chars")
                        
                    else:
                        logger.warning(f"✗ LinkedIn {source_name}: No content (likely login required)")
                        self.results["linkedin_content"][source_name] = {
                            "status": "login_required", 
                            "note": "LinkedIn content requires authentication"
                        }
                
                except Exception as e:
                    logger.error(f"✗ LinkedIn {source_name}: {str(e)}")
                    self.results["linkedin_content"][source_name] = {"status": "error", "error": str(e)}
                
                await asyncio.sleep(3)  # Longer delay for LinkedIn

    async def test_financial_platforms(self):
        """Test financial data platforms"""
        
        logger.info("Testing financial platforms...")
        
        financial_sources = ["yahoo_finance", "google_finance", "morningstar"]
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for source_name in financial_sources:
                url = self.agnico_sources[source_name]
                
                try:
                    logger.info(f"Testing {source_name}: {url}")
                    
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=100,
                        wait_for="networkidle0"  # Wait for dynamic financial data
                    )
                    
                    if result.markdown:
                        content = result.markdown
                        
                        # Extract financial platform specific data
                        financial_metrics = self._extract_financial_platform_data(content, source_name)
                        
                        self.results["financial_platforms"][source_name] = {
                            "url": url,
                            "content_length": len(content),
                            "financial_metrics": financial_metrics,
                            "stock_data": self._extract_stock_data(content),
                            "analyst_data": self._extract_analyst_data(content),
                            "status": "success"
                        }
                        
                        logger.info(f"✓ {source_name}: Financial data extracted")
                        
                        # Show key financial data
                        if financial_metrics:
                            print(f"\n{source_name.upper()} - FINANCIAL DATA:")
                            for metric, value in financial_metrics.items():
                                if value:
                                    print(f"  • {metric}: {value}")
                    
                    else:
                        logger.warning(f"✗ {source_name}: No financial data")
                        self.results["financial_platforms"][source_name] = {"status": "no_data"}
                
                except Exception as e:
                    logger.error(f"✗ {source_name}: {str(e)}")
                    self.results["financial_platforms"][source_name] = {"status": "error", "error": str(e)}
                
                await asyncio.sleep(2)

    async def test_news_aggregators(self):
        """Test mining news aggregators"""
        
        logger.info("Testing news aggregators...")
        
        news_sources = ["mining_com", "kitco_news", "northern_miner"]
        
        async with AsyncWebCrawler(headless=True) as crawler:
            for source_name in news_sources:
                url = self.agnico_sources[source_name]
                
                try:
                    logger.info(f"Testing {source_name}: {url}")
                    
                    result = await crawler.arun(url=url, word_count_threshold=200)
                    
                    if result.markdown:
                        content = result.markdown
                        
                        # Search for Agnico-specific content
                        agnico_mentions = self._find_agnico_mentions(content)
                        recent_news = self._extract_recent_agnico_news(content)
                        
                        self.results["news_aggregation"][source_name] = {
                            "url": url,
                            "content_length": len(content),
                            "agnico_mentions": len(agnico_mentions),
                            "agnico_content": agnico_mentions,
                            "recent_news": recent_news,
                            "status": "success"
                        }
                        
                        logger.info(f"✓ {source_name}: {len(agnico_mentions)} Agnico mentions")
                        
                        if agnico_mentions:
                            print(f"\n{source_name.upper()} - AGNICO MENTIONS:")
                            for mention in agnico_mentions[:3]:
                                print(f"  • {mention[:100]}...")
                    
                    else:
                        logger.warning(f"✗ {source_name}: No content")
                        self.results["news_aggregation"][source_name] = {"status": "no_content"}
                
                except Exception as e:
                    logger.error(f"✗ {source_name}: {str(e)}")
                    self.results["news_aggregation"][source_name] = {"status": "error", "error": str(e)}
                
                await asyncio.sleep(2)

    def _dataclass_to_dict(self, obj):
        """Convert dataclass to dictionary"""
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if v is not None}
        return obj

    def _extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content"""
        
        insights = []
        content_lower = content.lower()
        
        # Key insight patterns
        insight_patterns = [
            r'(record[^.]*(?:production|revenue|earnings|profit)[^.]*)',
            r'(guidance[^.]*(?:increased|decreased|raised|lowered)[^.]*)',
            r'(acquisition[^.]*\$[0-9,]+ million[^.]*)',
            r'(new discovery[^.]*[^.]*)',
            r'(expansion[^.]*[^.]*million[^.]*)',
        ]
        
        for pattern in insight_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            insights.extend([match.strip() for match in matches])
        
        return insights[:5]  # Top 5 insights

    def _extract_linkedin_insights(self, content: str) -> Dict[str, Any]:
        """Extract LinkedIn-specific insights"""
        
        return {
            "company_updates": self._find_company_updates(content),
            "employee_count": self._extract_employee_count(content),
            "recent_posts": self._extract_recent_posts(content),
            "engagement_metrics": self._extract_engagement_metrics(content)
        }

    def _find_company_updates(self, content: str) -> List[str]:
        """Find company updates in LinkedIn content"""
        
        update_patterns = [
            r'(we are (?:pleased|excited|proud)[^.]*)',
            r'(agnico eagle (?:announces|reports|achieves)[^.]*)',
            r'(our team[^.]*)',
        ]
        
        updates = []
        for pattern in update_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            updates.extend(matches)
        
        return updates[:5]

    def _count_linkedin_posts(self, content: str) -> int:
        """Count LinkedIn posts in content"""
        
        post_indicators = ['posted', 'shared', 'updated', 'ago', 'likes', 'comments']
        post_count = sum(content.lower().count(indicator) for indicator in post_indicators)
        return min(post_count // 3, 20)  # Estimate posts

    def _find_engagement_indicators(self, content: str) -> Dict[str, int]:
        """Find engagement indicators"""
        
        engagement = {}
        
        # Look for engagement metrics
        likes_match = re.search(r'(\d+)\s*likes?', content, re.IGNORECASE)
        comments_match = re.search(r'(\d+)\s*comments?', content, re.IGNORECASE)
        shares_match = re.search(r'(\d+)\s*shares?', content, re.IGNORECASE)
        
        if likes_match:
            engagement['likes'] = int(likes_match.group(1))
        if comments_match:
            engagement['comments'] = int(comments_match.group(1))
        if shares_match:
            engagement['shares'] = int(shares_match.group(1))
        
        return engagement

    def _extract_financial_platform_data(self, content: str, platform: str) -> Dict[str, str]:
        """Extract financial data from specific platforms"""
        
        financial_data = {}
        content_lower = content.lower()
        
        # Common financial metrics patterns
        patterns = {
            'stock_price': r'(?:price|quote)[^$]*\$([0-9]+(?:\.[0-9]+)?)',
            'market_cap': r'market cap[^$]*\$([0-9,.]+[bmk]?)',
            'pe_ratio': r'p/e[^0-9]*([0-9]+(?:\.[0-9]+)?)',
            'dividend_yield': r'dividend yield[^0-9]*([0-9]+(?:\.[0-9]+)?%)',
            '52_week_high': r'52[^$]*high[^$]*\$([0-9]+(?:\.[0-9]+)?)',
            '52_week_low': r'52[^$]*low[^$]*\$([0-9]+(?:\.[0-9]+)?)',
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, content_lower)
            if match:
                financial_data[metric] = match.group(1)
        
        return financial_data

    def _extract_stock_data(self, content: str) -> Dict[str, str]:
        """Extract stock-specific data"""
        
        stock_data = {}
        
        # Volume, price change, etc.
        volume_match = re.search(r'volume[^0-9]*([0-9,]+)', content, re.IGNORECASE)
        change_match = re.search(r'change[^$]*\$([+-]?[0-9]+(?:\.[0-9]+)?)', content, re.IGNORECASE)
        percent_change_match = re.search(r'([+-]?[0-9]+(?:\.[0-9]+)?\%)', content)
        
        if volume_match:
            stock_data['volume'] = volume_match.group(1)
        if change_match:
            stock_data['price_change'] = change_match.group(1)
        if percent_change_match:
            stock_data['percent_change'] = percent_change_match.group(1)
        
        return stock_data

    def _extract_analyst_data(self, content: str) -> Dict[str, str]:
        """Extract analyst recommendations"""
        
        analyst_data = {}
        content_lower = content.lower()
        
        # Analyst recommendations
        recommendation_patterns = [
            r'(buy|sell|hold|strong buy|strong sell)',
            r'target price[^$]*\$([0-9]+(?:\.[0-9]+)?)',
            r'analyst[^0-9]*([0-9]+)',
        ]
        
        for pattern in recommendation_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                if 'target' in pattern:
                    analyst_data['target_price'] = matches[0]
                elif 'analyst' in pattern:
                    analyst_data['analyst_count'] = matches[0]
                else:
                    analyst_data['recommendation'] = matches[0]
        
        return analyst_data

    def _find_agnico_mentions(self, content: str) -> List[str]:
        """Find mentions of Agnico Eagle in content"""
        
        agnico_patterns = [
            r'agnico eagle[^.]*\.',
            r'aem\.to[^.]*\.',
            r'agnico[^.]*(?:mining|gold|production)[^.]*\.',
        ]
        
        mentions = []
        for pattern in agnico_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            mentions.extend(matches)
        
        return mentions

    def _extract_recent_agnico_news(self, content: str) -> List[Dict[str, str]]:
        """Extract recent news about Agnico"""
        
        news_items = []
        
        # Look for news patterns with Agnico mentions
        news_pattern = r'((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}[^.]*agnico[^.]*\.)'
        
        matches = re.findall(news_pattern, content, re.IGNORECASE)
        
        for match in matches:
            news_items.append({
                'content': match.strip(),
                'source': 'news_aggregator'
            })
        
        return news_items[:5]

    def _extract_employee_count(self, content: str) -> Optional[str]:
        """Extract employee count from LinkedIn"""
        
        employee_patterns = [
            r'([0-9,]+)\s*employees',
            r'([0-9,]+)\s*followers',
            r'size[^0-9]*([0-9,]+)',
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def _extract_recent_posts(self, content: str) -> List[str]:
        """Extract recent posts from LinkedIn"""
        
        post_patterns = [
            r'(we are[^.]*\.)',
            r'(excited to[^.]*\.)',
            r'(proud to[^.]*\.)',
        ]
        
        posts = []
        for pattern in post_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            posts.extend(matches)
        
        return posts[:5]

    def _extract_engagement_metrics(self, content: str) -> Dict[str, int]:
        """Extract engagement metrics from LinkedIn"""
        
        metrics = {}
        
        # Followers, connections, etc.
        followers_match = re.search(r'([0-9,]+)\s*followers', content, re.IGNORECASE)
        if followers_match:
            metrics['followers'] = int(followers_match.group(1).replace(',', ''))
        
        return metrics

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report"""
        
        report = []
        report.append("AGNICO EAGLE COMPREHENSIVE SOURCE ANALYSIS")
        report.append("=" * 60)
        report.append(f"Test Date: {self.results['test_date']}")
        report.append(f"Company: {self.results['company']}")
        report.append("")
        
        # Sources tested summary
        report.append("SOURCES TESTED:")
        report.append("-" * 20)
        
        all_sources = (
            list(self.results["data_extracted"].keys()) +
            list(self.results["linkedin_content"].keys()) +
            list(self.results["financial_platforms"].keys()) +
            list(self.results["news_aggregation"].keys())
        )
        
        successful_sources = []
        failed_sources = []
        
        for source in all_sources:
            # Check if source was successful
            source_data = (
                self.results["data_extracted"].get(source) or
                self.results["linkedin_content"].get(source) or
                self.results["financial_platforms"].get(source) or
                self.results["news_aggregation"].get(source) or
                {}
            )
            
            if source_data.get("status") == "success":
                successful_sources.append(source)
            else:
                failed_sources.append(source)
        
        report.append(f"✓ Successful: {len(successful_sources)}")
        report.append(f"✗ Failed: {len(failed_sources)}")
        report.append("")
        
        # Official website analysis
        if self.results["data_extracted"]:
            report.append("OFFICIAL WEBSITE ANALYSIS:")
            report.append("-" * 30)
            
            total_news_items = 0
            total_financial_points = 0
            
            for source, data in self.results["data_extracted"].items():
                if data.get("status") == "success":
                    news_count = len(data.get("news_items", []))
                    financial_points = len([v for v in data.get("financial_data", {}).values() if v])
                    
                    total_news_items += news_count
                    total_financial_points += financial_points
                    
                    report.append(f"• {source}: {news_count} news items, {financial_points} financial points")
            
            report.append(f"• TOTAL: {total_news_items} news items, {total_financial_points} financial points")
            report.append("")
        
        # LinkedIn analysis
        if self.results["linkedin_content"]:
            report.append("LINKEDIN ANALYSIS:")
            report.append("-" * 18)
            
            for source, data in self.results["linkedin_content"].items():
                if data.get("status") == "success":
                    posts = data.get("posts_found", 0)
                    engagement = data.get("engagement_indicators", {})
                    report.append(f"• {source}: {posts} posts found")
                    if engagement:
                        report.append(f"  Engagement: {engagement}")
                elif data.get("status") == "login_required":
                    report.append(f"• {source}: Requires authentication")
                else:
                    report.append(f"• {source}: Failed")
            report.append("")
        
        # Financial platforms analysis
        if self.results["financial_platforms"]:
            report.append("FINANCIAL PLATFORMS ANALYSIS:")
            report.append("-" * 32)
            
            for source, data in self.results["financial_platforms"].items():
                if data.get("status") == "success":
                    metrics_count = len(data.get("financial_metrics", {}))
                    stock_data_count = len(data.get("stock_data", {}))
                    report.append(f"• {source}: {metrics_count} financial metrics, {stock_data_count} stock data points")
                    
                    # Show key metrics
                    if data.get("financial_metrics"):
                        for metric, value in list(data["financial_metrics"].items())[:3]:
                            report.append(f"  - {metric}: {value}")
                else:
                    report.append(f"• {source}: Failed")
            report.append("")
        
        # News aggregation analysis
        if self.results["news_aggregation"]:
            report.append("NEWS AGGREGATION ANALYSIS:")
            report.append("-" * 28)
            
            total_mentions = 0
            for source, data in self.results["news_aggregation"].items():
                if data.get("status") == "success":
                    mentions = data.get("agnico_mentions", 0)
                    total_mentions += mentions
                    report.append(f"• {source}: {mentions} Agnico mentions")
                else:
                    report.append(f"• {source}: Failed")
            
            report.append(f"• TOTAL MENTIONS: {total_mentions}")
            report.append("")
        
        # Key insights
        report.append("KEY INSIGHTS DISCOVERED:")
        report.append("-" * 25)
        
        insights_found = []
        for data in self.results["data_extracted"].values():
            if isinstance(data, dict) and "key_insights" in data:
                insights_found.extend(data["key_insights"])
        
        if insights_found:
            for insight in insights_found[:10]:
                report.append(f"• {insight}")
        else:
            report.append("• No specific insights extracted")
        
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 16)
        
        if len(successful_sources) >= len(all_sources) * 0.7:
            report.append("✓ Data extraction pipeline working well")
        else:
            report.append("⚠ Some sources need improvement")
        
        if total_news_items > 5:
            report.append("✓ Good news content discovery")
        else:
            report.append("⚠ Limited news content found")
        
        if "linkedin_company" in failed_sources:
            report.append("• Consider LinkedIn API integration for authenticated access")
        
        if total_mentions > 0:
            report.append("✓ Successfully found external news mentions")
        
        return "\n".join(report)

    async def run_comprehensive_test(self):
        """Run the complete test suite"""
        
        print("🔍 AGNICO EAGLE COMPREHENSIVE SOURCE TEST")
        print("=" * 50)
        
        try:
            # Test official sources
            await self.test_official_sources()
            
            # Test LinkedIn
            await self.test_linkedin_sources()
            
            # Test financial platforms
            await self.test_financial_platforms()
            
            # Test news aggregators
            await self.test_news_aggregators()
            
            # Generate report
            report = self.generate_comprehensive_report()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"agnico_comprehensive_test_{timestamp}.json"
            report_file = f"agnico_comprehensive_report_{timestamp}.txt"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            print("\n" + report)
            print(f"\nFiles saved:")
            print(f"• Detailed results: {results_file}")
            print(f"• Summary report: {report_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Comprehensive test failed: {str(e)}")
            return False

async def main():
    """Run Agnico Eagle comprehensive test"""
    
    tester = AgnicoComprehensiveTest()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n✅ Agnico Eagle comprehensive test completed!")
    else:
        print("\n❌ Agnico Eagle comprehensive test failed!")

if __name__ == "__main__":
    asyncio.run(main())