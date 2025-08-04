#!/usr/bin/env python3
"""
Production-Grade Mining Intelligence System Test
Comprehensive production test with robust data collection, extensive analysis, and detailed reporting

Features:
- Extended timeouts for comprehensive scraping (45-60 minutes)
- Robust error handling with retry mechanisms
- Progress tracking and detailed logging
- Comprehensive data validation
- Performance monitoring and timing
- Full domain coverage with deep analysis
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'production_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import specialized scrapers
from src.scrapers.specialized.metal_prices_scraper import MetalPricesScraper
from src.scrapers.specialized.economic_data_scraper import EconomicDataScraper
from src.scrapers.specialized.mining_companies_scraper import MiningCompaniesScraper
from src.scrapers.specialized.mining_news_scraper import SpecializedMiningNewsScraper

# Import analyzers
from src.analyzers.price_analyzer import PriceAnalyzer

# Import master compiler
from src.intelligence.master_compiler import MasterIntelligenceCompiler


class ProductionTestRunner:
    """Production-grade test runner with comprehensive monitoring"""
    
    def __init__(self):
        self.start_time = None
        self.test_results = {}
        self.performance_metrics = {}
        self.data_quality_scores = {}
        self.error_log = []
        
        # Production settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.scraping_timeout = 3600  # 1 hour max per domain
        
    def log_progress(self, message: str, level: str = "INFO"):
        """Log progress with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if level == "INFO":
            logger.info(formatted_message)
            print(f"ℹ️  {formatted_message}")
        elif level == "SUCCESS":
            logger.info(formatted_message)
            print(f"✅ {formatted_message}")
        elif level == "WARNING":
            logger.warning(formatted_message)
            print(f"⚠️  {formatted_message}")
        elif level == "ERROR":
            logger.error(formatted_message)
            print(f"❌ {formatted_message}")
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with retry logic and exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                
                wait_time = self.retry_delay * (2 ** attempt)
                self.log_progress(f"Attempt {attempt + 1} failed: {str(e)}, retrying in {wait_time}s", "WARNING")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"All {self.max_retries} attempts failed")
    
    async def test_metal_prices_comprehensive(self):
        """Comprehensive metal prices data collection and analysis"""
        self.log_progress("🔥 COMPREHENSIVE METAL PRICES COLLECTION", "INFO")
        
        domain_start = time.time()
        
        try:
            # Initialize scraper
            scraper = MetalPricesScraper()
            
            # Scrape with retry logic
            self.log_progress("Collecting metal prices from all sources...", "INFO")
            results = await self.retry_with_backoff(scraper.scrape_all_metal_prices)
            
            # Validate data quality
            quality_score = self._validate_metal_prices_data(results)
            self.data_quality_scores['metal_prices'] = quality_score
            
            # Performance analysis
            duration = time.time() - domain_start
            self.performance_metrics['metal_prices'] = {
                'duration': duration,
                'metals_scraped': results['summary']['total_metals_scraped'],
                'sources_success_rate': results['summary']['successful_sources'] / (results['summary']['total_metals_scraped'] * 4) * 100,  # 4 sources per metal
                'data_quality_score': quality_score
            }
            
            self.log_progress(f"Metal Prices: {results['summary']['total_metals_scraped']} metals, {results['summary']['successful_sources']} sources, {duration:.1f}s", "SUCCESS")
            
            # Clean up
            await scraper.cleanup()
            
            return results
            
        except Exception as e:
            self.log_progress(f"Metal prices collection failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'metal_prices', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    async def test_economic_indicators_comprehensive(self):
        """Comprehensive economic indicators collection and analysis"""
        self.log_progress("📊 COMPREHENSIVE ECONOMIC INDICATORS COLLECTION", "INFO")
        
        domain_start = time.time()
        
        try:
            # Initialize scraper
            scraper = EconomicDataScraper()
            
            # Scrape with retry logic
            self.log_progress("Collecting economic indicators from all sources...", "INFO")
            results = await self.retry_with_backoff(scraper.scrape_all_economic_data)
            
            # Validate data quality
            quality_score = self._validate_economic_data(results)
            self.data_quality_scores['economic_indicators'] = quality_score
            
            # Performance analysis
            duration = time.time() - domain_start
            self.performance_metrics['economic_indicators'] = {
                'duration': duration,
                'sources_scraped': results['summary']['total_sources_scraped'],
                'indicators_found': results['summary']['total_indicators_found'],
                'success_rate': results['summary']['successful_extractions'] / results['summary']['total_sources_scraped'] * 100 if results['summary']['total_sources_scraped'] > 0 else 0,
                'data_quality_score': quality_score
            }
            
            self.log_progress(f"Economic Indicators: {results['summary']['total_sources_scraped']} sources, {results['summary']['total_indicators_found']} indicators, {duration:.1f}s", "SUCCESS")
            
            # Clean up
            await scraper.cleanup()
            
            return results
            
        except Exception as e:
            self.log_progress(f"Economic indicators collection failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'economic_indicators', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    async def test_mining_companies_comprehensive(self):
        """Comprehensive mining companies data collection and analysis"""
        self.log_progress("🏢 COMPREHENSIVE MINING COMPANIES COLLECTION", "INFO")
        
        domain_start = time.time()
        
        try:
            # Initialize scraper
            scraper = MiningCompaniesScraper()
            
            # Scrape with retry logic
            self.log_progress("Collecting mining companies data...", "INFO")
            results = await self.retry_with_backoff(scraper.scrape_all_companies_data)
            
            # Validate data quality
            quality_score = self._validate_companies_data(results)
            self.data_quality_scores['companies'] = quality_score
            
            # Performance analysis
            duration = time.time() - domain_start
            self.performance_metrics['companies'] = {
                'duration': duration,
                'companies_attempted': results['summary']['total_companies_attempted'],
                'successful_scrapes': results['summary']['successful_company_scrapes'],
                'success_rate': results['summary']['successful_company_scrapes'] / results['summary']['total_companies_attempted'] * 100 if results['summary']['total_companies_attempted'] > 0 else 0,
                'data_quality_score': quality_score
            }
            
            self.log_progress(f"Companies: {results['summary']['successful_company_scrapes']}/{results['summary']['total_companies_attempted']} companies, {duration:.1f}s", "SUCCESS")
            
            # Clean up
            await scraper.cleanup()
            
            return results
            
        except Exception as e:
            self.log_progress(f"Companies collection failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'companies', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    async def test_mining_news_comprehensive(self):
        """Comprehensive mining news collection and analysis"""
        self.log_progress("📰 COMPREHENSIVE MINING NEWS COLLECTION", "INFO")
        
        domain_start = time.time()
        
        try:
            # Initialize scraper
            scraper = SpecializedMiningNewsScraper()
            
            # Scrape with retry logic
            self.log_progress("Collecting mining news from all sources...", "INFO")
            results = await self.retry_with_backoff(scraper.scrape_all_mining_news)
            
            # Validate data quality
            quality_score = self._validate_news_data(results)
            self.data_quality_scores['news'] = quality_score
            
            # Performance analysis
            duration = time.time() - domain_start
            self.performance_metrics['news'] = {
                'duration': duration,
                'sources_scraped': results['summary']['total_sources_scraped'],
                'articles_found': results['summary']['total_articles_found'],
                'unique_articles': results['summary']['unique_articles'],
                'deduplication_rate': (results['summary']['total_articles_found'] - results['summary']['unique_articles']) / results['summary']['total_articles_found'] * 100 if results['summary']['total_articles_found'] > 0 else 0,
                'data_quality_score': quality_score
            }
            
            self.log_progress(f"News: {results['summary']['unique_articles']} unique articles from {results['summary']['total_sources_scraped']} sources, {duration:.1f}s", "SUCCESS")
            
            # Clean up
            await scraper.cleanup()
            
            return results
            
        except Exception as e:
            self.log_progress(f"News collection failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'news', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    async def test_price_analysis_comprehensive(self, price_data):
        """Comprehensive price analysis"""
        self.log_progress("📈 COMPREHENSIVE PRICE ANALYSIS", "INFO")
        
        if not price_data:
            self.log_progress("No price data available for analysis", "WARNING")
            return None
        
        analysis_start = time.time()
        
        try:
            # Initialize analyzer
            analyzer = PriceAnalyzer()
            
            # Perform comprehensive analysis
            self.log_progress("Analyzing price trends, volatility, and correlations...", "INFO")
            results = await analyzer.analyze_all_prices(90)  # 90 days of analysis
            
            # Performance metrics
            duration = time.time() - analysis_start
            self.performance_metrics['price_analysis'] = {
                'duration': duration,
                'metals_analyzed': results['summary']['metals_analyzed'],
                'alerts_generated': results['summary']['total_alerts'],
                'analysis_success_rate': results['summary']['analysis_coverage']['success_rate']
            }
            
            self.log_progress(f"Price Analysis: {results['summary']['metals_analyzed']} metals analyzed, {results['summary']['total_alerts']} alerts, {duration:.1f}s", "SUCCESS")
            
            return results
            
        except Exception as e:
            self.log_progress(f"Price analysis failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'price_analysis', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    async def test_master_intelligence_comprehensive(self, collected_data):
        """Comprehensive intelligence compilation"""
        self.log_progress("🧠 COMPREHENSIVE INTELLIGENCE COMPILATION", "INFO")
        
        compilation_start = time.time()
        
        try:
            # Initialize compiler
            compiler = MasterIntelligenceCompiler()
            
            # Generate comprehensive intelligence report
            self.log_progress("Compiling cross-domain intelligence report...", "INFO")
            report = await compiler.generate_comprehensive_intelligence_report()
            
            # Performance metrics
            duration = time.time() - compilation_start
            self.performance_metrics['intelligence_compilation'] = {
                'duration': duration,
                'report_sections': len([k for k in report.keys() if not k.startswith('_')]),
                'opportunities_identified': len(report.get('executive_summary', {}).get('top_opportunities', [])),
                'risks_identified': len(report.get('executive_summary', {}).get('main_risks', [])),
                'data_quality': report.get('data_quality_assessment', {}).get('overall_quality', 'unknown')
            }
            
            self.log_progress(f"Intelligence Report: {len(report.get('executive_summary', {}).get('top_opportunities', []))} opportunities, {len(report.get('executive_summary', {}).get('main_risks', []))} risks, {duration:.1f}s", "SUCCESS")
            
            # Clean up
            await compiler.cleanup()
            
            return report
            
        except Exception as e:
            self.log_progress(f"Intelligence compilation failed: {str(e)}", "ERROR")
            self.error_log.append({'domain': 'intelligence_compilation', 'error': str(e), 'traceback': traceback.format_exc()})
            return None
    
    def _validate_metal_prices_data(self, data) -> float:
        """Validate metal prices data quality"""
        if not data:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Check basic structure
        if data.get('summary'):
            score += 20
        
        # Check metals coverage
        metals_scraped = data.get('summary', {}).get('total_metals_scraped', 0)
        if metals_scraped >= 8:  # Expect at least 8 metals
            score += 30
        elif metals_scraped >= 5:
            score += 20
        elif metals_scraped >= 3:
            score += 10
        
        # Check source diversity
        successful_sources = data.get('summary', {}).get('successful_sources', 0)
        if successful_sources >= 15:  # Multiple sources per metal
            score += 25
        elif successful_sources >= 10:
            score += 15
        elif successful_sources >= 5:
            score += 10
        
        # Check consensus pricing
        metals_with_consensus = data.get('summary', {}).get('metals_with_consensus', 0)
        if metals_with_consensus >= 5:
            score += 25
        elif metals_with_consensus >= 3:
            score += 15
        elif metals_with_consensus >= 1:
            score += 10
        
        return min(score, max_score)
    
    def _validate_economic_data(self, data) -> float:
        """Validate economic data quality"""
        if not data:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Check basic structure
        if data.get('summary'):
            score += 20
        
        # Check sources coverage
        sources_scraped = data.get('summary', {}).get('total_sources_scraped', 0)
        if sources_scraped >= 4:
            score += 30
        elif sources_scraped >= 2:
            score += 20
        elif sources_scraped >= 1:
            score += 10
        
        # Check indicators extracted
        indicators_found = data.get('summary', {}).get('total_indicators_found', 0)
        if indicators_found >= 10:
            score += 30
        elif indicators_found >= 5:
            score += 20
        elif indicators_found >= 2:
            score += 10
        
        # Check extraction success rate
        successful_extractions = data.get('summary', {}).get('successful_extractions', 0)
        total_sources = data.get('summary', {}).get('total_sources_scraped', 1)
        success_rate = successful_extractions / total_sources * 100
        if success_rate >= 75:
            score += 20
        elif success_rate >= 50:
            score += 15
        elif success_rate >= 25:
            score += 10
        
        return min(score, max_score)
    
    def _validate_companies_data(self, data) -> float:
        """Validate companies data quality"""
        if not data:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Check basic structure
        if data.get('summary'):
            score += 20
        
        # Check companies coverage
        companies_attempted = data.get('summary', {}).get('total_companies_attempted', 0)
        if companies_attempted >= 10:
            score += 25
        elif companies_attempted >= 5:
            score += 15
        elif companies_attempted >= 1:
            score += 10
        
        # Check success rate
        successful_scrapes = data.get('summary', {}).get('successful_company_scrapes', 0)
        if companies_attempted > 0:
            success_rate = successful_scrapes / companies_attempted * 100
            if success_rate >= 75:
                score += 30
            elif success_rate >= 50:
                score += 20
            elif success_rate >= 25:
                score += 10
        
        # Check data richness
        companies_with_stock_data = data.get('summary', {}).get('companies_with_stock_data', 0)
        if companies_with_stock_data >= 5:
            score += 25
        elif companies_with_stock_data >= 2:
            score += 15
        elif companies_with_stock_data >= 1:
            score += 10
        
        return min(score, max_score)
    
    def _validate_news_data(self, data) -> float:
        """Validate news data quality"""
        if not data:
            return 0.0
        
        score = 0.0
        max_score = 100.0
        
        # Check basic structure
        if data.get('summary'):
            score += 20
        
        # Check sources coverage
        sources_scraped = data.get('summary', {}).get('total_sources_scraped', 0)
        if sources_scraped >= 5:
            score += 25
        elif sources_scraped >= 3:
            score += 15
        elif sources_scraped >= 1:
            score += 10
        
        # Check articles volume
        unique_articles = data.get('summary', {}).get('unique_articles', 0)
        if unique_articles >= 50:
            score += 30
        elif unique_articles >= 25:
            score += 20
        elif unique_articles >= 10:
            score += 15
        elif unique_articles >= 5:
            score += 10
        
        # Check deduplication effectiveness
        total_articles = data.get('summary', {}).get('total_articles_found', 0)
        if total_articles > 0:
            dedup_rate = (total_articles - unique_articles) / total_articles * 100
            if dedup_rate >= 20:  # Good deduplication
                score += 25
            elif dedup_rate >= 10:
                score += 15
            elif dedup_rate >= 5:
                score += 10
        
        return min(score, max_score)
    
    async def generate_comprehensive_report(self, all_results):
        """Generate comprehensive production test report"""
        self.log_progress("📋 GENERATING COMPREHENSIVE PRODUCTION REPORT", "INFO")
        
        total_duration = time.time() - self.start_time
        
        # Compile comprehensive report
        report = {
            'test_metadata': {
                'test_type': 'production_comprehensive',
                'start_time': self.start_time,
                'end_time': time.time(),
                'total_duration_minutes': total_duration / 60,
                'test_timestamp': datetime.now().isoformat()
            },
            'executive_summary': self._generate_executive_summary(all_results),
            'domain_results': all_results,
            'performance_metrics': self.performance_metrics,
            'data_quality_assessment': self.data_quality_scores,
            'error_analysis': self.error_log,
            'system_health': self._assess_system_health(),
            'recommendations': self._generate_recommendations(),
            'detailed_findings': self._generate_detailed_findings(all_results)
        }
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"production_mining_intelligence_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # Generate human-readable summary
        summary_file = f"production_mining_intelligence_summary_{timestamp}.txt"
        self._generate_human_readable_summary(report, summary_file)
        
        self.log_progress(f"Comprehensive report saved: {report_file}", "SUCCESS")
        self.log_progress(f"Human-readable summary: {summary_file}", "SUCCESS")
        
        return report
    
    def _generate_executive_summary(self, all_results):
        """Generate executive summary of test results"""
        
        # Count successful domains
        successful_domains = sum(1 for result in all_results.values() if result is not None)
        total_domains = len(all_results)
        
        # Calculate overall quality score
        quality_scores = [score for score in self.data_quality_scores.values() if score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'test_success_rate': (successful_domains / total_domains) * 100,
            'domains_tested': total_domains,
            'domains_successful': successful_domains,
            'average_data_quality': avg_quality,
            'total_errors': len(self.error_log),
            'system_status': 'PRODUCTION_READY' if successful_domains >= 3 and avg_quality >= 70 else 'NEEDS_ATTENTION',
            'key_achievements': self._list_key_achievements(all_results),
            'critical_issues': [error['error'] for error in self.error_log if 'critical' in error.get('error', '').lower()]
        }
    
    def _assess_system_health(self):
        """Assess overall system health"""
        
        health_score = 100
        health_issues = []
        
        # Check data quality
        avg_quality = sum(self.data_quality_scores.values()) / len(self.data_quality_scores) if self.data_quality_scores else 0
        if avg_quality < 50:
            health_score -= 30
            health_issues.append("Low data quality scores")
        elif avg_quality < 70:
            health_score -= 15
            health_issues.append("Moderate data quality concerns")
        
        # Check error rate
        if len(self.error_log) > 2:
            health_score -= 20
            health_issues.append("High error rate")
        elif len(self.error_log) > 0:
            health_score -= 10
            health_issues.append("Some errors encountered")
        
        # Check performance
        slow_domains = [domain for domain, metrics in self.performance_metrics.items() 
                       if metrics.get('duration', 0) > 600]  # 10 minutes
        if len(slow_domains) > 1:
            health_score -= 15
            health_issues.append(f"Slow performance in: {', '.join(slow_domains)}")
        
        return {
            'overall_health_score': max(health_score, 0),
            'health_status': 'EXCELLENT' if health_score >= 90 else 'GOOD' if health_score >= 70 else 'FAIR' if health_score >= 50 else 'POOR',
            'health_issues': health_issues,
            'recommendation': 'PRODUCTION_READY' if health_score >= 70 else 'REQUIRES_OPTIMIZATION'
        }
    
    def _generate_recommendations(self):
        """Generate system improvement recommendations"""
        
        recommendations = []
        
        # Performance recommendations
        slow_domains = [domain for domain, metrics in self.performance_metrics.items() 
                       if metrics.get('duration', 0) > 300]
        if slow_domains:
            recommendations.append(f"Optimize performance for: {', '.join(slow_domains)}")
        
        # Quality recommendations
        low_quality_domains = [domain for domain, score in self.data_quality_scores.items() 
                              if score < 70]
        if low_quality_domains:
            recommendations.append(f"Improve data quality for: {', '.join(low_quality_domains)}")
        
        # Error handling recommendations
        if len(self.error_log) > 0:
            recommendations.append("Review and address error logs for system stability")
        
        # Success recommendations
        if not recommendations:
            recommendations.append("System performing well - consider expanding data sources")
        
        return recommendations
    
    def _list_key_achievements(self, all_results):
        """List key achievements from the test"""
        
        achievements = []
        
        # Data collection achievements
        if all_results.get('metal_prices'):
            metals = all_results['metal_prices'].get('summary', {}).get('total_metals_scraped', 0)
            achievements.append(f"Successfully scraped {metals} metal prices with consensus pricing")
        
        if all_results.get('economic_indicators'):
            indicators = all_results['economic_indicators'].get('summary', {}).get('total_indicators_found', 0)
            achievements.append(f"Extracted {indicators} economic indicators from multiple sources")
        
        if all_results.get('companies'):
            companies = all_results['companies'].get('summary', {}).get('successful_company_scrapes', 0)
            achievements.append(f"Analyzed {companies} mining companies with financial data")
        
        if all_results.get('news'):
            articles = all_results['news'].get('summary', {}).get('unique_articles', 0)
            achievements.append(f"Collected and categorized {articles} unique mining news articles")
        
        if all_results.get('intelligence_report'):
            opportunities = len(all_results['intelligence_report'].get('executive_summary', {}).get('top_opportunities', []))
            achievements.append(f"Identified {opportunities} investment opportunities through cross-domain analysis")
        
        return achievements
    
    def _generate_detailed_findings(self, all_results):
        """Generate detailed findings for each domain"""
        
        findings = {}
        
        for domain, results in all_results.items():
            if results:
                findings[domain] = {
                    'data_points_collected': self._count_data_points(domain, results),
                    'key_insights': self._extract_key_insights(domain, results),
                    'quality_metrics': self.data_quality_scores.get(domain, 0),
                    'performance_metrics': self.performance_metrics.get(domain, {}),
                    'recommendations': self._get_domain_recommendations(domain, results)
                }
        
        return findings
    
    def _count_data_points(self, domain, results):
        """Count data points for a domain"""
        
        if domain == 'metal_prices':
            return results.get('summary', {}).get('total_metals_scraped', 0)
        elif domain == 'economic_indicators':
            return results.get('summary', {}).get('total_indicators_found', 0)
        elif domain == 'companies':
            return results.get('summary', {}).get('successful_company_scrapes', 0)
        elif domain == 'news':
            return results.get('summary', {}).get('unique_articles', 0)
        else:
            return 0
    
    def _extract_key_insights(self, domain, results):
        """Extract key insights for a domain"""
        
        insights = []
        
        if domain == 'metal_prices' and results.get('summary'):
            summary = results['summary']
            insights.append(f"Average price spread: ${summary.get('average_price_spread', 0):.2f}")
            insights.append(f"Metals with consensus pricing: {summary.get('metals_with_consensus', 0)}")
        
        elif domain == 'economic_indicators' and results.get('summary'):
            summary = results['summary']
            insights.append(f"Canadian indicators: {summary.get('canadian_indicators_count', 0)}")
            insights.append(f"US indicators: {summary.get('us_indicators_count', 0)}")
        
        elif domain == 'companies' and results.get('summary'):
            summary = results['summary']
            insights.append(f"Companies with stock data: {summary.get('companies_with_stock_data', 0)}")
            insights.append(f"Success rate: {summary.get('successful_company_scrapes', 0) / summary.get('total_companies_attempted', 1) * 100:.1f}%")
        
        elif domain == 'news' and results.get('summary'):
            summary = results['summary']
            dedup_rate = (summary.get('total_articles_found', 0) - summary.get('unique_articles', 0)) / summary.get('total_articles_found', 1) * 100
            insights.append(f"Deduplication rate: {dedup_rate:.1f}%")
            insights.append(f"Sources coverage: {summary.get('total_sources_scraped', 0)} specialized mining publications")
        
        return insights
    
    def _get_domain_recommendations(self, domain, results):
        """Get recommendations for a specific domain"""
        
        recommendations = []
        
        quality_score = self.data_quality_scores.get(domain, 0)
        if quality_score < 70:
            recommendations.append(f"Improve data extraction quality (current: {quality_score:.1f}/100)")
        
        performance = self.performance_metrics.get(domain, {})
        if performance.get('duration', 0) > 300:
            recommendations.append("Optimize scraping performance and reduce timeouts")
        
        if domain == 'metal_prices':
            metals_scraped = results.get('summary', {}).get('total_metals_scraped', 0)
            if metals_scraped < 8:
                recommendations.append("Expand metal coverage to include more commodities")
        
        return recommendations
    
    def _generate_human_readable_summary(self, report, filename):
        """Generate human-readable summary report"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PRODUCTION MINING INTELLIGENCE SYSTEM - COMPREHENSIVE TEST REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Executive Summary
            exec_summary = report['executive_summary']
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Test Success Rate: {exec_summary['test_success_rate']:.1f}%\n")
            f.write(f"System Status: {exec_summary['system_status']}\n")
            f.write(f"Average Data Quality: {exec_summary['average_data_quality']:.1f}/100\n")
            f.write(f"Total Errors: {exec_summary['total_errors']}\n\n")
            
            # Key Achievements
            f.write("KEY ACHIEVEMENTS\n")
            f.write("-" * 40 + "\n")
            for achievement in exec_summary['key_achievements']:
                f.write(f"• {achievement}\n")
            f.write("\n")
            
            # Performance Metrics
            f.write("PERFORMANCE METRICS\n")
            f.write("-" * 40 + "\n")
            for domain, metrics in report['performance_metrics'].items():
                f.write(f"{domain.replace('_', ' ').title()}: {metrics.get('duration', 0):.1f}s\n")
            f.write("\n")
            
            # Data Quality Assessment
            f.write("DATA QUALITY ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            for domain, score in report['data_quality_assessment'].items():
                f.write(f"{domain.replace('_', ' ').title()}: {score:.1f}/100\n")
            f.write("\n")
            
            # System Health
            health = report['system_health']
            f.write("SYSTEM HEALTH ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            f.write(f"Overall Health Score: {health['overall_health_score']}/100\n")
            f.write(f"Health Status: {health['health_status']}\n")
            f.write(f"Recommendation: {health['recommendation']}\n\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            for rec in report['recommendations']:
                f.write(f"• {rec}\n")
            f.write("\n")
            
            # Test Duration
            duration_minutes = report['test_metadata']['total_duration_minutes']
            f.write(f"Total Test Duration: {duration_minutes:.1f} minutes\n")
            f.write(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


async def run_production_test():
    """Run comprehensive production test"""
    
    print("🚀 PRODUCTION MINING INTELLIGENCE SYSTEM - COMPREHENSIVE TEST")
    print("=" * 80)
    print("Running full production test with robust data collection and analysis")
    print(f"Expected duration: 45-60 minutes")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize test runner
    runner = ProductionTestRunner()
    runner.start_time = time.time()
    
    # Collection results storage
    all_results = {}
    
    try:
        # Phase 1: Comprehensive Data Collection
        runner.log_progress("PHASE 1: COMPREHENSIVE DATA COLLECTION", "INFO")
        
        # Metal Prices (Expected: 8-12 minutes)
        all_results['metal_prices'] = await runner.test_metal_prices_comprehensive()
        
        # Economic Indicators (Expected: 10-15 minutes)
        all_results['economic_indicators'] = await runner.test_economic_indicators_comprehensive()
        
        # Mining Companies (Expected: 15-20 minutes)
        all_results['companies'] = await runner.test_mining_companies_comprehensive()
        
        # Mining News (Expected: 8-12 minutes)
        all_results['news'] = await runner.test_mining_news_comprehensive()
        
        # Phase 2: Comprehensive Analysis
        runner.log_progress("PHASE 2: COMPREHENSIVE ANALYSIS", "INFO")
        
        # Price Analysis
        all_results['price_analysis'] = await runner.test_price_analysis_comprehensive(all_results['metal_prices'])
        
        # Phase 3: Intelligence Compilation
        runner.log_progress("PHASE 3: INTELLIGENCE COMPILATION", "INFO")
        
        # Master Intelligence Report
        all_results['intelligence_report'] = await runner.test_master_intelligence_comprehensive(all_results)
        
        # Phase 4: Comprehensive Report Generation
        runner.log_progress("PHASE 4: COMPREHENSIVE REPORT GENERATION", "INFO")
        
        final_report = await runner.generate_comprehensive_report(all_results)
        
        # Final Summary
        total_duration = (time.time() - runner.start_time) / 60
        runner.log_progress(f"PRODUCTION TEST COMPLETED in {total_duration:.1f} minutes", "SUCCESS")
        
        # System Status
        system_health = final_report['system_health']
        if system_health['recommendation'] == 'PRODUCTION_READY':
            runner.log_progress("🎉 SYSTEM IS PRODUCTION READY!", "SUCCESS")
        else:
            runner.log_progress("⚠️ SYSTEM REQUIRES OPTIMIZATION", "WARNING")
        
        return final_report
        
    except Exception as e:
        runner.log_progress(f"CRITICAL ERROR: {str(e)}", "ERROR")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the comprehensive production test
    result = asyncio.run(run_production_test())
    
    if result:
        print(f"\n✅ Production test completed successfully!")
        print(f"Report generated with {result['executive_summary']['test_success_rate']:.1f}% success rate")
    else:
        print(f"\n❌ Production test encountered critical errors!")