#!/usr/bin/env python3
"""
Enhanced Economics Data Scraper for August 4, 2025
Improved version with better text extraction and anti-bot measures
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
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedHTMLParser(HTMLParser):
    """Enhanced HTML parser with better text extraction"""
    
    def __init__(self):
        super().__init__()
        self.content = []
        self.current_text = ""
        self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'meta', 'link'}
        self.in_skip_tag = False
        self.skip_depth = 0
        
        # Table extraction
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        
        # Structure tracking
        self.headings = []
        self.in_heading = False
        self.heading_level = 0
    
    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        
        if tag_lower in self.skip_tags:
            self.in_skip_tag = True
            self.skip_depth = 1
        elif self.in_skip_tag:
            self.skip_depth += 1
        elif tag_lower == 'table':
            self.in_table = True
            self.current_table = []
        elif tag_lower == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag_lower in ['td', 'th'] and self.in_row:
            self.in_cell = True
            self.current_cell = ""
        elif tag_lower in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = True
            self.heading_level = int(tag_lower[1])
    
    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        
        if tag_lower in self.skip_tags:
            self.skip_depth -= 1
            if self.skip_depth <= 0:
                self.in_skip_tag = False
                self.skip_depth = 0
        elif tag_lower == 'table':
            self.in_table = False
            if self.current_table:
                self.tables.append(self.current_table)
        elif tag_lower == 'tr' and self.in_table:
            self.in_row = False
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag_lower in ['td', 'th'] and self.in_row:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
        elif tag_lower in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = False
            if self.current_text.strip():
                self.headings.append({
                    'level': self.heading_level,
                    'text': self.current_text.strip()
                })
                self.current_text = ""
    
    def handle_data(self, data):
        if not self.in_skip_tag:
            clean_data = data.strip()
            if clean_data:
                if self.in_cell:
                    self.current_cell += " " + clean_data
                elif self.in_heading:
                    self.current_text += " " + clean_data
                else:
                    self.content.append(clean_data)
    
    def get_text(self):
        """Get all text content, properly cleaned"""
        all_text = ' '.join([text for text in self.content if text and len(text.strip()) > 0])
        # Clean up whitespace
        all_text = re.sub(r'\s+', ' ', all_text)
        return all_text.strip()
    
    def get_tables(self):
        """Get all extracted tables"""
        return self.tables
    
    def get_headings(self):
        """Get all extracted headings"""
        return self.headings

class EnhancedEconomicsScraper:
    """Enhanced economics scraper with better extraction and anti-bot measures"""
    
    def __init__(self):
        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Economics websites configuration with enhanced extraction rules
        self.economics_targets = {
            "trading_economics_canada": {
                "name": "Trading Economics Canada",
                "url": "https://tradingeconomics.com/canada/indicators",
                "type": "economic_indicators",
                "retry_count": 3,
                "timeout": 30
            },
            "rbc_economic_analysis": {
                "name": "RBC Economic Analysis",
                "url": "https://www.rbc.com/en/thought-leadership/economics/forward-guidance-our-weekly-preview/",
                "type": "economic_analysis",
                "retry_count": 2,
                "timeout": 20
            },
            "investing_commodities_analysis": {
                "name": "Investing.com Commodities Analysis",
                "url": "https://ca.investing.com/analysis/commodities",
                "type": "commodity_analysis",
                "retry_count": 3,
                "timeout": 30
            },
            "investing_commodities_news": {
                "name": "Investing.com Commodities News",
                "url": "https://ca.investing.com/news/commodities-news",
                "type": "commodity_news",
                "retry_count": 3,
                "timeout": 30
            }
        }
        
        # Enhanced keywords for better relevance scoring
        self.mining_keywords = [
            "mining", "mine", "miner", "exploration", "drilling", "ore", "deposit", "resource",
            "reserve", "production", "extraction", "processing", "smelting", "refining",
            "gold", "silver", "copper", "platinum", "palladium", "nickel", "zinc", "lead",
            "iron ore", "aluminum", "tin", "uranium", "lithium", "cobalt", "rare earth",
            "commodity", "commodities", "metals", "precious metals", "base metals"
        ]
        
        self.economic_indicators = [
            "gdp", "gross domestic product", "inflation", "cpi", "consumer price index",
            "ppi", "producer price index", "interest rate", "employment", "unemployment",
            "manufacturing", "industrial production", "trade balance", "current account",
            "business investment", "consumer spending", "retail sales", "housing starts",
            "building permits", "capacity utilization"
        ]
        
        self.canadian_keywords = [
            "canada", "canadian", "bank of canada", "boc", "statistics canada", "statscan",
            "toronto", "ontario", "quebec", "british columbia", "alberta", "saskatchewan",
            "manitoba", "nova scotia", "new brunswick", "newfoundland", "yukon", "northwest territories"
        ]
        
        # Economic indicator patterns for extraction
        self.indicator_patterns = {
            "GDP Growth": [
                r"gdp.*?growth.*?([+-]?\d+\.?\d*%?)",
                r"gross domestic product.*?([+-]?\d+\.?\d*%?)",
                r"economic growth.*?([+-]?\d+\.?\d*%?)"
            ],
            "Inflation Rate": [
                r"inflation.*?rate.*?([+-]?\d+\.?\d*%?)",
                r"cpi.*?([+-]?\d+\.?\d*%?)",
                r"consumer price.*?([+-]?\d+\.?\d*%?)"
            ],
            "Interest Rate": [
                r"interest rate.*?([+-]?\d+\.?\d*%?)",
                r"policy rate.*?([+-]?\d+\.?\d*%?)",
                r"overnight rate.*?([+-]?\d+\.?\d*%?)"
            ],
            "Unemployment Rate": [
                r"unemployment.*?rate.*?([+-]?\d+\.?\d*%?)",
                r"jobless.*?rate.*?([+-]?\d+\.?\d*%?)"
            ],
            "CAD Exchange Rate": [
                r"cad.*?usd.*?([+-]?\d+\.?\d*)",
                r"canadian dollar.*?([+-]?\d+\.?\d*)",
                r"loonie.*?([+-]?\d+\.?\d*)"
            ]
        }
    
    def scrape_all_economics_sites(self):
        """Scrape all economics websites with enhanced error handling"""
        
        logger.info("Starting enhanced economics data scraping for August 4, 2025")
        
        start_time = time.time()
        results = {
            "scraping_session": {
                "date": datetime.now().isoformat(),
                "purpose": "Enhanced economics data collection for mining intelligence",
                "target_sites": 4,
                "focus": "Canadian economic data, commodity forecasts, mining sector analysis",
                "method": "Enhanced HTTP scraping with anti-bot measures",
                "improvements": [
                    "Better text encoding handling",
                    "User agent rotation",
                    "Enhanced content extraction",
                    "Structured economic indicator parsing",
                    "Improved error handling and retries"
                ]
            },
            "site_results": {},
            "performance_summary": {},
            "aggregated_data": {
                "economic_indicators": [],
                "commodity_analysis": [],
                "canadian_economic_news": [],
                "mining_relevant_insights": [],
                "extracted_headings": [],
                "key_economic_metrics": []
            }
        }
        
        # Process each target site with enhanced error handling
        for site_key, site_config in self.economics_targets.items():
            logger.info(f"Scraping {site_config['name']} - {site_config['url']}")
            
            site_start_time = time.time()
            site_result = None
            
            # Retry logic with exponential backoff
            for attempt in range(site_config.get('retry_count', 2)):
                try:
                    site_result = self._scrape_economics_site_enhanced(site_key, site_config, attempt + 1)
                    break
                except Exception as e:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Attempt {attempt + 1} failed for {site_config['name']}: {str(e)}")
                    if attempt < site_config.get('retry_count', 2) - 1:
                        logger.info(f"Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                    else:
                        site_result = {
                            "site_name": site_config["name"],
                            "url": site_config["url"],
                            "success": False,
                            "error": f"All {site_config.get('retry_count', 2)} attempts failed. Last error: {str(e)}",
                            "attempts_made": attempt + 1
                        }
            
            if site_result:
                site_result["response_time"] = time.time() - site_start_time
                site_result["timestamp"] = datetime.now().isoformat()
                results["site_results"][site_key] = site_result
                
                # Add to aggregated data
                if site_result.get("success", False):
                    self._aggregate_site_data_enhanced(site_result, results["aggregated_data"])
                
                logger.info(f"Completed {site_config['name']} in {site_result['response_time']:.1f}s")
            
            # Rate limiting with jitter
            sleep_time = random.uniform(2, 4)
            time.sleep(sleep_time)
        
        # Generate enhanced performance summary
        results["performance_summary"] = self._generate_performance_summary_enhanced(results["site_results"])
        results["total_scraping_time"] = time.time() - start_time
        
        # Save results
        os.makedirs("reports/2025-08-04", exist_ok=True)
        output_file = "reports/2025-08-04/enhanced_economics_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Enhanced economics data scraping completed in {results['total_scraping_time']:.1f}s")
        logger.info(f"Results saved to {output_file}")
        
        return results
    
    def _scrape_economics_site_enhanced(self, site_key, site_config, attempt_number):
        """Enhanced site scraping with better extraction"""
        
        site_result = {
            "site_name": site_config["name"],
            "url": site_config["url"],
            "content_type": site_config["type"],
            "success": False,
            "scraper_used": "enhanced_urllib+htmlparser",
            "attempt_number": attempt_number,
            "content_length": 0,
            "word_count": 0,
            "economics_content": [],
            "extracted_headings": [],
            "data_quality": "unknown",
            "mining_relevance": 0
        }
        
        # Create request with rotating user agent and enhanced headers
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Add referer for some sites
        if 'investing.com' in site_config["url"]:
            headers['Referer'] = 'https://ca.investing.com/'
        
        request = Request(site_config["url"], headers=headers)
        
        # Make HTTP request with timeout
        with urlopen(request, timeout=site_config.get('timeout', 30)) as response:
            # Handle different encodings
            encoding = response.headers.get_content_charset() or 'utf-8'
            html_content = response.read().decode(encoding, errors='replace')
        
        # Parse HTML with enhanced parser
        parser = EnhancedHTMLParser()
        parser.feed(html_content)
        
        text_content = parser.get_text()
        tables = parser.get_tables()
        headings = parser.get_headings()
        
        if len(text_content) < 100:
            raise Exception("Insufficient content extracted")
        
        site_result["content_length"] = len(text_content)
        site_result["word_count"] = len(text_content.split())
        site_result["extracted_headings"] = headings
        site_result["success"] = True
        
        # Enhanced content extraction
        economics_content = self._extract_economics_content_enhanced(
            text_content, tables, headings, site_config
        )
        
        site_result["economics_content"] = economics_content
        site_result["content_items_extracted"] = len(economics_content)
        
        # Enhanced quality assessment
        site_result["data_quality"] = self._assess_data_quality_enhanced(
            economics_content, text_content, headings
        )
        site_result["mining_relevance"] = self._calculate_mining_relevance_enhanced(
            text_content, economics_content
        )
        
        return site_result
    
    def _extract_economics_content_enhanced(self, text_content, tables, headings, site_config):
        """Enhanced economics content extraction"""
        
        economics_content = []
        
        # Extract economic indicators using pattern matching
        if site_config["type"] == "economic_indicators":
            indicators = self._extract_economic_indicators_enhanced(text_content, tables)
            if indicators:
                economics_content.append({
                    "title": "Canadian Economic Indicators",
                    "type": "indicators",
                    "data_points": indicators,
                    "extraction_method": "pattern_matching_and_tables",
                    "mining_relevance": self._calculate_mining_relevance_enhanced(text_content, [])
                })
        
        # Extract analysis content with better structure recognition
        analysis_sections = self._extract_analysis_sections(text_content, headings)
        for section in analysis_sections:
            if section["relevance_score"] > 0:
                economics_content.append(section)
        
        # Extract commodity mentions with context
        commodity_insights = self._extract_commodity_insights_enhanced(text_content)
        if commodity_insights:
            economics_content.append({
                "title": "Commodity Market Insights",
                "type": "commodity_analysis",
                "insights": commodity_insights,
                "extraction_method": "contextual_commodity_analysis",
                "mining_relevance": len(commodity_insights) * 2
            })
        
        return economics_content
    
    def _extract_economic_indicators_enhanced(self, text_content, tables):
        """Enhanced economic indicator extraction"""
        
        indicators = []
        
        # Extract from tables first
        for table in tables:
            if len(table) > 1:  # Has header and data rows
                for row in table[1:]:  # Skip header
                    if len(row) >= 2:
                        indicator_name = row[0].strip()
                        current_value = row[1].strip()
                        change = row[2].strip() if len(row) > 2 else ""
                        
                        # Filter for meaningful indicators
                        if (indicator_name and current_value and 
                            any(keyword in indicator_name.lower() for keyword in self.economic_indicators)):
                            
                            indicators.append({
                                "indicator_name": indicator_name,
                                "current_value": current_value,
                                "change": change,
                                "source": "Trading Economics Canada",
                                "extraction_method": "table_parsing",
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
        
        # Extract using pattern matching
        for indicator_name, patterns in self.indicator_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    for match in matches[:1]:  # Take first match
                        indicators.append({
                            "indicator_name": indicator_name,
                            "current_value": match,
                            "source": "Trading Economics Canada",
                            "extraction_method": "pattern_matching",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
        
        return indicators
    
    def _extract_analysis_sections(self, text_content, headings):
        """Extract analysis sections based on headings and content structure"""
        
        sections = []
        
        # Split content by headings
        text_parts = re.split(r'\n\s*\n', text_content)
        
        for i, part in enumerate(text_parts):
            if len(part.strip()) < 100:  # Skip short sections
                continue
            
            # Calculate relevance
            relevance_score = self._calculate_mining_relevance_enhanced(part, [])
            
            if relevance_score > 0:
                # Extract key insights from this section
                insights = self._extract_key_insights_enhanced(part)
                commodity_mentions = self._extract_commodity_mentions_enhanced(part)
                
                sections.append({
                    "title": f"Economic Analysis Section {i+1}",
                    "type": "analysis",
                    "content_preview": part[:300] + "...",
                    "key_insights": insights,
                    "commodity_mentions": commodity_mentions,
                    "canadian_focus": any(keyword in part.lower() for keyword in self.canadian_keywords),
                    "relevance_score": relevance_score,
                    "word_count": len(part.split())
                })
        
        return sections
    
    def _extract_key_insights_enhanced(self, content):
        """Enhanced key insight extraction with better filtering"""
        
        insights = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
            
            # Enhanced relevance scoring
            relevance_score = 0
            
            # Mining keywords (high weight)
            mining_matches = sum(1 for keyword in self.mining_keywords if keyword.lower() in sentence.lower())
            relevance_score += mining_matches * 2
            
            # Economic indicators (medium weight)
            economic_matches = sum(1 for keyword in self.economic_indicators if keyword.lower() in sentence.lower())
            relevance_score += economic_matches * 1.5
            
            # Canadian keywords (low weight)
            canadian_matches = sum(1 for keyword in self.canadian_keywords if keyword.lower() in sentence.lower())
            relevance_score += canadian_matches * 0.5
            
            # Numeric data bonus
            if re.search(r'\d+\.?\d*%?', sentence):
                relevance_score += 1
            
            if relevance_score >= 1.5:
                insights.append({
                    "text": sentence,
                    "relevance_score": relevance_score,
                    "contains_numeric_data": bool(re.search(r'\d+\.?\d*%?', sentence))
                })
            
            if len(insights) >= 15:  # Limit insights per section
                break
        
        # Sort by relevance and return top insights
        insights.sort(key=lambda x: x["relevance_score"], reverse=True)
        return [insight["text"] for insight in insights[:10]]
    
    def _extract_commodity_mentions_enhanced(self, content):
        """Enhanced commodity mention extraction with better context"""
        
        commodities = {
            "gold": ["gold", "au", "yellow metal"],
            "silver": ["silver", "ag", "white metal"],
            "copper": ["copper", "cu", "red metal"],
            "oil": ["oil", "crude", "petroleum", "wti", "brent"],
            "natural gas": ["natural gas", "gas", "lng"],
            "iron ore": ["iron ore", "iron", "fe"],
            "nickel": ["nickel", "ni"],
            "zinc": ["zinc", "zn"],
            "aluminum": ["aluminum", "aluminium", "al"],
            "uranium": ["uranium", "u3o8"]
        }
        
        mentions = []
        content_lower = content.lower()
        
        for commodity, variants in commodities.items():
            for variant in variants:
                if variant in content_lower:
                    # Find sentences containing the commodity
                    pattern = rf'[^.!?]*\b{re.escape(variant)}\b[^.!?]*[.!?]'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for match in matches[:2]:  # Limit matches per commodity
                        clean_match = re.sub(r'\s+', ' ', match.strip())
                        if len(clean_match) > 20:  # Only meaningful mentions
                            mentions.append({
                                "commodity": commodity,
                                "context": clean_match,
                                "variant_found": variant
                            })
                    
                    if mentions:  # Found matches for this commodity, move to next
                        break
        
        return mentions
    
    def _extract_commodity_insights_enhanced(self, text_content):
        """Extract commodity-specific insights with enhanced context"""
        
        insights = []
        
        # Look for price movements and forecasts
        price_patterns = [
            r'(gold|silver|copper|oil|gas|iron ore|nickel|zinc|aluminum|uranium).*?(up|down|rise|fall|increase|decrease|rally|decline).*?(\d+\.?\d*%?)',
            r'(gold|silver|copper|oil|gas|iron ore|nickel|zinc|aluminum|uranium).*?(price|trading|valued).*?(\$\d+\.?\d*)',
            r'(bullish|bearish|outlook|forecast).*?(gold|silver|copper|oil|gas|iron ore|nickel|zinc|aluminum|uranium)'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                insight_text = ' '.join(match)
                if len(insight_text) > 10:
                    insights.append({
                        "type": "price_movement",
                        "text": insight_text,
                        "pattern_matched": pattern
                    })
        
        return insights[:10]  # Limit insights
    
    def _calculate_mining_relevance_enhanced(self, content, economics_content):
        """Enhanced mining relevance calculation"""
        
        content_lower = content.lower()
        score = 0
        
        # Direct mining keywords (high weight)
        mining_mentions = sum(1 for keyword in self.mining_keywords if keyword in content_lower)
        score += min(mining_mentions * 2, 8)
        
        # Economic indicators affecting mining (medium weight)
        economic_mentions = sum(1 for keyword in self.economic_indicators if keyword in content_lower)
        score += min(economic_mentions * 0.5, 3)
        
        # Canadian focus (mining is important to Canada)
        canadian_mentions = sum(1 for keyword in self.canadian_keywords if keyword in content_lower)
        score += min(canadian_mentions * 0.3, 2)
        
        # Commodity price mentions
        commodity_price_mentions = len(re.findall(r'(gold|silver|copper|oil|gas|iron|nickel|zinc|aluminum|uranium).*?(price|\$)', content_lower))
        score += min(commodity_price_mentions * 1.5, 4)
        
        # TSX/mining company mentions
        tsx_mentions = len(re.findall(r'(tsx|tsxv|mining.+company|resource.+company)', content_lower))
        score += min(tsx_mentions * 2, 3)
        
        return min(int(score), 10)
    
    def _assess_data_quality_enhanced(self, economics_content, text_content, headings):
        """Enhanced data quality assessment"""
        
        if not economics_content and len(text_content) < 500:
            return "poor"
        
        quality_score = 0
        
        # Content extraction success
        total_insights = sum(len(item.get("key_insights", [])) for item in economics_content)
        total_data_points = sum(len(item.get("data_points", [])) for item in economics_content)
        
        quality_score += min(total_data_points * 2, 6)
        quality_score += min(total_insights * 0.5, 4)
        
        # Structure recognition
        if headings:
            quality_score += min(len(headings) * 0.5, 2)
        
        # Content richness
        if len(text_content) > 5000:
            quality_score += 2
        elif len(text_content) > 1000:
            quality_score += 1
        
        # Numeric data presence
        numeric_matches = len(re.findall(r'\d+\.?\d*%?', text_content))
        quality_score += min(numeric_matches * 0.1, 2)
        
        if quality_score >= 8:
            return "excellent"
        elif quality_score >= 6:
            return "good"
        elif quality_score >= 3:
            return "fair"
        else:
            return "poor"
    
    def _aggregate_site_data_enhanced(self, site_result, aggregated_data):
        """Enhanced data aggregation"""
        
        if not site_result.get("success", False) or not site_result.get("economics_content"):
            return
        
        # Add headings to aggregated data
        if site_result.get("extracted_headings"):
            aggregated_data["extracted_headings"].extend([
                {
                    "source": site_result["site_name"],
                    "heading": heading["text"],
                    "level": heading["level"]
                }
                for heading in site_result["extracted_headings"]
            ])
        
        for content_item in site_result["economics_content"]:
            if content_item.get("type") == "indicators":
                aggregated_data["economic_indicators"].extend(content_item.get("data_points", []))
                
                # Add to key metrics
                for indicator in content_item.get("data_points", []):
                    aggregated_data["key_economic_metrics"].append({
                        "source": site_result["site_name"],
                        "indicator": indicator.get("indicator_name"),
                        "value": indicator.get("current_value"),
                        "change": indicator.get("change", ""),
                        "date": indicator.get("date")
                    })
            
            elif content_item.get("type") in ["analysis", "commodity_analysis"]:
                aggregated_data["commodity_analysis"].append({
                    "source": site_result["site_name"],
                    "title": content_item.get("title", ""),
                    "key_insights": content_item.get("key_insights", []),
                    "commodity_mentions": content_item.get("commodity_mentions", []),
                    "mining_relevance": content_item.get("mining_relevance", 0),
                    "canadian_focus": content_item.get("canadian_focus", False)
                })
                
                # Add to Canadian economic news if relevant
                if content_item.get("canadian_focus"):
                    aggregated_data["canadian_economic_news"].append({
                        "source": site_result["site_name"],
                        "title": content_item.get("title", ""),
                        "key_insights": content_item.get("key_insights", [])[:3],
                        "canadian_focus": True
                    })
                
                # Add high-relevance content to mining insights
                if content_item.get("mining_relevance", 0) >= 4:
                    aggregated_data["mining_relevant_insights"].append({
                        "source": site_result["site_name"],
                        "title": content_item.get("title", ""),
                        "key_insights": content_item.get("key_insights", [])[:3],
                        "commodity_mentions": content_item.get("commodity_mentions", [])[:3],
                        "relevance_score": content_item.get("mining_relevance", 0)
                    })
    
    def _generate_performance_summary_enhanced(self, site_results):
        """Enhanced performance summary generation"""
        
        total_sites = len(site_results)
        successful_sites = sum(1 for result in site_results.values() if result.get("success", False))
        
        avg_response_time = sum(result.get("response_time", 0) for result in site_results.values()) / total_sites
        
        total_content_items = sum(result.get("content_items_extracted", 0) for result in site_results.values())
        total_headings = sum(len(result.get("extracted_headings", [])) for result in site_results.values())
        
        quality_distribution = {}
        for result in site_results.values():
            quality = result.get("data_quality", "unknown")
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        mining_relevance_scores = [result.get("mining_relevance", 0) for result in site_results.values() if result.get("success")]
        avg_mining_relevance = sum(mining_relevance_scores) / len(mining_relevance_scores) if mining_relevance_scores else 0
        
        # Calculate retry statistics
        total_attempts = sum(result.get("attempt_number", 1) for result in site_results.values())
        retry_rate = ((total_attempts - total_sites) / total_sites) * 100 if total_sites > 0 else 0
        
        return {
            "sites_attempted": total_sites,
            "sites_successful": successful_sites,
            "success_rate": round((successful_sites / total_sites) * 100, 1),
            "average_response_time": round(avg_response_time, 2),
            "total_content_items_extracted": total_content_items,
            "total_headings_extracted": total_headings,
            "data_quality_distribution": quality_distribution,
            "average_mining_relevance": round(avg_mining_relevance, 1),
            "retry_rate": round(retry_rate, 1),
            "total_attempts_made": total_attempts,
            "scrapers_used": ["enhanced_urllib+htmlparser"],
            "enhancements_applied": [
                "User agent rotation",
                "Enhanced text encoding",
                "Structured content extraction",
                "Pattern-based indicator extraction",
                "Improved relevance scoring",
                "Retry logic with exponential backoff"
            ]
        }

def main():
    """Main function to run the enhanced economics data scraper"""
    
    print("Starting Enhanced Economics Data Scraper for August 4, 2025")
    print("=" * 65)
    print("Enhancements: Better text extraction, anti-bot measures, structured parsing")
    print()
    
    scraper = EnhancedEconomicsScraper()
    
    try:
        results = scraper.scrape_all_economics_sites()
        
        print(f"\nENHANCED SCRAPING RESULTS SUMMARY")
        print("=" * 45)
        perf = results['performance_summary']
        print(f"Sites Attempted: {perf['sites_attempted']}")
        print(f"Sites Successful: {perf['sites_successful']}")
        print(f"Success Rate: {perf['success_rate']}%")
        print(f"Average Response Time: {perf['average_response_time']}s")
        print(f"Total Content Items: {perf['total_content_items_extracted']}")
        print(f"Total Headings Extracted: {perf['total_headings_extracted']}")
        print(f"Average Mining Relevance: {perf['average_mining_relevance']}/10")
        print(f"Retry Rate: {perf['retry_rate']}%")
        
        print(f"\nDATA QUALITY DISTRIBUTION")
        print("-" * 30)
        for quality, count in perf['data_quality_distribution'].items():
            print(f"  {quality}: {count} sites")
        
        print(f"\nAGGREGATED DATA SUMMARY")
        print("-" * 30)
        agg = results['aggregated_data']
        print(f"Economic Indicators: {len(agg['economic_indicators'])}")
        print(f"Key Economic Metrics: {len(agg['key_economic_metrics'])}")
        print(f"Commodity Analysis Items: {len(agg['commodity_analysis'])}")
        print(f"Economic News Items: {len(agg['canadian_economic_news'])}")
        print(f"High-Relevance Mining Insights: {len(agg['mining_relevant_insights'])}")
        print(f"Extracted Headings: {len(agg['extracted_headings'])}")
        
        # Show sample extracted indicators
        if agg['economic_indicators']:
            print(f"\nSAMPLE ECONOMIC INDICATORS")
            print("-" * 35)
            for indicator in agg['economic_indicators'][:5]:
                name = indicator.get('indicator_name', 'Unknown')
                value = indicator.get('current_value', 'N/A')
                method = indicator.get('extraction_method', 'unknown')
                print(f"  {name}: {value} ({method})")
        
        # Show sample mining insights
        if agg['mining_relevant_insights']:
            print(f"\nSAMPLE MINING INSIGHTS")
            print("-" * 25)
            for insight in agg['mining_relevant_insights'][:3]:
                source = insight.get('source', 'Unknown')
                relevance = insight.get('relevance_score', 0)
                print(f"  Source: {source} (Relevance: {relevance}/10)")
                for key_insight in insight.get('key_insights', [])[:1]:
                    print(f"    - {key_insight[:120]}...")
        
        print(f"\nENHANCEMENTS APPLIED")
        print("-" * 25)
        for enhancement in perf['enhancements_applied']:
            print(f"  ✓ {enhancement}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during enhanced scraping: {str(e)}")
        raise

if __name__ == "__main__":
    main()