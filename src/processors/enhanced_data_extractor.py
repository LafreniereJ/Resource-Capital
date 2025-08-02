#!/usr/bin/env python3
"""
Enhanced Data Extractor with LLM-Powered Content Analysis
Extracts structured financial and operational data from mining company websites
"""

import asyncio
import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import logging
from ..core.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FinancialMetrics:
    """Structure for financial data"""
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    cash_flow: Optional[float] = None
    net_income: Optional[float] = None
    guidance_revenue: Optional[str] = None
    guidance_production: Optional[str] = None
    guidance_costs: Optional[str] = None
    dividend_amount: Optional[float] = None
    share_price: Optional[float] = None
    market_cap: Optional[float] = None

@dataclass
class OperationalMetrics:
    """Structure for operational data"""
    production_volume: Optional[float] = None
    production_unit: Optional[str] = None
    cash_cost: Optional[float] = None
    all_in_cost: Optional[float] = None
    grade: Optional[float] = None
    recovery_rate: Optional[float] = None
    reserves: Optional[float] = None
    resources: Optional[float] = None

@dataclass
class NewsItem:
    """Structure for news/announcement data"""
    title: str
    date: str
    content: str
    url: str
    category: str  # earnings, operational, corporate, exploration
    relevance_score: int
    key_points: List[str]
    financial_impact: Optional[str] = None

class EnhancedDataExtractor:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.llm_config = Config.get_llm_config()
        self.extraction_schemas = self._setup_extraction_schemas()
        
    def _setup_extraction_schemas(self) -> Dict[str, str]:
        """Setup LLM extraction schemas for different content types"""
        
        financial_schema = """
        Extract financial information from the content and return a JSON object with the following structure:
        {
            "financial_metrics": {
                "revenue": number (in millions, latest quarter/year),
                "ebitda": number (in millions),
                "cash_flow": number (in millions, operating cash flow),
                "net_income": number (in millions),
                "guidance_revenue": string (any forward-looking revenue guidance),
                "guidance_production": string (production guidance),
                "guidance_costs": string (cost guidance),
                "dividend_amount": number (quarterly dividend per share),
                "share_price": number (current or recent),
                "market_cap": number (in millions)
            },
            "operational_metrics": {
                "production_volume": number (latest period production),
                "production_unit": string (ounces, tonnes, barrels, etc.),
                "cash_cost": number (per unit cash cost),
                "all_in_cost": number (all-in sustaining cost),
                "grade": number (ore grade),
                "recovery_rate": number (percentage),
                "reserves": number (proven and probable reserves),
                "resources": number (measured, indicated, inferred)
            },
            "recent_announcements": [
                {
                    "date": string (YYYY-MM-DD format),
                    "title": string,
                    "category": string (earnings, operational, corporate, exploration, acquisition),
                    "key_points": [string],
                    "financial_impact": string (positive, negative, neutral, or specific impact)
                }
            ]
        }
        
        Focus on the most recent data (last 12 months). If specific numbers aren't found, use null.
        For dates, convert any format to YYYY-MM-DD. Only include high-confidence extractions.
        """
        
        news_schema = """
        Extract recent news and announcements from the content. Return a JSON object:
        {
            "news_items": [
                {
                    "title": string,
                    "date": string (YYYY-MM-DD format),
                    "content": string (summary of key points, max 300 chars),
                    "category": string (earnings, operational, corporate, exploration, acquisition, guidance),
                    "relevance_score": number (1-10, 10 being most material/important),
                    "key_points": [string] (3-5 bullet points of main takeaways),
                    "financial_impact": string (description of financial impact if any),
                    "url": string (if available)
                }
            ]
        }
        
        Only include items from the last 6 months. Focus on material events that would interest investors.
        Prioritize earnings results, guidance updates, major operational changes, M&A activity.
        """
        
        project_schema = """
        Extract project and operational updates from mining company content. Return JSON:
        {
            "project_updates": [
                {
                    "project_name": string,
                    "location": string,
                    "update_type": string (development, production, exploration, expansion, closure),
                    "date": string (YYYY-MM-DD),
                    "key_developments": [string],
                    "production_impact": string,
                    "timeline": string,
                    "capex": number (if mentioned, in millions),
                    "status": string (on-track, delayed, ahead-of-schedule, etc.)
                }
            ],
            "exploration_results": [
                {
                    "property": string,
                    "location": string,
                    "date": string,
                    "highlights": [string],
                    "drill_results": string,
                    "resource_estimate": string
                }
            ]
        }
        
        Focus on recent updates (last 12 months) that show material progress or changes.
        """
        
        return {
            "financial": financial_schema,
            "news": news_schema,
            "projects": project_schema
        }

    async def extract_structured_data(self, url: str, content: str, company_symbol: str) -> Dict[str, Any]:
        """Extract structured data using LLM-powered analysis"""
        
        extracted_data = {
            "company_symbol": company_symbol,
            "url": url,
            "extraction_date": datetime.now().isoformat(),
            "financial_data": {},
            "operational_data": {},
            "news_items": [],
            "project_updates": [],
            "exploration_results": []
        }
        
        async with AsyncWebCrawler(headless=True) as crawler:
            
            # Extract financial data
            try:
                logger.info(f"Extracting financial data from {url}")
                
                financial_result = await crawler.arun(
                    url=url,
                    extraction_strategy=LLMExtractionStrategy(
                        provider=self.llm_config["provider"],
                        api_token=self.llm_config["api_token"],
                        instruction=self.extraction_schemas["financial"]
                    ),
                    word_count_threshold=Config.MIN_WORD_COUNT
                )
                
                if hasattr(financial_result, 'extracted_content') and financial_result.extracted_content:
                    try:
                        financial_json = json.loads(financial_result.extracted_content)
                        extracted_data["financial_data"] = financial_json.get("financial_metrics", {})
                        extracted_data["operational_data"] = financial_json.get("operational_metrics", {})
                        
                        # Add recent announcements to news items
                        if "recent_announcements" in financial_json:
                            extracted_data["news_items"].extend(financial_json["recent_announcements"])
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse financial JSON for {company_symbol}")
                        
            except Exception as e:
                logger.error(f"Error extracting financial data for {company_symbol}: {str(e)}")
            
            # Extract news data
            try:
                logger.info(f"Extracting news data from {url}")
                
                news_result = await crawler.arun(
                    url=url,
                    extraction_strategy=LLMExtractionStrategy(
                        provider=self.llm_config["provider"],
                        api_token=self.llm_config["api_token"],
                        instruction=self.extraction_schemas["news"]
                    ),
                    word_count_threshold=Config.MIN_WORD_COUNT
                )
                
                if hasattr(news_result, 'extracted_content') and news_result.extracted_content:
                    try:
                        news_json = json.loads(news_result.extracted_content)
                        if "news_items" in news_json:
                            extracted_data["news_items"].extend(news_json["news_items"])
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse news JSON for {company_symbol}")
                        
            except Exception as e:
                logger.error(f"Error extracting news data for {company_symbol}: {str(e)}")
            
            # Extract project data
            try:
                logger.info(f"Extracting project data from {url}")
                
                project_result = await crawler.arun(
                    url=url,
                    extraction_strategy=LLMExtractionStrategy(
                        provider=self.llm_config["provider"],
                        api_token=self.llm_config["api_token"],
                        instruction=self.extraction_schemas["projects"]
                    ),
                    word_count_threshold=Config.MIN_WORD_COUNT
                )
                
                if hasattr(project_result, 'extracted_content') and project_result.extracted_content:
                    try:
                        project_json = json.loads(project_result.extracted_content)
                        extracted_data["project_updates"] = project_json.get("project_updates", [])
                        extracted_data["exploration_results"] = project_json.get("exploration_results", [])
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse project JSON for {company_symbol}")
                        
            except Exception as e:
                logger.error(f"Error extracting project data for {company_symbol}: {str(e)}")
        
        return extracted_data

    def calculate_content_relevance(self, extracted_data: Dict[str, Any]) -> int:
        """Calculate relevance score for the extracted content"""
        
        score = 0
        
        # Financial data relevance
        financial = extracted_data.get("financial_data", {})
        if financial.get("revenue"):
            score += 20
        if financial.get("ebitda"):
            score += 15
        if financial.get("guidance_revenue") or financial.get("guidance_production"):
            score += 25
        if financial.get("dividend_amount"):
            score += 10
        
        # News items relevance
        news_items = extracted_data.get("news_items", [])
        for item in news_items:
            item_score = item.get("relevance_score", 0)
            if item_score >= 8:
                score += 15
            elif item_score >= 6:
                score += 10
            elif item_score >= 4:
                score += 5
        
        # Project updates relevance
        project_updates = extracted_data.get("project_updates", [])
        if project_updates:
            score += len(project_updates) * 5
        
        # Recent content bonus
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_items = 0
        
        for item in news_items:
            try:
                item_date = datetime.strptime(item.get("date", ""), "%Y-%m-%d")
                if item_date > recent_cutoff:
                    recent_items += 1
            except:
                pass
        
        score += recent_items * 5
        
        return min(score, 100)  # Cap at 100

    async def process_company(self, company_data: Dict[str, str]) -> Dict[str, Any]:
        """Process a single company and extract all relevant data"""
        
        symbol = company_data["symbol"]
        logger.info(f"Processing company: {symbol}")
        
        results = {
            "symbol": symbol,
            "name": company_data["name"],
            "processing_date": datetime.now().isoformat(),
            "extracted_data": [],
            "relevance_score": 0,
            "errors": []
        }
        
        # URLs to process
        urls_to_process = []
        
        if company_data.get("website"):
            urls_to_process.append(("main_website", company_data["website"]))
        
        if company_data.get("investor_relations_url"):
            urls_to_process.append(("investor_relations", company_data["investor_relations_url"]))
        
        if company_data.get("news_url"):
            urls_to_process.append(("news_page", company_data["news_url"]))
        
        # Process each URL
        for url_type, url in urls_to_process:
            try:
                logger.info(f"Processing {url_type} for {symbol}: {url}")
                
                # Get basic content first
                async with AsyncWebCrawler(headless=True) as crawler:
                    basic_result = await crawler.arun(url=url, word_count_threshold=100)
                    
                    if basic_result.markdown and len(basic_result.markdown) > 500:
                        # Extract structured data using LLM
                        extracted_data = await self.extract_structured_data(
                            url, basic_result.markdown, symbol
                        )
                        
                        # Calculate relevance
                        relevance = self.calculate_content_relevance(extracted_data)
                        extracted_data["relevance_score"] = relevance
                        extracted_data["url_type"] = url_type
                        
                        results["extracted_data"].append(extracted_data)
                        results["relevance_score"] += relevance
                        
                        logger.info(f"Extracted data from {url_type} with relevance score: {relevance}")
                    
                    else:
                        logger.warning(f"Insufficient content from {url_type} for {symbol}")
                
                # Rate limiting
                await asyncio.sleep(Config.CRAWL_DELAY)
                
            except Exception as e:
                error_msg = f"Error processing {url_type} for {symbol}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Calculate overall relevance score
        if results["extracted_data"]:
            results["relevance_score"] = results["relevance_score"] // len(results["extracted_data"])
        
        return results

    def save_extracted_data(self, company_results: List[Dict[str, Any]]) -> str:
        """Save extracted data to database and files"""
        
        # Update database schema to include new fields
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new columns if they don't exist
        try:
            cursor.execute('ALTER TABLE company_news ADD COLUMN financial_metrics TEXT')
            cursor.execute('ALTER TABLE company_news ADD COLUMN operational_metrics TEXT')
            cursor.execute('ALTER TABLE company_news ADD COLUMN project_updates TEXT')
        except sqlite3.OperationalError:
            pass  # Columns already exist
        
        # Save data to database
        for company_result in company_results:
            company_id = self.get_company_id(company_result["symbol"])
            
            if not company_id:
                continue
            
            for extracted_data in company_result["extracted_data"]:
                
                # Save news items
                for news_item in extracted_data.get("news_items", []):
                    cursor.execute('''
                        INSERT INTO company_news 
                        (company_id, title, content, url, published_date, content_type, 
                         relevance_score, financial_metrics, operational_metrics, project_updates)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        company_id,
                        news_item.get("title", ""),
                        news_item.get("content", ""),
                        news_item.get("url", extracted_data["url"]),
                        news_item.get("date", datetime.now().strftime("%Y-%m-%d")),
                        news_item.get("category", "general"),
                        news_item.get("relevance_score", 0),
                        json.dumps(extracted_data.get("financial_data", {})),
                        json.dumps(extracted_data.get("operational_data", {})),
                        json.dumps(extracted_data.get("project_updates", []))
                    ))
        
        conn.commit()
        conn.close()
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_extraction_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(company_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved enhanced extraction results to {filename}")
        return filename

    def get_company_id(self, symbol: str) -> Optional[int]:
        """Get company ID from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM companies WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None

    def generate_extraction_report(self, company_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive extraction report"""
        
        report = []
        report.append("ENHANCED DATA EXTRACTION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Companies processed: {len(company_results)}")
        report.append("")
        
        # Summary statistics
        total_news_items = sum(
            len(data.get("news_items", []))
            for result in company_results
            for data in result.get("extracted_data", [])
        )
        
        total_financial_metrics = sum(
            1 for result in company_results
            for data in result.get("extracted_data", [])
            if data.get("financial_data")
        )
        
        total_project_updates = sum(
            len(data.get("project_updates", []))
            for result in company_results
            for data in result.get("extracted_data", [])
        )
        
        report.append("EXTRACTION SUMMARY:")
        report.append(f"• News items extracted: {total_news_items}")
        report.append(f"• Companies with financial data: {total_financial_metrics}")
        report.append(f"• Project updates found: {total_project_updates}")
        report.append("")
        
        # Top companies by relevance
        sorted_companies = sorted(
            company_results, 
            key=lambda x: x.get("relevance_score", 0), 
            reverse=True
        )
        
        report.append("TOP COMPANIES BY RELEVANCE:")
        report.append("-" * 30)
        for i, company in enumerate(sorted_companies[:10]):
            symbol = company["symbol"]
            score = company.get("relevance_score", 0)
            news_count = sum(
                len(data.get("news_items", []))
                for data in company.get("extracted_data", [])
            )
            report.append(f"{i+1}. {symbol}: Score {score}, {news_count} news items")
        
        report.append("")
        
        # Recent high-impact news
        all_news = []
        for result in company_results:
            for data in result.get("extracted_data", []):
                for news_item in data.get("news_items", []):
                    news_item["company"] = result["symbol"]
                    all_news.append(news_item)
        
        # Sort by relevance score
        high_impact_news = sorted(
            [item for item in all_news if item.get("relevance_score", 0) >= 7],
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        if high_impact_news:
            report.append("HIGH-IMPACT NEWS (Score >= 7):")
            report.append("-" * 30)
            for news in high_impact_news[:10]:
                company = news.get("company", "")
                title = news.get("title", "")[:60]
                score = news.get("relevance_score", 0)
                date = news.get("date", "")
                report.append(f"• {company}: {title}... (Score: {score}, Date: {date})")
        
        return "\n".join(report)

async def main():
    """Main execution function for enhanced extraction"""
    
    extractor = EnhancedDataExtractor()
    
    # Get companies from database
    conn = sqlite3.connect(extractor.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbol, name, website, investor_relations_url, news_url 
        FROM companies 
        WHERE website IS NOT NULL AND website != ''
        ORDER BY market_cap DESC
        LIMIT 5
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
    
    logger.info(f"Starting enhanced extraction for {len(companies)} companies")
    
    # Process all companies
    results = []
    for company in companies:
        try:
            result = await extractor.process_company(company)
            results.append(result)
            logger.info(f"Completed processing {company['symbol']}")
            
        except Exception as e:
            logger.error(f"Failed to process {company['symbol']}: {str(e)}")
    
    # Save results
    if results:
        filename = extractor.save_extracted_data(results)
        report = extractor.generate_extraction_report(results)
        
        # Save report
        report_filename = filename.replace('.json', '_report.txt')
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print("\n" + report)
        print(f"\nFiles saved:")
        print(f"• Data: {filename}")
        print(f"• Report: {report_filename}")
        
        return True
    
    else:
        logger.error("No results to save!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\nEnhanced extraction completed successfully!")
    else:
        print("\nEnhanced extraction failed!")