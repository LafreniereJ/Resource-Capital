#!/usr/bin/env python3
"""
Economics Data Scraper - Specialized scraper for economics category websites
Focuses on extracting current economic indicators, analysis, and news relevant to mining/commodities
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import re
import os
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EconomicsDataPoint:
    """Structure for economic data points"""
    indicator_name: str
    current_value: str
    previous_value: str = ""
    change: str = ""
    date: str = ""
    forecast: str = ""
    unit: str = ""
    source: str = ""
    category: str = ""

@dataclass
class EconomicsContent:
    """Structure for economics content extraction"""
    url: str
    title: str
    date: str
    content: str
    data_points: List[EconomicsDataPoint]
    key_insights: List[str]
    commodity_mentions: List[str]
    canadian_focus: bool
    mining_relevance_score: int
    content_type: str  # indicators, analysis, news
    
class EconomicsDataScraper:
    """Specialized scraper for economics data collection"""
    
    def __init__(self):
        self.scraper = UnifiedScraper()
        self.intelligence = ScraperIntelligence()
        
        # Economics websites configuration
        self.economics_targets = {
            "trading_economics_canada": {
                "name": "Trading Economics Canada",
                "url": "https://tradingeconomics.com/canada/indicators",
                "type": "economic_indicators",
                "selectors": {
                    "indicators_table": "table.table-indicators, .indicators-table, .economic-data",
                    "indicator_rows": "tr, .indicator-row",
                    "indicator_name": "td:first-child, .indicator-name",
                    "current_value": "td:nth-child(2), .current-value, .last-value",
                    "previous_value": "td:nth-child(3), .previous-value",
                    "change": "td:nth-child(4), .change",
                    "date": "td:nth-child(5), .date, .last-updated"
                },
                "js_heavy": True,
                "wait_time": 5
            },
            "rbc_economic_analysis": {
                "name": "RBC Economic Analysis", 
                "url": "https://www.rbc.com/en/thought-leadership/economics/forward-guidance-our-weekly-preview/",
                "type": "economic_analysis",
                "selectors": {
                    "article_content": ".article-content, .content, .rbc-content",
                    "headline": "h1, .headline, .article-title",
                    "date": ".date, .publish-date, time",
                    "key_points": ".key-points, .highlights, ul li"
                },
                "js_heavy": False,
                "wait_time": 3
            },
            "investing_commodities_analysis": {
                "name": "Investing.com Commodities Analysis",
                "url": "https://ca.investing.com/analysis/commodities", 
                "type": "commodity_analysis",
                "selectors": {
                    "articles": ".articleItem, .article-item, .js-article-item",
                    "article_title": ".title, .article-title, h3 a",
                    "article_content": ".article-content, .articlePage",
                    "date": ".date, .time, .articleDateTime",
                    "summary": ".summary, .article-summary"
                },
                "js_heavy": True,
                "wait_time": 4,
                "follow_links": True,
                "max_articles": 10
            },
            "investing_commodities_news": {
                "name": "Investing.com Commodities News",
                "url": "https://ca.investing.com/news/commodities-news",
                "type": "commodity_news", 
                "selectors": {
                    "news_items": ".js-article-item, .articleItem, .news-item",
                    "news_title": ".title, .article-title, h3 a",
                    "news_content": ".article-content, .articlePage",
                    "date": ".date, .time, .articleDateTime",
                    "summary": ".summary, .article-summary"
                },
                "js_heavy": True,
                "wait_time": 4,
                "follow_links": True,
                "max_articles": 15
            }
        }
        
        # Keywords for economic relevance scoring
        self.mining_keywords = [
            "mining", "mine", "miner", "exploration", "ore", "deposit", "resource",
            "gold", "silver", "copper", "platinum", "nickel", "zinc", "iron ore",
            "commodity", "commodities", "metals", "precious metals", "base metals"
        ]
        
        self.economic_indicators = [
            "gdp", "inflation", "cpi", "ppi", "interest rate", "employment", "unemployment",
            "manufacturing", "industrial production", "trade balance", "current account",
            "business investment", "consumer spending", "retail sales"
        ]
        
        self.canadian_keywords = [
            "canada", "canadian", "bank of canada", "boc", "statistics canada",
            "toronto", "ontario", "quebec", "british columbia", "alberta"
        ]
        
    async def scrape_all_economics_sites(self) -> Dict[str, Any]:
        """Scrape all 4 economics websites and compile results"""
        
        logger.info("Starting systematic economics data scraping for August 4, 2025")
        
        start_time = time.time()
        results = {
            "scraping_session": {
                "date": datetime.now().isoformat(),
                "purpose": "Economics data collection for mining intelligence",
                "target_sites": 4,
                "focus": "Canadian economic data, commodity forecasts, mining sector analysis"
            },
            "site_results": {},
            "performance_summary": {},
            "aggregated_data": {
                "economic_indicators": [],
                "commodity_analysis": [],
                "canadian_economic_news": [],
                "mining_relevant_insights": []
            }
        }
        
        # Process each target site
        for site_key, site_config in self.economics_targets.items():
            logger.info(f"Scraping {site_config['name']} - {site_config['url']}")
            
            site_start_time = time.time()
            
            try:
                site_result = await self._scrape_economics_site(site_key, site_config)
                site_result["response_time"] = time.time() - site_start_time
                site_result["timestamp"] = datetime.now().isoformat()
                
                results["site_results"][site_key] = site_result
                
                # Add to aggregated data based on content type
                if site_result["success"]:
                    self._aggregate_site_data(site_result, results["aggregated_data"])
                
                logger.info(f"Completed {site_config['name']} in {site_result['response_time']:.1f}s")
                
            except Exception as e:
                logger.error(f"Error scraping {site_config['name']}: {str(e)}")
                results["site_results"][site_key] = {
                    "success": False,
                    "error": str(e),
                    "response_time": time.time() - site_start_time,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Rate limiting between sites
            await asyncio.sleep(2)
        
        # Generate performance summary
        results["performance_summary"] = self._generate_performance_summary(results["site_results"])
        results["total_scraping_time"] = time.time() - start_time
        
        # Save results to JSON file
        output_file = "/Projects/Resource Capital/reports/2025-08-04/economics_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Economics data scraping completed in {results['total_scraping_time']:.1f}s")
        logger.info(f"Results saved to {output_file}")
        
        return results
    
    async def _scrape_economics_site(self, site_key: str, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape individual economics site"""
        
        # Configure scraping strategy based on site requirements
        strategy = ScrapingStrategy(
            primary="playwright" if site_config["js_heavy"] else "requests",
            fallbacks=["requests", "playwright", "selenium"] if site_config["js_heavy"] else ["playwright", "requests"],
            timeout=45,
            retries=3,
            rate_limit=2.0
        )
        
        # Primary page scrape
        scraping_result = await self.scraper.scrape(
            url=site_config["url"],
            target_config=site_config,
            strategy=strategy
        )
        
        site_result = {
            "site_name": site_config["name"],
            "url": site_config["url"],
            "content_type": site_config["type"],
            "success": scraping_result.success,
            "scraper_used": scraping_result.scraper_used,
            "content_length": len(scraping_result.content),
            "word_count": scraping_result.word_count,
            "economics_content": [],
            "data_quality": "unknown",
            "mining_relevance": 0
        }
        
        if not scraping_result.success:
            site_result["error"] = scraping_result.error_message
            return site_result
        
        # Extract and analyze content based on site type
        if site_config["type"] == "economic_indicators":
            economics_content = await self._extract_economic_indicators(
                scraping_result.content, site_config, site_key
            )
        elif site_config["type"] in ["economic_analysis", "commodity_analysis", "commodity_news"]:
            economics_content = await self._extract_analysis_content(
                scraping_result.content, site_config, site_key, scraping_result.url
            )
        else:
            economics_content = []
        
        site_result["economics_content"] = [asdict(content) for content in economics_content]
        site_result["content_items_extracted"] = len(economics_content)
        
        # Calculate data quality and mining relevance
        site_result["data_quality"] = self._assess_data_quality(economics_content, scraping_result)
        site_result["mining_relevance"] = self._calculate_mining_relevance(economics_content)
        
        return site_result
    
    async def _extract_economic_indicators(self, content: str, site_config: Dict[str, Any], site_key: str) -> List[EconomicsContent]:
        """Extract economic indicators from Trading Economics Canada"""
        
        economics_contents = []
        
        # Look for key Canadian economic indicators in the content
        indicators_found = []
        
        # Parse common economic indicators from text content
        indicator_patterns = {
            "GDP Growth": r"GDP.*?([+-]?\d+\.?\d*%?)",
            "Inflation Rate": r"Inflation.*?([+-]?\d+\.?\d*%?)", 
            "Interest Rate": r"Interest Rate.*?([+-]?\d+\.?\d*%?)",
            "Unemployment Rate": r"Unemployment.*?([+-]?\d+\.?\d*%?)",
            "Manufacturing PMI": r"Manufacturing.*?([+-]?\d+\.?\d*)",
            "Trade Balance": r"Trade Balance.*?([+-]?\d+\.?\d*)",
            "Current Account": r"Current Account.*?([+-]?\d+\.?\d*)"
        }
        
        data_points = []
        for indicator_name, pattern in indicator_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches[:1]:  # Take first match
                    data_points.append(EconomicsDataPoint(
                        indicator_name=indicator_name,
                        current_value=match,
                        source="Trading Economics Canada",
                        category="economic_indicator",
                        date=datetime.now().strftime("%Y-%m-%d")
                    ))
        
        # Extract key insights from content
        key_insights = self._extract_key_insights(content)
        commodity_mentions = self._extract_commodity_mentions(content)
        
        if data_points or key_insights:
            economics_content = EconomicsContent(
                url=site_config["url"],
                title="Canadian Economic Indicators",
                date=datetime.now().strftime("%Y-%m-%d"),
                content=content[:1000],  # First 1000 chars as summary
                data_points=data_points,
                key_insights=key_insights,
                commodity_mentions=commodity_mentions,
                canadian_focus=True,
                mining_relevance_score=self._score_mining_relevance(content),
                content_type="economic_indicators"
            )
            economics_contents.append(economics_content)
        
        return economics_contents
    
    async def _extract_analysis_content(self, content: str, site_config: Dict[str, Any], site_key: str, url: str) -> List[EconomicsContent]:
        """Extract analysis content from RBC and Investing.com sites"""
        
        economics_contents = []
        
        # Split content into sections for analysis
        sections = self._split_content_into_sections(content)
        
        for i, section in enumerate(sections[:5]):  # Process up to 5 sections
            if len(section) < 200:  # Skip short sections
                continue
            
            # Extract structured data from section
            title = self._extract_title_from_section(section)
            date = self._extract_date_from_section(section)
            key_insights = self._extract_key_insights(section)
            commodity_mentions = self._extract_commodity_mentions(section)
            
            # Determine if this is Canadian-focused content
            canadian_focus = any(keyword in section.lower() for keyword in self.canadian_keywords)
            
            mining_relevance_score = self._score_mining_relevance(section)
            
            # Only include content with some relevance to mining/commodities
            if mining_relevance_score > 0 or commodity_mentions:
                economics_content = EconomicsContent(
                    url=url,
                    title=title or f"Economic Analysis Section {i+1}",
                    date=date or datetime.now().strftime("%Y-%m-%d"),
                    content=section,
                    data_points=[],  # Analysis content typically doesn't have structured data points
                    key_insights=key_insights,
                    commodity_mentions=commodity_mentions,
                    canadian_focus=canadian_focus,
                    mining_relevance_score=mining_relevance_score,
                    content_type=site_config["type"]
                )
                economics_contents.append(economics_content)
        
        return economics_contents
    
    def _split_content_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections for analysis"""
        
        # Split by common section delimiters
        sections = []
        
        # Split by double newlines first
        paragraphs = content.split('\n\n')
        
        current_section = []
        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # Skip short paragraphs
                continue
            
            current_section.append(paragraph.strip())
            
            # Create section when we reach reasonable length
            if len('\n\n'.join(current_section)) > 500:
                sections.append('\n\n'.join(current_section))
                current_section = []
        
        # Add remaining content as final section
        if current_section:
            sections.append('\n\n'.join(current_section))
        
        return sections
    
    def _extract_title_from_section(self, section: str) -> str:
        """Extract title from content section"""
        lines = section.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 120:
                # Likely a title
                return line
        return ""
    
    def _extract_date_from_section(self, section: str) -> str:
        """Extract date from content section"""
        # Look for date patterns
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'  # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, section, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content"""
        insights = []
        
        # Look for sentences with key economic/mining terms
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30 or len(sentence) > 200:
                continue
            
            # Check if sentence contains relevant terms
            relevant_score = 0
            relevant_score += sum(1 for keyword in self.mining_keywords if keyword.lower() in sentence.lower())
            relevant_score += sum(1 for keyword in self.economic_indicators if keyword.lower() in sentence.lower())
            relevant_score += sum(0.5 for keyword in self.canadian_keywords if keyword.lower() in sentence.lower())
            
            if relevant_score >= 1.0:
                insights.append(sentence)
            
            # Limit insights
            if len(insights) >= 10:
                break
        
        return insights
    
    def _extract_commodity_mentions(self, content: str) -> List[str]:
        """Extract commodity mentions from content"""
        commodities = [
            "gold", "silver", "copper", "platinum", "palladium", "nickel", "zinc",
            "lead", "iron ore", "aluminum", "tin", "uranium", "lithium", "cobalt",
            "oil", "natural gas", "coal", "wheat", "corn", "soybeans"
        ]
        
        mentions = []
        content_lower = content.lower()
        
        for commodity in commodities:
            if commodity in content_lower:
                # Find context around commodity mention
                pattern = rf'.{{0,50}}\b{re.escape(commodity)}\b.{{0,50}}'
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches[:2]:  # Limit matches per commodity
                    mentions.append(f"{commodity}: {match.strip()}")
        
        return mentions
    
    def _score_mining_relevance(self, content: str) -> int:
        """Score content relevance to mining sector (0-10)"""
        content_lower = content.lower()
        score = 0
        
        # Mining keywords (high weight)
        mining_mentions = sum(1 for keyword in self.mining_keywords if keyword in content_lower)
        score += min(mining_mentions * 2, 6)
        
        # Economic indicators (medium weight)
        economic_mentions = sum(1 for keyword in self.economic_indicators if keyword in content_lower)
        score += min(economic_mentions, 3)
        
        # Canadian focus (low weight)
        canadian_mentions = sum(1 for keyword in self.canadian_keywords if keyword in content_lower)
        score += min(canadian_mentions, 1)
        
        return min(score, 10)
    
    def _aggregate_site_data(self, site_result: Dict[str, Any], aggregated_data: Dict[str, Any]):
        """Aggregate site data into combined datasets"""
        
        if not site_result["success"] or not site_result["economics_content"]:
            return
        
        for content_item in site_result["economics_content"]:
            content_type = content_item["content_type"]
            
            if content_type == "economic_indicators":
                aggregated_data["economic_indicators"].extend(content_item["data_points"])
            elif content_type in ["economic_analysis", "commodity_analysis"]:
                aggregated_data["commodity_analysis"].append({
                    "source": site_result["site_name"],
                    "title": content_item["title"],
                    "key_insights": content_item["key_insights"],
                    "commodity_mentions": content_item["commodity_mentions"],
                    "mining_relevance_score": content_item["mining_relevance_score"]
                })
            elif content_type == "commodity_news":
                aggregated_data["canadian_economic_news"].append({
                    "source": site_result["site_name"],
                    "title": content_item["title"],
                    "date": content_item["date"],
                    "key_insights": content_item["key_insights"][:3],  # Top 3 insights
                    "canadian_focus": content_item["canadian_focus"]
                })
            
            # Add high-relevance insights to mining relevant section
            if content_item["mining_relevance_score"] >= 5:
                aggregated_data["mining_relevant_insights"].append({
                    "source": site_result["site_name"],
                    "title": content_item["title"],
                    "key_insights": content_item["key_insights"][:2],
                    "commodity_mentions": content_item["commodity_mentions"][:3],
                    "relevance_score": content_item["mining_relevance_score"]
                })
    
    def _assess_data_quality(self, economics_contents: List[EconomicsContent], scraping_result: ScrapingResult) -> str:
        """Assess quality of extracted data"""
        
        if not economics_contents:
            return "poor"
        
        total_insights = sum(len(content.key_insights) for content in economics_contents)
        total_data_points = sum(len(content.data_points) for content in economics_contents)
        avg_relevance = sum(content.mining_relevance_score for content in economics_contents) / len(economics_contents)
        
        if total_data_points >= 3 or (total_insights >= 5 and avg_relevance >= 3):
            return "excellent"
        elif total_data_points >= 1 or (total_insights >= 3 and avg_relevance >= 2):
            return "good"
        elif total_insights >= 1 or avg_relevance >= 1:
            return "fair"
        else:
            return "poor"
    
    def _calculate_mining_relevance(self, economics_contents: List[EconomicsContent]) -> int:
        """Calculate overall mining relevance score for site (0-10)"""
        
        if not economics_contents:
            return 0
        
        return int(sum(content.mining_relevance_score for content in economics_contents) / len(economics_contents))
    
    def _generate_performance_summary(self, site_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary across all sites"""
        
        total_sites = len(site_results)
        successful_sites = sum(1 for result in site_results.values() if result.get("success", False))
        
        avg_response_time = sum(result.get("response_time", 0) for result in site_results.values()) / total_sites
        
        total_content_items = sum(result.get("content_items_extracted", 0) for result in site_results.values())
        
        quality_distribution = {}
        for result in site_results.values():
            quality = result.get("data_quality", "unknown")
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        mining_relevance_scores = [result.get("mining_relevance", 0) for result in site_results.values() if result.get("success")]
        avg_mining_relevance = sum(mining_relevance_scores) / len(mining_relevance_scores) if mining_relevance_scores else 0
        
        return {
            "sites_attempted": total_sites,
            "sites_successful": successful_sites,
            "success_rate": round((successful_sites / total_sites) * 100, 1),
            "average_response_time": round(avg_response_time, 2),
            "total_content_items_extracted": total_content_items,
            "data_quality_distribution": quality_distribution,
            "average_mining_relevance": round(avg_mining_relevance, 1),
            "scrapers_used": list(set(result.get("scraper_used", "unknown") for result in site_results.values()))
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.scraper.cleanup()

# Convenience function for standalone execution
async def scrape_economics_data() -> Dict[str, Any]:
    """Convenience function to scrape all economics data"""
    scraper = EconomicsDataScraper()
    try:
        return await scraper.scrape_all_economics_sites()
    finally:
        await scraper.cleanup()

# Example usage and testing
if __name__ == "__main__":
    async def test_economics_scraper():
        """Test the economics data scraper"""
        
        print("Starting Economics Data Scraper Test")
        print("=" * 60)
        
        results = await scrape_economics_data()
        
        print(f"\nScraping Results Summary:")
        print(f"Sites Attempted: {results['performance_summary']['sites_attempted']}")
        print(f"Sites Successful: {results['performance_summary']['sites_successful']}")
        print(f"Success Rate: {results['performance_summary']['success_rate']}%")
        print(f"Average Response Time: {results['performance_summary']['average_response_time']}s")
        print(f"Total Content Items: {results['performance_summary']['total_content_items_extracted']}")
        print(f"Average Mining Relevance: {results['performance_summary']['average_mining_relevance']}/10")
        
        print(f"\nData Quality Distribution:")
        for quality, count in results['performance_summary']['data_quality_distribution'].items():
            print(f"  {quality}: {count} sites")
        
        print(f"\nAggregated Data Summary:")
        print(f"Economic Indicators: {len(results['aggregated_data']['economic_indicators'])}")
        print(f"Commodity Analysis Items: {len(results['aggregated_data']['commodity_analysis'])}")
        print(f"Economic News Items: {len(results['aggregated_data']['canadian_economic_news'])}")
        print(f"High-Relevance Mining Insights: {len(results['aggregated_data']['mining_relevant_insights'])}")
        
        print(f"\nDetailed Site Results:")
        for site_key, site_result in results['site_results'].items():
            print(f"\n{site_result.get('site_name', site_key)}:")
            print(f"  Success: {site_result.get('success', False)}")
            print(f"  Response Time: {site_result.get('response_time', 0):.1f}s")
            print(f"  Data Quality: {site_result.get('data_quality', 'unknown')}")
            print(f"  Mining Relevance: {site_result.get('mining_relevance', 0)}/10")
            print(f"  Content Items: {site_result.get('content_items_extracted', 0)}")
            if not site_result.get('success') and 'error' in site_result:
                print(f"  Error: {site_result['error']}")
    
    asyncio.run(test_economics_scraper())