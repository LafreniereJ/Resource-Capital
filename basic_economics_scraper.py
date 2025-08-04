#!/usr/bin/env python3
"""
Basic Economics Data Scraper for August 4, 2025
Uses only built-in Python modules to collect economic data
"""

import json
import time
import re
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from html.parser import HTMLParser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EconomicsHTMLParser(HTMLParser):
    """Simple HTML parser to extract text content"""
    
    def __init__(self):
        super().__init__()
        self.content = []
        self.current_text = ""
        self.in_script = False
        self.in_style = False
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
    
    def handle_starttag(self, tag, attrs):
        if tag.lower() in ['script', 'style']:
            self.in_script = True
        elif tag.lower() == 'table':
            self.in_table = True
            self.current_table = []
        elif tag.lower() == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag.lower() in ['td', 'th'] and self.in_row:
            self.in_cell = True
            self.current_cell = ""
    
    def handle_endtag(self, tag):
        if tag.lower() in ['script', 'style']:
            self.in_script = False
        elif tag.lower() == 'table':
            self.in_table = False
            if self.current_table:
                self.tables.append(self.current_table)
        elif tag.lower() == 'tr' and self.in_table:
            self.in_row = False
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag.lower() in ['td', 'th'] and self.in_row:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
    
    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            if self.in_cell:
                self.current_cell += data
            else:
                self.content.append(data.strip())
    
    def get_text(self):
        """Get all text content"""
        return ' '.join([text for text in self.content if text])
    
    def get_tables(self):
        """Get all extracted tables"""
        return self.tables

class BasicEconomicsScraper:
    """Basic economics scraper using only built-in Python modules"""
    
    def __init__(self):
        # Economics websites to scrape
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
    
    def scrape_all_economics_sites(self):
        """Scrape all 4 economics websites and compile results"""
        
        logger.info("Starting basic economics data scraping for August 4, 2025")
        
        start_time = time.time()
        results = {
            "scraping_session": {
                "date": datetime.now().isoformat(),
                "purpose": "Economics data collection for mining intelligence",
                "target_sites": 4,
                "focus": "Canadian economic data, commodity forecasts, mining sector analysis",
                "method": "Basic HTTP requests with built-in Python modules"
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
                
                # Add to aggregated data
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
    
    def _scrape_economics_site(self, site_key, site_config):
        """Scrape individual economics site"""
        
        site_result = {
            "site_name": site_config["name"],
            "url": site_config["url"],
            "content_type": site_config["type"],
            "success": False,
            "scraper_used": "urllib+htmlparser",
            "content_length": 0,
            "word_count": 0,
            "economics_content": [],
            "data_quality": "unknown",
            "mining_relevance": 0
        }
        
        try:
            # Create request with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            request = Request(site_config["url"], headers=headers)
            
            # Make HTTP request
            with urlopen(request, timeout=30) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            
            # Parse HTML content
            parser = EconomicsHTMLParser()
            parser.feed(html_content)
            
            text_content = parser.get_text()
            tables = parser.get_tables()
            
            if len(text_content) < 100:
                site_result["error"] = "Insufficient content extracted"
                return site_result
            
            site_result["content_length"] = len(text_content)
            site_result["word_count"] = len(text_content.split())
            site_result["success"] = True
            
            # Extract economics content
            economics_content = self._extract_economics_content(text_content, tables, site_config)
            
            site_result["economics_content"] = economics_content
            site_result["content_items_extracted"] = len(economics_content)
            
            # Calculate data quality and mining relevance
            site_result["data_quality"] = self._assess_data_quality(economics_content, text_content)
            site_result["mining_relevance"] = self._calculate_mining_relevance(text_content)
            
        except Exception as e:
            site_result["error"] = str(e)
        
        return site_result
    
    def _extract_economics_content(self, text_content, tables, site_config):
        """Extract economics content from text and tables"""
        
        economics_content = []
        
        # Extract economic indicators from tables (for Trading Economics)
        if site_config["type"] == "economic_indicators" and tables:
            indicators = []
            for table in tables:
                for row in table[1:]:  # Skip header row
                    if len(row) >= 2:
                        indicator_name = row[0]
                        current_value = row[1] if len(row) > 1 else ""
                        change = row[2] if len(row) > 2 else ""
                        
                        if indicator_name and current_value:
                            indicators.append({
                                "indicator_name": indicator_name,
                                "current_value": current_value,
                                "change": change,
                                "source": site_config["name"],
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
            
            if indicators:
                economics_content.append({
                    "title": "Economic Indicators",
                    "type": "indicators",
                    "data_points": indicators,
                    "mining_relevance": self._calculate_mining_relevance(text_content)
                })
        
        # Extract key insights from text content
        key_insights = self._extract_key_insights(text_content)
        commodity_mentions = self._extract_commodity_mentions(text_content)
        
        if key_insights or commodity_mentions:
            economics_content.append({
                "title": f"{site_config['name']} Analysis",
                "type": "analysis",
                "key_insights": key_insights,
                "commodity_mentions": commodity_mentions,
                "canadian_focus": any(keyword in text_content.lower() for keyword in self.canadian_keywords),
                "mining_relevance": self._calculate_mining_relevance(text_content)
            })
        
        return economics_content
    
    def _extract_key_insights(self, content):
        """Extract key insights from content"""
        insights = []
        
        # Split content into sentences
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
    
    def _extract_commodity_mentions(self, content):
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
    
    def _calculate_mining_relevance(self, content):
        """Calculate mining relevance score (0-10)"""
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
    
    def _aggregate_site_data(self, site_result, aggregated_data):
        """Aggregate site data into combined datasets"""
        
        if not site_result["success"] or not site_result["economics_content"]:
            return
        
        for content_item in site_result["economics_content"]:
            if content_item.get("type") == "indicators":
                aggregated_data["economic_indicators"].extend(content_item.get("data_points", []))
            elif content_item.get("type") == "analysis":
                aggregated_data["commodity_analysis"].append({
                    "source": site_result["site_name"],
                    "key_insights": content_item.get("key_insights", []),
                    "commodity_mentions": content_item.get("commodity_mentions", []),
                    "mining_relevance": content_item.get("mining_relevance", 0)
                })
                
                # Add to Canadian economic news if Canadian-focused
                if content_item.get("canadian_focus"):
                    aggregated_data["canadian_economic_news"].append({
                        "source": site_result["site_name"],
                        "key_insights": content_item.get("key_insights", [])[:3],
                        "canadian_focus": True
                    })
                
                # Add high-relevance content to mining insights
                if content_item.get("mining_relevance", 0) >= 5:
                    aggregated_data["mining_relevant_insights"].append({
                        "source": site_result["site_name"],
                        "key_insights": content_item.get("key_insights", [])[:2],
                        "commodity_mentions": content_item.get("commodity_mentions", [])[:3],
                        "relevance_score": content_item.get("mining_relevance", 0)
                    })
    
    def _assess_data_quality(self, economics_content, text_content):
        """Assess quality of extracted data"""
        
        if not economics_content:
            return "poor"
        
        total_insights = sum(len(item.get("key_insights", [])) for item in economics_content)
        total_data_points = sum(len(item.get("data_points", [])) for item in economics_content)
        
        if total_data_points >= 3 or total_insights >= 5:
            return "excellent"
        elif total_data_points >= 1 or total_insights >= 3:
            return "good"
        elif total_insights >= 1:
            return "fair"
        else:
            return "poor"
    
    def _generate_performance_summary(self, site_results):
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
            "scrapers_used": ["urllib+htmlparser"]
        }

def main():
    """Main function to run the economics data scraper"""
    
    print("Starting Basic Economics Data Scraper for August 4, 2025")
    print("=" * 60)
    print("Using built-in Python modules only (urllib + HTMLParser)")
    print()
    
    scraper = BasicEconomicsScraper()
    
    try:
        results = scraper.scrape_all_economics_sites()
        
        print(f"\nSCRAPING RESULTS SUMMARY")
        print("=" * 40)
        print(f"Sites Attempted: {results['performance_summary']['sites_attempted']}")
        print(f"Sites Successful: {results['performance_summary']['sites_successful']}")
        print(f"Success Rate: {results['performance_summary']['success_rate']}%")
        print(f"Average Response Time: {results['performance_summary']['average_response_time']}s")
        print(f"Total Content Items: {results['performance_summary']['total_content_items_extracted']}")
        print(f"Average Mining Relevance: {results['performance_summary']['average_mining_relevance']}/10")
        
        print(f"\nDATA QUALITY DISTRIBUTION")
        print("-" * 30)
        for quality, count in results['performance_summary']['data_quality_distribution'].items():
            print(f"  {quality}: {count} sites")
        
        print(f"\nAGGREGATED DATA SUMMARY")
        print("-" * 30)
        print(f"Economic Indicators: {len(results['aggregated_data']['economic_indicators'])}")
        print(f"Commodity Analysis Items: {len(results['aggregated_data']['commodity_analysis'])}")
        print(f"Economic News Items: {len(results['aggregated_data']['canadian_economic_news'])}")
        print(f"High-Relevance Mining Insights: {len(results['aggregated_data']['mining_relevant_insights'])}")
        
        print(f"\nDETAILED SITE PERFORMANCE")
        print("-" * 40)
        for site_key, site_result in results['site_results'].items():
            print(f"\n{site_result.get('site_name', site_key)}:")
            print(f"  Success: {site_result.get('success', False)}")
            print(f"  Response Time: {site_result.get('response_time', 0):.1f}s")
            print(f"  Content Length: {site_result.get('content_length', 0):,} chars")
            print(f"  Word Count: {site_result.get('word_count', 0):,}")
            print(f"  Data Quality: {site_result.get('data_quality', 'unknown')}")
            print(f"  Mining Relevance: {site_result.get('mining_relevance', 0)}/10")
            print(f"  Content Items: {site_result.get('content_items_extracted', 0)}")
            if not site_result.get('success') and 'error' in site_result:
                print(f"  Error: {site_result['error']}")
        
        # Show some sample extracted data
        if results['aggregated_data']['economic_indicators']:
            print(f"\nSAMPLE ECONOMIC INDICATORS")
            print("-" * 35)
            for indicator in results['aggregated_data']['economic_indicators'][:5]:
                print(f"  {indicator.get('indicator_name', 'Unknown')}: {indicator.get('current_value', 'N/A')}")
        
        if results['aggregated_data']['mining_relevant_insights']:
            print(f"\nSAMPLE MINING INSIGHTS")
            print("-" * 25)
            for insight in results['aggregated_data']['mining_relevant_insights'][:3]:
                source = insight.get('source', 'Unknown')
                relevance = insight.get('relevance_score', 0)
                print(f"  Source: {source} (Relevance: {relevance}/10)")
                for key_insight in insight.get('key_insights', [])[:2]:
                    print(f"    - {key_insight[:100]}...")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    main()