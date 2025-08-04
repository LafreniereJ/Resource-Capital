#!/usr/bin/env python3
"""
Standalone Economics Data Scraper for August 4, 2025
Collects economic data from 4 target economics websites
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import re
import os
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    content_type: str

class SimpleEconomicsScraper:
    """Simple economics scraper using requests and BeautifulSoup"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Economics websites configuration
        self.economics_targets = {
            "trading_economics_canada": {
                "name": "Trading Economics Canada",
                "url": "https://tradingeconomics.com/canada/indicators",
                "type": "economic_indicators"
            },
            "rbc_economic_analysis": {
                "name": "RBC Economic Analysis",
                "url": "https://www.rbc.com/en/thought-leadership/economics/forward-guidance-our-weekly-preview/",
                "type": "economic_analysis"
            },
            "investing_commodities_analysis": {
                "name": "Investing.com Commodities Analysis",
                "url": "https://ca.investing.com/analysis/commodities",
                "type": "commodity_analysis"
            },
            "investing_commodities_news": {
                "name": "Investing.com Commodities News",
                "url": "https://ca.investing.com/news/commodities-news",
                "type": "commodity_news"
            }
        }
        
        # Keywords for relevance scoring
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
    
    def scrape_all_economics_sites(self) -> Dict[str, Any]:
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
                site_result = self._scrape_economics_site(site_key, site_config)
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
            time.sleep(3)
        
        # Generate performance summary
        results["performance_summary"] = self._generate_performance_summary(results["site_results"])
        results["total_scraping_time"] = time.time() - start_time
        
        # Save results to JSON file
        os.makedirs("reports/2025-08-04", exist_ok=True)
        output_file = "reports/2025-08-04/economics_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Economics data scraping completed in {results['total_scraping_time']:.1f}s")
        logger.info(f"Results saved to {output_file}")
        
        return results
    
    def _scrape_economics_site(self, site_key: str, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape individual economics site"""
        
        site_result = {
            "site_name": site_config["name"],
            "url": site_config["url"],
            "content_type": site_config["type"],
            "success": False,
            "scraper_used": "requests+beautifulsoup",
            "content_length": 0,
            "word_count": 0,
            "economics_content": [],
            "data_quality": "unknown",
            "mining_relevance": 0
        }
        
        try:
            # Make HTTP request
            response = self.session.get(site_config["url"], timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            text_content = self._extract_main_content(soup, site_config["url"])
            
            if len(text_content) < 100:
                site_result["error"] = "Insufficient content extracted"
                return site_result
            
            site_result["content_length"] = len(text_content)
            site_result["word_count"] = len(text_content.split())
            site_result["success"] = True
            
            # Extract and analyze content based on site type
            if site_config["type"] == "economic_indicators":
                economics_content = self._extract_economic_indicators(text_content, site_config, soup)
            else:
                economics_content = self._extract_analysis_content(text_content, site_config)
            
            site_result["economics_content"] = [asdict(content) for content in economics_content]
            site_result["content_items_extracted"] = len(economics_content)
            
            # Calculate data quality and mining relevance
            site_result["data_quality"] = self._assess_data_quality(economics_content, text_content)
            site_result["mining_relevance"] = self._calculate_mining_relevance(economics_content)
            
        except requests.RequestException as e:
            site_result["error"] = f"Request failed: {str(e)}"
        except Exception as e:
            site_result["error"] = f"Parsing failed: {str(e)}"
        
        return site_result
    
    def _extract_main_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract main content from HTML"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try different content selectors based on URL
        content_selectors = []
        
        if 'tradingeconomics.com' in url:
            content_selectors = ['.indicators-table', '.economic-data', 'table', '.main-content', 'main', 'body']
        elif 'rbc.com' in url:
            content_selectors = ['.article-content', '.content', '.rbc-content', 'main', '.main-content', 'body']
        elif 'investing.com' in url:
            content_selectors = ['.articleItem', '.article-item', '.js-article-item', 'main', '.main-content', 'body']
        else:
            content_selectors = ['article', '.article-content', '.content', 'main', '.main-content', 'body']
        
        # Try each selector
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content_parts = []
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > 50:  # Only include substantial content
                        content_parts.append(text)
                
                if content_parts:
                    return '\n\n'.join(content_parts)
        
        # Fallback: get all text from body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_economic_indicators(self, content: str, site_config: Dict[str, Any], soup: BeautifulSoup) -> List[EconomicsContent]:
        """Extract economic indicators from Trading Economics Canada"""
        
        economics_contents = []
        data_points = []
        
        # Look for tables with economic data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    indicator_name = cells[0].get_text(strip=True)
                    current_value = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    change = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    
                    if indicator_name and current_value:
                        data_points.append(EconomicsDataPoint(
                            indicator_name=indicator_name,
                            current_value=current_value,
                            change=change,
                            source="Trading Economics Canada",
                            category="economic_indicator",
                            date=datetime.now().strftime("%Y-%m-%d")
                        ))
        
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
    
    def _extract_analysis_content(self, content: str, site_config: Dict[str, Any]) -> List[EconomicsContent]:
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
                    url=site_config["url"],
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
    
    def _assess_data_quality(self, economics_contents: List[EconomicsContent], text_content: str) -> str:
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
            "scrapers_used": ["requests+beautifulsoup"]
        }

def main():
    """Main function to run the economics data scraper"""
    
    print("Starting Economics Data Scraper for August 4, 2025")
    print("=" * 60)
    
    scraper = SimpleEconomicsScraper()
    
    try:
        results = scraper.scrape_all_economics_sites()
        
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
        
        return results
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    main()