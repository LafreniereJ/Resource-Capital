#!/usr/bin/env python3
"""
Pattern-Based Enhanced Data Extractor
Uses advanced regex patterns and NLP techniques to extract structured data
without requiring external LLM APIs
"""

import asyncio
import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from crawl4ai import AsyncWebCrawler
import logging
from ..core.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FinancialData:
    """Structured financial information"""
    revenue: Optional[float] = None
    revenue_period: Optional[str] = None
    ebitda: Optional[float] = None
    cash_flow: Optional[float] = None
    net_income: Optional[float] = None
    guidance_revenue: Optional[str] = None
    guidance_production: Optional[str] = None
    dividend_amount: Optional[float] = None
    share_price: Optional[float] = None
    currency: str = "CAD"

@dataclass
class OperationalData:
    """Structured operational information"""
    production_volume: Optional[float] = None
    production_unit: Optional[str] = None
    production_period: Optional[str] = None
    cash_cost: Optional[float] = None
    all_in_cost: Optional[float] = None
    grade: Optional[float] = None
    recovery_rate: Optional[float] = None
    reserves: Optional[float] = None
    resources: Optional[float] = None

@dataclass
class NewsItem:
    """Structured news item"""
    title: str
    date: str
    content: str
    category: str
    relevance_score: int
    key_points: List[str]
    financial_impact: Optional[str] = None
    url: str = ""

class PatternBasedExtractor:
    """Enhanced data extraction using pattern matching and NLP"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup extraction patterns for different data types"""
        
        # Financial number patterns
        self.financial_patterns = {
            'revenue': [
                r'revenue[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'sales[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'total revenue.*?([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
            ],
            'ebitda': [
                r'ebitda[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'adjusted ebitda[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
            ],
            'cash_flow': [
                r'cash flow[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'operating cash flow[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'free cash flow[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
            ],
            'net_income': [
                r'net (?:income|earnings)[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
                r'net profit[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion|M|B)',
            ],
            'dividend': [
                r'dividend[^$]*\$([0-9]+(?:\.[0-9]+)?)',
                r'quarterly dividend[^$]*\$([0-9]+(?:\.[0-9]+)?)',
            ]
        }
        
        # Production patterns
        self.production_patterns = {
            'production_volume': [
                r'production[^0-9]*([0-9,]+(?:\.[0-9]+)?)\s*(ounces|tonnes|tons|barrels|pounds)',
                r'produced[^0-9]*([0-9,]+(?:\.[0-9]+)?)\s*(ounces|tonnes|tons|barrels|pounds)',
                r'output[^0-9]*([0-9,]+(?:\.[0-9]+)?)\s*(ounces|tonnes|tons|barrels|pounds)',
            ],
            'cash_cost': [
                r'cash cost[^$]*\$([0-9,]+(?:\.[0-9]+)?)',
                r'total cash cost[^$]*\$([0-9,]+(?:\.[0-9]+)?)',
            ],
            'all_in_cost': [
                r'all-in sustaining cost[^$]*\$([0-9,]+(?:\.[0-9]+)?)',
                r'aisc[^$]*\$([0-9,]+(?:\.[0-9]+)?)',
            ],
            'grade': [
                r'grade[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:g/t|oz/t|%)',
                r'average grade[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:g/t|oz/t|%)',
            ],
            'reserves': [
                r'proven and probable reserves[^0-9]*([0-9,]+(?:\.[0-9]+)?)',
                r'total reserves[^0-9]*([0-9,]+(?:\.[0-9]+)?)',
                r'reserves[^0-9]*([0-9,]+(?:\.[0-9]+)?)\s*(?:million|M)?\s*(?:ounces|tonnes|tons)',
            ]
        }
        
        # Date patterns
        self.date_patterns = [
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'q[1-4]\s+\d{4}',
            r'\d{4}\s+q[1-4]'
        ]
        
        # News category patterns
        self.category_patterns = {
            'earnings': [
                r'earnings', r'quarterly results', r'financial results',
                r'q[1-4].*results', r'annual results'
            ],
            'operational': [
                r'production', r'mining', r'operational', r'mill',
                r'processing', r'operations'
            ],
            'corporate': [
                r'acquisition', r'merger', r'takeover', r'appointment',
                r'resignation', r'board', r'leadership'
            ],
            'exploration': [
                r'exploration', r'drilling', r'discovery', r'resource',
                r'reserve', r'assay', r'mineral'
            ],
            'guidance': [
                r'guidance', r'outlook', r'forecast', r'projection',
                r'expects', r'anticipates'
            ]
        }

    def extract_financial_data(self, content: str) -> FinancialData:
        """Extract financial metrics from content"""
        
        financial_data = FinancialData()
        content_lower = content.lower()
        
        for metric, patterns in self.financial_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    try:
                        # Convert string to float, handle commas
                        value_str = matches[0].replace(',', '')
                        value = float(value_str)
                        
                        # Convert millions/billions to actual numbers
                        if 'billion' in pattern or 'B' in pattern:
                            value = value * 1000  # Store in millions
                        
                        setattr(financial_data, metric, value)
                        logger.debug(f"Extracted {metric}: {value}")
                        break  # Use first match
                        
                    except (ValueError, IndexError):
                        continue
        
        return financial_data

    def extract_operational_data(self, content: str) -> OperationalData:
        """Extract operational metrics from content"""
        
        operational_data = OperationalData()
        content_lower = content.lower()
        
        for metric, patterns in self.production_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    try:
                        if metric == 'production_volume':
                            # Handle tuple (value, unit)
                            if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                                value_str, unit = matches[0]
                                value = float(value_str.replace(',', ''))
                                operational_data.production_volume = value
                                operational_data.production_unit = unit
                            else:
                                value_str = matches[0].replace(',', '')
                                value = float(value_str)
                                setattr(operational_data, metric, value)
                        else:
                            value_str = matches[0].replace(',', '')
                            value = float(value_str)
                            setattr(operational_data, metric, value)
                        
                        logger.debug(f"Extracted {metric}: {value}")
                        break
                        
                    except (ValueError, IndexError, TypeError):
                        continue
        
        return operational_data

    def extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        # Standardize date formats
        standardized_dates = []
        for date_str in dates:
            try:
                # Try different parsing approaches
                standardized_date = self.standardize_date(date_str)
                if standardized_date:
                    standardized_dates.append(standardized_date)
            except:
                continue
        
        return list(set(standardized_dates))  # Remove duplicates

    def standardize_date(self, date_str: str) -> Optional[str]:
        """Convert various date formats to YYYY-MM-DD"""
        
        date_str = date_str.strip().lower()
        
        # Month name patterns
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        try:
            # Handle "January 15, 2024" format
            for month_name, month_num in months.items():
                if month_name in date_str:
                    parts = re.findall(r'\d+', date_str)
                    if len(parts) >= 2:
                        day = parts[0].zfill(2)
                        year = parts[-1]
                        return f"{year}-{month_num}-{day}"
            
            # Handle MM/DD/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            
            # Handle YYYY-MM-DD (already standard)
            if re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
                parts = date_str.split('-')
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            
            # Handle Q1 2024 format
            quarter_match = re.search(r'q([1-4])\s+(\d{4})', date_str)
            if quarter_match:
                quarter = int(quarter_match.group(1))
                year = quarter_match.group(2)
                month = (quarter - 1) * 3 + 1  # Q1=Jan, Q2=Apr, etc.
                return f"{year}-{month:02d}-01"
                
        except:
            pass
        
        return None

    def categorize_content(self, content: str, title: str = "") -> str:
        """Categorize content based on keywords"""
        
        combined_text = (content + " " + title).lower()
        
        # Score each category
        category_scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                score += matches
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
            if category_scores[best_category] > 0:
                return best_category
        
        return "general"

    def calculate_relevance_score(self, content: str, title: str, 
                                financial_data: FinancialData, 
                                operational_data: OperationalData) -> int:
        """Calculate relevance score for content"""
        
        score = 0
        combined_text = (content + " " + title).lower()
        
        # Financial data points
        if financial_data.revenue:
            score += 25
        if financial_data.ebitda:
            score += 20
        if financial_data.guidance_revenue or financial_data.guidance_production:
            score += 30
        if financial_data.cash_flow:
            score += 15
        if financial_data.dividend_amount:
            score += 10
        
        # Operational data points
        if operational_data.production_volume:
            score += 20
        if operational_data.cash_cost or operational_data.all_in_cost:
            score += 15
        if operational_data.reserves or operational_data.resources:
            score += 10
        
        # Keyword relevance
        high_value_keywords = [
            'earnings', 'guidance', 'dividend', 'acquisition', 'merger',
            'production record', 'major discovery', 'resource estimate'
        ]
        
        for keyword in high_value_keywords:
            if keyword in combined_text:
                score += 10
        
        # Recent content bonus
        dates = self.extract_dates(content)
        recent_cutoff = datetime.now() - timedelta(days=30)
        
        for date_str in dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if date_obj > recent_cutoff:
                    score += 15
                    break
            except:
                continue
        
        return min(score, 100)  # Cap at 100

    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extract key bullet points from content"""
        
        key_points = []
        
        # Look for existing bullet points
        bullet_patterns = [
            r'[•\-\*]\s*([^•\-\*\n]{20,200})',
            r'(?:^|\n)\s*\d+\.\s*([^0-9\n]{20,200})',
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            key_points.extend([match.strip() for match in matches])
        
        # If no bullet points found, extract important sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', content)
            important_keywords = [
                'revenue', 'earnings', 'production', 'guidance', 'expects',
                'announced', 'reported', 'achieved', 'record', 'increased',
                'decreased', 'million', 'billion'
            ]
            
            for sentence in sentences:
                sentence = sentence.strip()
                if (len(sentence) > 30 and len(sentence) < 200 and
                    any(keyword in sentence.lower() for keyword in important_keywords)):
                    key_points.append(sentence)
        
        # Return top points, deduplicated
        unique_points = []
        for point in key_points[:max_points * 2]:  # Get extra to filter
            if point not in unique_points and len(point.strip()) > 20:
                unique_points.append(point.strip())
        
        return unique_points[:max_points]

    def extract_news_items(self, content: str, url: str) -> List[NewsItem]:
        """Extract structured news items from content"""
        
        news_items = []
        
        # Split content into potential news sections
        sections = self.split_into_news_sections(content)
        
        for section in sections:
            if len(section.strip()) < 100:  # Skip very short sections
                continue
            
            # Extract title (first meaningful line)
            lines = section.split('\n')
            title = ""
            for line in lines:
                line = line.strip()
                if len(line) > 10 and not line.startswith(('http', 'www')):
                    title = line[:100]  # Limit title length
                    break
            
            if not title:
                continue
            
            # Extract dates
            dates = self.extract_dates(section)
            date = dates[0] if dates else datetime.now().strftime("%Y-%m-%d")
            
            # Extract financial and operational data
            financial_data = self.extract_financial_data(section)
            operational_data = self.extract_operational_data(section)
            
            # Categorize content
            category = self.categorize_content(section, title)
            
            # Calculate relevance score
            relevance_score = self.calculate_relevance_score(
                section, title, financial_data, operational_data
            )
            
            # Extract key points
            key_points = self.extract_key_points(section)
            
            # Determine financial impact
            financial_impact = self.determine_financial_impact(section, financial_data)
            
            # Create news item
            news_item = NewsItem(
                title=title,
                date=date,
                content=section[:500] + "..." if len(section) > 500 else section,
                category=category,
                relevance_score=relevance_score,
                key_points=key_points,
                financial_impact=financial_impact,
                url=url
            )
            
            # Only include items with reasonable relevance
            if relevance_score >= 20:
                news_items.append(news_item)
        
        # Sort by relevance score and return top items
        news_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return news_items[:10]  # Return top 10 most relevant

    def split_into_news_sections(self, content: str) -> List[str]:
        """Split content into distinct news sections"""
        
        # Common section delimiters
        delimiters = [
            r'\n\s*###?\s+[A-Z]',  # Markdown headers
            r'\n\s*[A-Z][^a-z]{10,}',  # ALL CAPS headers
            r'\n\s*\d{1,2}/\d{1,2}/\d{4}',  # Date headers
            r'\n\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}',  # Month headers
        ]
        
        # Try to split by delimiters
        sections = [content]
        for delimiter in delimiters:
            new_sections = []
            for section in sections:
                parts = re.split(delimiter, section)
                new_sections.extend(parts)
            sections = new_sections
        
        # Filter out very short sections
        meaningful_sections = [s for s in sections if len(s.strip()) > 200]
        
        # If no good splits found, use paragraph breaks
        if len(meaningful_sections) < 2:
            paragraphs = content.split('\n\n')
            meaningful_sections = [p for p in paragraphs if len(p.strip()) > 200]
        
        return meaningful_sections[:20]  # Limit to prevent too many sections

    def determine_financial_impact(self, content: str, financial_data: FinancialData) -> Optional[str]:
        """Determine financial impact of news"""
        
        content_lower = content.lower()
        
        # Positive indicators
        positive_terms = [
            'record', 'strong', 'increased', 'growth', 'beat', 'exceeded',
            'outperformed', 'positive', 'up', 'higher', 'improvement'
        ]
        
        # Negative indicators
        negative_terms = [
            'down', 'decreased', 'lower', 'missed', 'below', 'weak',
            'declined', 'loss', 'impairment', 'closure', 'suspended'
        ]
        
        positive_score = sum(1 for term in positive_terms if term in content_lower)
        negative_score = sum(1 for term in negative_terms if term in content_lower)
        
        # Check for specific financial improvements
        if financial_data.revenue or financial_data.ebitda or financial_data.cash_flow:
            if any(term in content_lower for term in ['increased', 'up', 'higher', 'record']):
                return "positive"
        
        if positive_score > negative_score and positive_score > 1:
            return "positive"
        elif negative_score > positive_score and negative_score > 1:
            return "negative"
        else:
            return "neutral"

    async def process_company_enhanced(self, company_data: Dict[str, str]) -> Dict[str, Any]:
        """Process a company with enhanced pattern-based extraction"""
        
        symbol = company_data["symbol"]
        logger.info(f"Processing company with enhanced extraction: {symbol}")
        
        results = {
            "symbol": symbol,
            "name": company_data["name"],
            "processing_date": datetime.now().isoformat(),
            "financial_data": {},
            "operational_data": {},
            "news_items": [],
            "relevance_score": 0,
            "errors": []
        }
        
        # URLs to process
        urls_to_process = [
            ("main_website", company_data.get("website")),
            ("investor_relations", company_data.get("investor_relations_url")),
            ("news_page", company_data.get("news_url"))
        ]
        
        # Process each URL
        async with AsyncWebCrawler(headless=True) as crawler:
            for url_type, url in urls_to_process:
                if not url:
                    continue
                
                try:
                    logger.info(f"Processing {url_type} for {symbol}: {url}")
                    
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=Config.MIN_WORD_COUNT
                    )
                    
                    if result.markdown and len(result.markdown) > 500:
                        content = result.markdown
                        
                        # Extract structured data
                        financial_data = self.extract_financial_data(content)
                        operational_data = self.extract_operational_data(content)
                        news_items = self.extract_news_items(content, url)
                        
                        # Store data
                        if url_type == "main_website":
                            results["financial_data"].update(asdict(financial_data))
                            results["operational_data"].update(asdict(operational_data))
                        
                        results["news_items"].extend(news_items)
                        
                        # Calculate relevance
                        page_relevance = sum(item.relevance_score for item in news_items)
                        results["relevance_score"] += page_relevance
                        
                        logger.info(f"Extracted from {url_type}: {len(news_items)} news items, relevance: {page_relevance}")
                    
                    else:
                        logger.warning(f"Insufficient content from {url_type} for {symbol}")
                
                except Exception as e:
                    error_msg = f"Error processing {url_type} for {symbol}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                
                # Rate limiting
                await asyncio.sleep(Config.CRAWL_DELAY)
        
        # Remove duplicates and sort news items
        seen_titles = set()
        unique_news = []
        for item in results["news_items"]:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_news.append(item)
        
        results["news_items"] = sorted(unique_news, key=lambda x: x.relevance_score, reverse=True)[:10]
        
        return results

async def main():
    """Test the enhanced pattern-based extractor"""
    
    extractor = PatternBasedExtractor()
    
    # Get test companies
    conn = sqlite3.connect(extractor.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbol, name, website, investor_relations_url, news_url 
        FROM companies 
        WHERE website IS NOT NULL AND website != ''
        ORDER BY market_cap DESC
        LIMIT 3
    ''')
    
    companies = [
        {
            "symbol": row[0],
            "name": row[1],
            "website": row[2],
            "investor_relations_url": row[3],
            "news_url": row[4]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    if not companies:
        logger.error("No companies found in database!")
        return False
    
    logger.info(f"Testing enhanced extraction on {len(companies)} companies")
    
    # Process companies
    results = []
    for company in companies:
        try:
            result = await extractor.process_company_enhanced(company)
            results.append(result)
            
            # Display immediate results
            print(f"\n{result['symbol']} - {result['name']}")
            print("-" * 50)
            print(f"Financial data points: {len([k for k, v in result['financial_data'].items() if v is not None])}")
            print(f"Operational data points: {len([k for k, v in result['operational_data'].items() if v is not None])}")
            print(f"News items: {len(result['news_items'])}")
            print(f"Relevance score: {result['relevance_score']}")
            
            if result['news_items']:
                print("Top news item:")
                top_news = result['news_items'][0]
                print(f"  • {top_news.title}")
                print(f"  • Category: {top_news.category}, Score: {top_news.relevance_score}")
                print(f"  • Key points: {len(top_news.key_points)}")
            
        except Exception as e:
            logger.error(f"Failed to process {company['symbol']}: {str(e)}")
    
    # Save results
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pattern_extraction_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\nResults saved to: {filename}")
        
        # Summary statistics
        total_news = sum(len(r['news_items']) for r in results)
        companies_with_financials = sum(1 for r in results if any(v for v in r['financial_data'].values() if v))
        
        print(f"\nSUMMARY:")
        print(f"• Total news items extracted: {total_news}")
        print(f"• Companies with financial data: {companies_with_financials}/{len(results)}")
        print(f"• Average relevance score: {sum(r['relevance_score'] for r in results) / len(results):.1f}")
        
        return True
    
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\nPattern-based extraction completed successfully!")
    else:
        print("\nPattern-based extraction failed!")