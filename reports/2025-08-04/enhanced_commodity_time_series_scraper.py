#!/usr/bin/env python3
"""
Enhanced Commodity Time-Series Performance Scraper
Advanced scraper for comprehensive commodity analysis with multi-timeframe performance metrics

Target Commodities:
- Precious Metals: Gold, Silver, Platinum, Palladium
- Base Metals: Copper, Nickel, Zinc, Aluminum, Lead
- Battery Metals: Lithium, Cobalt  
- Energy Metals: Uranium

Performance Metrics for Each Commodity:
- Current Price (with currency and units)
- Daily Change (absolute $ and percentage)
- Weekly Change (absolute $ and percentage) 
- Monthly Change (absolute $ and percentage)
- Year-to-Date (YTD) performance (absolute $ and percentage)
- Year-over-Year (YoY) performance (absolute $ and percentage)

Data Sources:
1. Kitco.com - Precious metals historical data
2. Trading Economics - Multi-timeframe data
3. MarketWatch Commodities - Historical performance data
4. Yahoo Finance Commodities - Time-series data
5. LME (London Metal Exchange) - Official base metals data

Author: Mining Intelligence System
Date: 2025-08-04
"""

import asyncio
import json
import re
import requests
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urljoin, urlparse
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TimeSeriesPerformance:
    """Data structure for commodity time-series performance metrics"""
    commodity: str
    current_price: float
    currency: str
    unit: str
    
    # Change metrics
    daily_change_abs: Optional[float] = None
    daily_change_pct: Optional[float] = None
    weekly_change_abs: Optional[float] = None
    weekly_change_pct: Optional[float] = None
    monthly_change_abs: Optional[float] = None
    monthly_change_pct: Optional[float] = None
    ytd_change_abs: Optional[float] = None
    ytd_change_pct: Optional[float] = None
    yoy_change_abs: Optional[float] = None
    yoy_change_pct: Optional[float] = None
    
    # Metadata
    last_update: Optional[str] = None
    data_source: str = ""
    confidence_score: float = 0.0
    raw_data: Optional[Dict] = None

@dataclass
class CommodityAnalysis:
    """Comprehensive commodity analysis with investment insights"""
    commodity: str
    category: str  # precious_metals, base_metals, battery_metals, energy_metals
    
    # Consolidated performance from multiple sources
    consensus_performance: Optional[TimeSeriesPerformance] = None
    source_data: Dict[str, TimeSeriesPerformance] = None
    
    # Analysis metrics  
    momentum_score: float = 0.0  # -10 to +10 scale
    volatility_index: float = 0.0
    trend_direction: str = "neutral"  # bullish, bearish, neutral
    support_resistance: Dict[str, float] = None
    
    # Investment insights
    investment_implications: List[str] = None
    risk_factors: List[str] = None
    opportunity_assessment: str = "neutral"

class EnhancedCommodityTimeScraper:
    """
    Advanced commodity scraper with comprehensive time-series analysis
    Implements anti-fragile design patterns with multiple data sources
    """
    
    def __init__(self):
        # User agents for anti-bot protection - initialize first
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.session = requests.Session()
        self.setup_session()
        
        # Target commodity categories
        self.target_commodities = {
            'precious_metals': ['gold', 'silver', 'platinum', 'palladium'],
            'base_metals': ['copper', 'nickel', 'zinc', 'aluminum', 'lead'],
            'battery_metals': ['lithium', 'cobalt'],
            'energy_metals': ['uranium']
        }
        
        # Enhanced data source configurations with time-series capabilities
        self.data_sources = {
            'kitco': {
                'name': 'Kitco.com',
                'base_url': 'https://www.kitco.com',
                'specialties': ['precious_metals'],
                'has_historical': True,
                'endpoints': {
                    'gold': '/gold-price-today-usa/',
                    'silver': '/silver-price-today-usa/', 
                    'platinum': '/platinum-price-today-usa/',
                    'palladium': '/palladium-price-today-usa/',
                    'charts': '/price/precious-metals'
                },
                'selectors': {
                    'current_price': ['.price', '.current-price', '#sp-price', '.price-value'],
                    'daily_change': ['.change', '.price-change', '.change-percent'],
                    'charts_data': ['.price-chart', '.chart-container', '.highcharts-container'],
                    'performance_table': ['table.price-table', '.performance-data']
                }
            },
            'trading_economics': {
                'name': 'Trading Economics',
                'base_url': 'https://tradingeconomics.com',
                'specialties': ['all_commodities'],
                'has_historical': True,
                'endpoints': {
                    'commodities': '/commodities',
                    'gold': '/commodity/gold',
                    'silver': '/commodity/silver',
                    'copper': '/commodity/copper',
                    'platinum': '/commodity/platinum',
                    'palladium': '/commodity/palladium',
                    'aluminum': '/commodity/aluminum',
                    'zinc': '/commodity/zinc',
                    'nickel': '/commodity/nickel',
                    'lithium': '/commodity/lithium',
                    'uranium': '/commodity/uranium',
                    'cobalt': '/commodity/cobalt'
                },
                'selectors': {
                    'current_price': ['.price-current', '.te-price', 'table.table-hover td:nth-child(2)'],
                    'change_data': ['.change-percent', '.te-change', 'table.table-hover td:nth-child(3)'],
                    'performance_metrics': ['.forecast-data', '.historical-data', '.performance-table'],
                    'chart_data': ['.chart-container', '.highcharts-container']
                }
            },
            'marketwatch': {
                'name': 'MarketWatch Commodities',
                'base_url': 'https://www.marketwatch.com',
                'specialties': ['all_commodities'],
                'has_historical': True,
                'endpoints': {
                    'commodities': '/investing/futures',
                    'gold': '/investing/future/gold',
                    'silver': '/investing/future/silver',
                    'copper': '/investing/future/copper',
                    'platinum': '/investing/future/platinum',
                    'crude_oil': '/investing/future/crude%20oil'
                },
                'selectors': {
                    'current_price': ['.price', '.last-price', '.intraday__price'],
                    'change_metrics': ['.change', '.change--up', '.change--down'],
                    'performance_data': ['.performance', '.historical-performance'],
                    'volume_data': ['.volume', '.trading-volume']
                }
            },
            'yahoo_finance': {
                'name': 'Yahoo Finance Commodities',
                'base_url': 'https://finance.yahoo.com',
                'specialties': ['all_commodities'],
                'has_historical': True,
                'endpoints': {
                    'gold': '/quote/GC=F',
                    'silver': '/quote/SI=F',
                    'copper': '/quote/HG=F',
                    'platinum': '/quote/PL=F',
                    'palladium': '/quote/PA=F',
                    'crude_oil': '/quote/CL=F'
                },
                'selectors': {
                    'current_price': ['[data-symbol] [data-field="regularMarketPrice"]', '.Trsdu\\(0\\.3s\\)'],
                    'change_data': ['[data-field="regularMarketChange"]', '[data-field="regularMarketChangePercent"]'],
                    'historical_data': ['.historical-prices', '.chart-container'],
                    'summary_data': ['.summary', '.quote-summary']
                }
            },
            'lme': {
                'name': 'London Metal Exchange',
                'base_url': 'https://www.lme.com',
                'specialties': ['base_metals'],
                'has_historical': True,
                'endpoints': {
                    'copper': '/Metals/Non-ferrous/Copper',
                    'aluminum': '/Metals/Non-ferrous/Aluminium',
                    'zinc': '/Metals/Non-ferrous/Zinc',
                    'nickel': '/Metals/Non-ferrous/Nickel',
                    'lead': '/Metals/Non-ferrous/Lead'
                },
                'selectors': {
                    'official_price': ['.lme-price', '.official-price', '.settlement-price'],
                    'cash_price': ['.cash-price', '.spot-price'],
                    'forward_prices': ['.forward-prices', '.futures-data'],
                    'volume_data': ['.volume-data', '.trading-stats']
                }
            }
        }
        
        # Results storage
        self.scraped_data = {}
        self.analysis_results = {}
        self.performance_log = []
        self.errors = []
        
    def setup_session(self):
        """Configure session with comprehensive anti-bot protection"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Configure timeouts and retries
        self.session.timeout = 30
        
    def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Implement ethical delay patterns"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Ethical delay: {delay:.2f} seconds")
        time.sleep(delay)
        
    def safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Safe HTTP requests with comprehensive error handling and retry logic
        """
        for attempt in range(max_retries):
            try:
                # Rotate user agent for each attempt
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                logger.info(f"Requesting: {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"Success: {url} - Content length: {len(response.content)}")
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden: {url} - Bot detection likely")
                    if attempt < max_retries - 1:
                        self.random_delay(5.0, 10.0)  # Longer delay for bot detection
                elif response.status_code == 429:
                    logger.warning(f"429 Rate Limited: {url}")
                    if attempt < max_retries - 1:
                        self.random_delay(15.0, 25.0)  # Extended delay for rate limiting
                elif response.status_code == 404:
                    logger.error(f"404 Not Found: {url}")
                    break  # Don't retry 404s
                else:
                    logger.warning(f"HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout: {url}")
                if attempt < max_retries - 1:
                    self.random_delay(3.0, 6.0)
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error: {url}")
                if attempt < max_retries - 1:
                    self.random_delay(5.0, 10.0)
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception for {url}: {e}")
                if attempt < max_retries - 1:
                    self.random_delay(3.0, 6.0)
                    
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
        
    async def scrape_comprehensive_commodity_data(self) -> Dict[str, Any]:
        """
        Execute comprehensive commodity scraping with time-series performance analysis
        """
        start_time = datetime.now(timezone.utc)
        logger.info("Starting comprehensive commodity time-series analysis...")
        
        results = {
            'scraping_started': start_time.isoformat(),
            'target_commodities': self.target_commodities,
            'commodity_analysis': {},
            'performance_rankings': {},
            'market_intelligence': {},
            'data_sources_used': {},
            'performance_log': [],
            'errors': [],
            'summary': {}
        }
        
        # Scrape each commodity category
        for category, commodities in self.target_commodities.items():
            logger.info(f"Processing {category}: {commodities}")
            results['commodity_analysis'][category] = {}
            
            for commodity in commodities:
                try:
                    commodity_analysis = await self.analyze_commodity_comprehensive(commodity, category)
                    results['commodity_analysis'][category][commodity] = commodity_analysis
                    
                    logger.info(f"✅ Completed analysis for {commodity}")
                    
                    # Ethical delay between commodities
                    self.random_delay(3.0, 6.0)
                    
                except Exception as e:
                    error_msg = f"Failed to analyze {commodity}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
        
        # Generate performance rankings and market intelligence
        results['performance_rankings'] = self.generate_performance_rankings(results['commodity_analysis'])
        results['market_intelligence'] = self.generate_market_intelligence(results['commodity_analysis'])
        results['data_sources_used'] = self.compile_data_sources_summary()
        
        # Finalize results
        end_time = datetime.now(timezone.utc)
        results['scraping_completed'] = end_time.isoformat()
        results['total_duration'] = (end_time - start_time).total_seconds()
        results['performance_log'] = self.performance_log
        results['errors'] = self.errors
        results['summary'] = self.generate_comprehensive_summary(results)
        
        # Save results
        await self.save_comprehensive_results(results)
        
        return results
        
    async def analyze_commodity_comprehensive(self, commodity: str, category: str) -> CommodityAnalysis:
        """
        Perform comprehensive analysis of a single commodity across all relevant data sources
        """
        logger.info(f"Analyzing {commodity} ({category}) across all data sources...")
        
        analysis = CommodityAnalysis(
            commodity=commodity,
            category=category,
            source_data={},
            investment_implications=[],
            risk_factors=[],
            support_resistance={}
        )
        
        # Identify relevant data sources for this commodity
        relevant_sources = self.get_relevant_sources(commodity, category)
        
        source_performances = []
        
        # Scrape each relevant source
        for source_name in relevant_sources:
            try:
                source_config = self.data_sources[source_name]
                performance_data = await self.scrape_source_time_series(commodity, source_name, source_config)
                
                if performance_data:
                    analysis.source_data[source_name] = performance_data
                    source_performances.append(performance_data)
                    
                    logger.info(f"✓ {source_name}: ${performance_data.current_price:.2f} {performance_data.currency}")
                
                # Respectful delay between sources
                self.random_delay(2.0, 4.0)
                
            except Exception as e:
                error_msg = f"Failed to scrape {commodity} from {source_name}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
                continue
        
        # Generate consensus performance from multiple sources
        if source_performances:
            analysis.consensus_performance = self.calculate_consensus_performance(source_performances)
            analysis.momentum_score = self.calculate_momentum_score(analysis.consensus_performance)
            analysis.volatility_index = self.calculate_volatility_index(source_performances)
            analysis.trend_direction = self.determine_trend_direction(analysis.consensus_performance)
            analysis.investment_implications = self.generate_investment_implications(commodity, analysis.consensus_performance)
            analysis.risk_factors = self.identify_risk_factors(commodity, analysis.consensus_performance)
            analysis.opportunity_assessment = self.assess_opportunity(analysis.consensus_performance, analysis.momentum_score)
        
        return analysis
        
    def get_relevant_sources(self, commodity: str, category: str) -> List[str]:
        """Determine which data sources are most relevant for a specific commodity"""
        relevant_sources = []
        
        for source_name, config in self.data_sources.items():
            # Check if source covers this commodity category
            if 'all_commodities' in config['specialties'] or category in config['specialties']:
                # Check if source has specific endpoint for this commodity
                if commodity in config['endpoints'] or 'commodities' in config['endpoints']:
                    relevant_sources.append(source_name)
        
        # Prioritize sources based on commodity type
        if category == 'precious_metals' and 'kitco' in relevant_sources:
            relevant_sources = ['kitco'] + [s for s in relevant_sources if s != 'kitco']
        elif category == 'base_metals' and 'lme' in relevant_sources:
            relevant_sources = ['lme'] + [s for s in relevant_sources if s != 'lme']
            
        return relevant_sources
        
    async def scrape_source_time_series(self, commodity: str, source_name: str, source_config: Dict) -> Optional[TimeSeriesPerformance]:
        """
        Scrape comprehensive time-series performance data from a specific source
        """
        performance_start = time.time()
        
        try:
            # Determine the best URL for this commodity
            url = self.construct_commodity_url(commodity, source_config)
            if not url:
                return None
                
            response = self.safe_request(url)
            if not response:
                return None
                
            # Extract time-series performance data
            performance_data = self.extract_time_series_performance(
                response.text, commodity, source_name, source_config
            )
            
            if performance_data:
                performance_data.data_source = source_name
                performance_data.last_update = datetime.now(timezone.utc).isoformat()
                performance_data.confidence_score = self.calculate_confidence_score(performance_data, source_name)
                
                # Log performance metrics
                response_time = time.time() - performance_start
                self.performance_log.append({
                    'source': source_name,
                    'commodity': commodity,
                    'url': url,
                    'success': True,
                    'response_time': response_time,
                    'data_quality': 'high' if performance_data.confidence_score > 0.7 else 'medium',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                
            return performance_data
            
        except Exception as e:
            response_time = time.time() - performance_start
            error_msg = f"Error scraping {commodity} from {source_name}: {str(e)}"
            logger.error(error_msg)
            
            self.performance_log.append({
                'source': source_name,
                'commodity': commodity,
                'success': False,
                'response_time': response_time,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            return None
            
    def construct_commodity_url(self, commodity: str, source_config: Dict) -> Optional[str]:
        """Construct the optimal URL for scraping a specific commodity"""
        base_url = source_config['base_url']
        endpoints = source_config['endpoints']
        
        # Check for specific commodity endpoint
        if commodity in endpoints:
            return base_url + endpoints[commodity]
        elif 'commodities' in endpoints:
            return base_url + endpoints['commodities']
        
        return None
        
    def extract_time_series_performance(self, content: str, commodity: str, source_name: str, source_config: Dict) -> Optional[TimeSeriesPerformance]:
        """
        Extract comprehensive time-series performance metrics from scraped content
        Advanced extraction with multiple fallback patterns
        """
        
        # Initialize performance data structure
        performance = TimeSeriesPerformance(
            commodity=commodity,
            current_price=0.0,
            currency='USD',
            unit=self.get_commodity_unit(commodity)
        )
        
        # Source-specific extraction strategies
        if source_name == 'kitco':
            performance = self.extract_kitco_performance(content, commodity, performance)
        elif source_name == 'trading_economics':
            performance = self.extract_trading_economics_performance(content, commodity, performance)
        elif source_name == 'marketwatch':
            performance = self.extract_marketwatch_performance(content, commodity, performance)
        elif source_name == 'yahoo_finance':
            performance = self.extract_yahoo_finance_performance(content, commodity, performance)
        elif source_name == 'lme':
            performance = self.extract_lme_performance(content, commodity, performance)
        
        # Validate and return
        if performance.current_price > 0:
            return performance
        else:
            logger.warning(f"No valid price data extracted for {commodity} from {source_name}")
            return None
            
    def extract_kitco_performance(self, content: str, commodity: str, performance: TimeSeriesPerformance) -> TimeSeriesPerformance:
        """Extract time-series data from Kitco (specialized for precious metals)"""
        
        # Current price patterns for Kitco
        price_patterns = [
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>.*?\$?([\d,]+\.?\d*)',
            r'id="sp-price"[^>]*>.*?\$?([\d,]+\.?\d*)',
            r'<div[^>]*class="[^"]*current-price[^"]*"[^>]*>.*?\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    performance.current_price = float(match.group(1).replace(',', ''))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Daily change patterns
        daily_change_patterns = [
            r'<span[^>]*class="[^"]*change[^"]*"[^>]*>.*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)',
            r'change[^>]*>.*?([+-]?\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%)'
        ]
        
        for pattern in daily_change_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    abs_change = match.group(1).replace('$', '').replace(',', '').strip()
                    pct_change = match.group(2).replace('%', '').strip()
                    
                    performance.daily_change_abs = float(abs_change)
                    performance.daily_change_pct = float(pct_change)
                    break
                except (ValueError, IndexError):
                    continue
        
        # Look for historical performance data in tables or charts
        historical_patterns = [
            r'1\s*Week.*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)',
            r'Weekly.*?([+-]?\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%)',
            r'1\s*Month.*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)',
            r'Monthly.*?([+-]?\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%)',
            r'YTD.*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)',
            r'Year.*?Date.*?([+-]?\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%)',
            r'1\s*Year.*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)',
            r'12.*?Month.*?([+-]?\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%)'
        ]
        
        # Extract weekly change
        weekly_pattern = r'(?:1\s*Week|Weekly).*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)'
        match = re.search(weekly_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                performance.weekly_change_abs = float(match.group(1).replace('$', '').replace(',', '').strip())
                performance.weekly_change_pct = float(match.group(2).replace('%', '').strip())
            except (ValueError, IndexError):
                pass
        
        # Extract monthly change
        monthly_pattern = r'(?:1\s*Month|Monthly).*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)'
        match = re.search(monthly_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                performance.monthly_change_abs = float(match.group(1).replace('$', '').replace(',', '').strip())
                performance.monthly_change_pct = float(match.group(2).replace('%', '').strip())
            except (ValueError, IndexError):
                pass
        
        # Extract YTD change
        ytd_pattern = r'(?:YTD|Year.*?Date).*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)'
        match = re.search(ytd_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                performance.ytd_change_abs = float(match.group(1).replace('$', '').replace(',', '').strip())
                performance.ytd_change_pct = float(match.group(2).replace('%', '').strip())
            except (ValueError, IndexError):
                pass
        
        # Extract YoY change  
        yoy_pattern = r'(?:1\s*Year|12.*?Month|Year.*?Year).*?([+-]?\$?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)'
        match = re.search(yoy_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                performance.yoy_change_abs = float(match.group(1).replace('$', '').replace(',', '').strip())
                performance.yoy_change_pct = float(match.group(2).replace('%', '').strip())
            except (ValueError, IndexError):
                pass
        
        return performance
        
    def extract_trading_economics_performance(self, content: str, commodity: str, performance: TimeSeriesPerformance) -> TimeSeriesPerformance:
        """Extract time-series data from Trading Economics (comprehensive data)"""
        
        # Trading Economics table extraction patterns
        table_pattern = r'<tr[^>]*>.*?<td[^>]*>.*?' + commodity.title() + r'.*?</td>.*?<td[^>]*>.*?([\d,]+\.?\d*).*?</td>.*?<td[^>]*>.*?([+-]?[\d.]+%?).*?</td>'
        match = re.search(table_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                performance.current_price = float(match.group(1).replace(',', ''))
                change_str = match.group(2).replace('%', '').strip()
                performance.daily_change_pct = float(change_str)
            except (ValueError, IndexError):
                pass
        
        # Look for forecast and historical data sections
        forecast_patterns = [
            r'forecast.*?' + commodity + r'.*?([\d,]+\.?\d*).*?([+-]?[\d.]+%)',
            r'outlook.*?' + commodity + r'.*?([\d,]+\.?\d*).*?([+-]?[\d.]+%)'
        ]
        
        for pattern in forecast_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                # This could be forward-looking data - use cautiously
                break
        
        # Extract chart data if available (JSON embedded in page)
        chart_data_pattern = r'"historical":\s*\[(.*?)\]'
        match = re.search(chart_data_pattern, content, re.DOTALL)
        if match:
            try:
                # Parse historical data points for trend analysis
                historical_data = match.group(1)
                # Additional processing would go here for time-series analysis
            except:
                pass
        
        return performance
        
    def extract_marketwatch_performance(self, content: str, commodity: str, performance: TimeSeriesPerformance) -> TimeSeriesPerformance:
        """Extract time-series data from MarketWatch (futures data)"""
        
        # MarketWatch price extraction
        price_patterns = [
            r'<bg-quote[^>]*field="Last"[^>]*>.*?([\d,]+\.?\d*)',
            r'class="[^"]*intraday__price[^"]*"[^>]*>.*?([\d,]+\.?\d*)',
            r'data-module="LastPrice"[^>]*>.*?([\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    performance.current_price = float(match.group(1).replace(',', ''))
                    break
                except (ValueError, IndexError):
                    continue
        
        # MarketWatch change data
        change_patterns = [
            r'<bg-quote[^>]*field="Change"[^>]*>.*?([+-]?[\d,]+\.?\d*)',
            r'<bg-quote[^>]*field="PercentChange"[^>]*>.*?([+-]?[\d.]+)%',
            r'class="[^"]*change[^"]*"[^>]*>.*?([+-]?[\d,]+\.?\d*).*?\(([+-]?[\d.]+%?)\)'
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    if len(match.groups()) >= 2:
                        performance.daily_change_abs = float(match.group(1).replace(',', ''))
                        performance.daily_change_pct = float(match.group(2).replace('%', ''))
                    else:
                        # Single match - determine if it's absolute or percentage
                        value = match.group(1).replace(',', '')
                        if '%' in match.group(0):
                            performance.daily_change_pct = float(value.replace('%', ''))
                        else:
                            performance.daily_change_abs = float(value)
                    break
                except (ValueError, IndexError):
                    continue
        
        # Look for performance table data
        performance_table_pattern = r'<table[^>]*class="[^"]*performance[^"]*"[^>]*>(.*?)</table>'
        match = re.search(performance_table_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            table_content = match.group(1)
            
            # Extract different timeframe data from performance table
            timeframe_patterns = {
                'weekly': r'(?:1W|1 Week|Weekly).*?([+-]?[\d.]+%)',
                'monthly': r'(?:1M|1 Month|Monthly).*?([+-]?[\d.]+%)',
                'ytd': r'(?:YTD|Year to Date).*?([+-]?[\d.]+%)',
                'yearly': r'(?:1Y|1 Year|52W).*?([+-]?[\d.]+%)'
            }
            
            for timeframe, pattern in timeframe_patterns.items():
                match = re.search(pattern, table_content, re.IGNORECASE)
                if match:
                    try:
                        pct_value = float(match.group(1).replace('%', ''))
                        if timeframe == 'weekly':
                            performance.weekly_change_pct = pct_value
                        elif timeframe == 'monthly':
                            performance.monthly_change_pct = pct_value
                        elif timeframe == 'ytd':
                            performance.ytd_change_pct = pct_value
                        elif timeframe == 'yearly':
                            performance.yoy_change_pct = pct_value
                    except (ValueError, IndexError):
                        continue
        
        return performance
        
    def extract_yahoo_finance_performance(self, content: str, commodity: str, performance: TimeSeriesPerformance) -> TimeSeriesPerformance:
        """Extract time-series data from Yahoo Finance (comprehensive futures data)"""
        
        # Yahoo Finance uses specific data attributes
        price_patterns = [
            r'data-field="regularMarketPrice"[^>]*value="([\d,]+\.?\d*)"',
            r'data-symbol="[^"]*"[^>]*data-field="regularMarketPrice"[^>]*>.*?([\d,]+\.?\d*)',
            r'class="[^"]*Trsdu\(0\.3s\)[^"]*"[^>]*>.*?([\d,]+\.?\d*)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    performance.current_price = float(match.group(1).replace(',', ''))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Yahoo Finance change data
        change_abs_pattern = r'data-field="regularMarketChange"[^>]*value="([+-]?[\d,]+\.?\d*)"'
        match = re.search(change_abs_pattern, content, re.IGNORECASE)
        if match:
            try:
                performance.daily_change_abs = float(match.group(1).replace(',', ''))
            except (ValueError, IndexError):
                pass
        
        change_pct_pattern = r'data-field="regularMarketChangePercent"[^>]*value="([+-]?[\d.]+)"'
        match = re.search(change_pct_pattern, content, re.IGNORECASE)
        if match:
            try:
                performance.daily_change_pct = float(match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Look for historical data table
        historical_table_pattern = r'<table[^>]*class="[^"]*historical-prices[^"]*"[^>]*>(.*?)</table>'
        match = re.search(historical_table_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Process historical price table for trend analysis
            # This would require more sophisticated parsing
            pass
        
        # Look for summary statistics 
        summary_patterns = [
            r'52.*?Week.*?High.*?([\d,]+\.?\d*)',
            r'52.*?Week.*?Low.*?([\d,]+\.?\d*)',
            r'50.*?Day.*?Average.*?([\d,]+\.?\d*)',
            r'200.*?Day.*?Average.*?([\d,]+\.?\d*)'
        ]
        
        # These could be used for additional analysis
        
        return performance
        
    def extract_lme_performance(self, content: str, commodity: str, performance: TimeSeriesPerformance) -> TimeSeriesPerformance:
        """Extract time-series data from LME (official base metals data)"""
        
        # LME official price patterns
        official_price_patterns = [
            r'<span[^>]*class="[^"]*lme-price[^"]*"[^>]*>.*?([\d,]+\.?\d*)',
            r'Official.*?Price.*?([\d,]+\.?\d*)',
            r'Settlement.*?Price.*?([\d,]+\.?\d*)'
        ]
        
        for pattern in official_price_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    performance.current_price = float(match.group(1).replace(',', ''))
                    performance.currency = 'USD'
                    performance.unit = 'USD/tonne'  # LME standard
                    break
                except (ValueError, IndexError):
                    continue
        
        # LME cash vs 3-month price differential (indicator of market conditions)
        cash_price_pattern = r'Cash.*?Price.*?([\d,]+\.?\d*)'
        three_month_pattern = r'3.*?Month.*?Price.*?([\d,]+\.?\d*)'
        
        cash_match = re.search(cash_price_pattern, content, re.IGNORECASE)
        three_month_match = re.search(three_month_pattern, content, re.IGNORECASE)
        
        if cash_match and three_month_match:
            try:
                cash_price = float(cash_match.group(1).replace(',', ''))
                three_month_price = float(three_month_match.group(1).replace(',', ''))
                
                # Use cash price as current price
                performance.current_price = cash_price
                
                # Calculate contango/backwardation as a market indicator
                price_differential = three_month_price - cash_price
                differential_pct = (price_differential / cash_price) * 100
                
                # This differential can indicate market conditions
                # Positive = contango (future > spot), Negative = backwardation (spot > future)
                
            except (ValueError, IndexError):
                pass
        
        # LME volume and open interest data
        volume_pattern = r'Volume.*?([\d,]+)'
        volume_match = re.search(volume_pattern, content, re.IGNORECASE)
        if volume_match:
            # Volume data could be used for liquidity analysis
            pass
        
        return performance
        
    def get_commodity_unit(self, commodity: str) -> str:
        """Return the standard trading unit for a commodity"""
        units = {
            'gold': 'USD/oz',
            'silver': 'USD/oz', 
            'platinum': 'USD/oz',
            'palladium': 'USD/oz',
            'copper': 'USD/lb',
            'nickel': 'USD/lb',
            'zinc': 'USD/lb',
            'aluminum': 'USD/lb',
            'lead': 'USD/lb',
            'lithium': 'USD/tonne',
            'cobalt': 'USD/lb',
            'uranium': 'USD/lb'
        }
        return units.get(commodity, 'USD')
        
    def calculate_consensus_performance(self, source_performances: List[TimeSeriesPerformance]) -> TimeSeriesPerformance:
        """Calculate consensus performance metrics from multiple sources"""
        
        if not source_performances:
            return None
            
        # Initialize consensus with first source as template
        consensus = TimeSeriesPerformance(
            commodity=source_performances[0].commodity,
            current_price=0.0,
            currency=source_performances[0].currency,
            unit=source_performances[0].unit
        )
        
        # Collect all non-null values for each metric
        prices = [p.current_price for p in source_performances if p.current_price and p.current_price > 0]
        daily_abs = [p.daily_change_abs for p in source_performances if p.daily_change_abs is not None]
        daily_pct = [p.daily_change_pct for p in source_performances if p.daily_change_pct is not None]
        weekly_abs = [p.weekly_change_abs for p in source_performances if p.weekly_change_abs is not None]
        weekly_pct = [p.weekly_change_pct for p in source_performances if p.weekly_change_pct is not None]
        monthly_abs = [p.monthly_change_abs for p in source_performances if p.monthly_change_abs is not None]
        monthly_pct = [p.monthly_change_pct for p in source_performances if p.monthly_change_pct is not None]
        ytd_abs = [p.ytd_change_abs for p in source_performances if p.ytd_change_abs is not None]
        ytd_pct = [p.ytd_change_pct for p in source_performances if p.ytd_change_pct is not None]
        yoy_abs = [p.yoy_change_abs for p in source_performances if p.yoy_change_abs is not None]
        yoy_pct = [p.yoy_change_pct for p in source_performances if p.yoy_change_pct is not None]
        
        # Calculate consensus values (median is more robust than mean for financial data)
        if prices:
            consensus.current_price = sorted(prices)[len(prices)//2] if len(prices) > 1 else prices[0]
        if daily_abs:
            consensus.daily_change_abs = sorted(daily_abs)[len(daily_abs)//2] if len(daily_abs) > 1 else daily_abs[0]
        if daily_pct:
            consensus.daily_change_pct = sorted(daily_pct)[len(daily_pct)//2] if len(daily_pct) > 1 else daily_pct[0]
        if weekly_abs:
            consensus.weekly_change_abs = sorted(weekly_abs)[len(weekly_abs)//2] if len(weekly_abs) > 1 else weekly_abs[0]
        if weekly_pct:
            consensus.weekly_change_pct = sorted(weekly_pct)[len(weekly_pct)//2] if len(weekly_pct) > 1 else weekly_pct[0]
        if monthly_abs:
            consensus.monthly_change_abs = sorted(monthly_abs)[len(monthly_abs)//2] if len(monthly_abs) > 1 else monthly_abs[0]
        if monthly_pct:
            consensus.monthly_change_pct = sorted(monthly_pct)[len(monthly_pct)//2] if len(monthly_pct) > 1 else monthly_pct[0]
        if ytd_abs:
            consensus.ytd_change_abs = sorted(ytd_abs)[len(ytd_abs)//2] if len(ytd_abs) > 1 else ytd_abs[0]
        if ytd_pct:
            consensus.ytd_change_pct = sorted(ytd_pct)[len(ytd_pct)//2] if len(ytd_pct) > 1 else ytd_pct[0]
        if yoy_abs:
            consensus.yoy_change_abs = sorted(yoy_abs)[len(yoy_abs)//2] if len(yoy_abs) > 1 else yoy_abs[0]
        if yoy_pct:
            consensus.yoy_change_pct = sorted(yoy_pct)[len(yoy_pct)//2] if len(yoy_pct) > 1 else yoy_pct[0]
        
        # Calculate confidence score based on data availability and consistency
        data_points = sum([
            1 if prices else 0,
            1 if daily_pct else 0,
            1 if weekly_pct else 0,
            1 if monthly_pct else 0,
            1 if ytd_pct else 0,
            1 if yoy_pct else 0
        ])
        
        source_count = len(source_performances)
        consensus.confidence_score = min(1.0, (data_points / 6.0) * (source_count / 3.0))
        
        consensus.last_update = datetime.now(timezone.utc).isoformat()
        
        return consensus
        
    def calculate_momentum_score(self, performance: TimeSeriesPerformance) -> float:
        """Calculate momentum score from -10 (strong bearish) to +10 (strong bullish)"""
        if not performance:
            return 0.0
            
        scores = []
        weights = []
        
        # Daily momentum (weight: 1)
        if performance.daily_change_pct is not None:
            daily_score = max(-2, min(2, performance.daily_change_pct / 2.5))  # Normalize to -2 to +2
            scores.append(daily_score)
            weights.append(1)
        
        # Weekly momentum (weight: 2)
        if performance.weekly_change_pct is not None:
            weekly_score = max(-2.5, min(2.5, performance.weekly_change_pct / 4.0))  # Normalize to -2.5 to +2.5
            scores.append(weekly_score)
            weights.append(2)
        
        # Monthly momentum (weight: 2)
        if performance.monthly_change_pct is not None:
            monthly_score = max(-2.5, min(2.5, performance.monthly_change_pct / 6.0))  # Normalize to -2.5 to +2.5
            scores.append(monthly_score)
            weights.append(2)
        
        # YTD momentum (weight: 3)
        if performance.ytd_change_pct is not None:
            ytd_score = max(-3, min(3, performance.ytd_change_pct / 15.0))  # Normalize to -3 to +3
            scores.append(ytd_score)
            weights.append(3)
        
        # Calculate weighted average
        if scores:
            weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / sum(weights)
            return round(weighted_score, 1)
        
        return 0.0
        
    def calculate_volatility_index(self, source_performances: List[TimeSeriesPerformance]) -> float:
        """Calculate volatility index based on price dispersion across sources and timeframes"""
        if not source_performances:
            return 0.0
            
        # Collect price variations
        prices = [p.current_price for p in source_performances if p.current_price and p.current_price > 0]
        daily_changes = [abs(p.daily_change_pct) for p in source_performances if p.daily_change_pct is not None]
        
        volatility_factors = []
        
        # Price dispersion across sources
        if len(prices) > 1:
            avg_price = sum(prices) / len(prices)
            price_std = (sum((p - avg_price) ** 2 for p in prices) / len(prices)) ** 0.5
            price_cv = price_std / avg_price if avg_price > 0 else 0
            volatility_factors.append(price_cv * 10)  # Scale to reasonable range
        
        # Daily change magnitude
        if daily_changes:
            avg_daily_change = sum(daily_changes) / len(daily_changes)
            volatility_factors.append(avg_daily_change / 2)  # Scale to reasonable range
        
        # Return average of volatility factors
        if volatility_factors:
            return round(sum(volatility_factors) / len(volatility_factors), 1)
        
        return 0.0
        
    def determine_trend_direction(self, performance: TimeSeriesPerformance) -> str:
        """Determine overall trend direction based on multi-timeframe analysis"""
        if not performance:
            return "neutral"
            
        # Collect available percentage changes
        changes = []
        weights = []
        
        if performance.daily_change_pct is not None:
            changes.append(performance.daily_change_pct)
            weights.append(1)
        if performance.weekly_change_pct is not None:
            changes.append(performance.weekly_change_pct)
            weights.append(2)
        if performance.monthly_change_pct is not None:
            changes.append(performance.monthly_change_pct)
            weights.append(2)
        if performance.ytd_change_pct is not None:
            changes.append(performance.ytd_change_pct)
            weights.append(3)
        if performance.yoy_change_pct is not None:
            changes.append(performance.yoy_change_pct)
            weights.append(2)
        
        if not changes:
            return "neutral"
            
        # Calculate weighted average trend
        weighted_trend = sum(change * weight for change, weight in zip(changes, weights)) / sum(weights)
        
        if weighted_trend > 2.0:
            return "bullish"
        elif weighted_trend < -2.0:
            return "bearish"
        else:
            return "neutral"
            
    def generate_investment_implications(self, commodity: str, performance: TimeSeriesPerformance) -> List[str]:
        """Generate investment implications based on performance analysis"""
        implications = []
        
        if not performance:
            return implications
            
        # Precious metals implications
        if commodity in ['gold', 'silver']:
            if performance.ytd_change_pct and performance.ytd_change_pct > 10:
                implications.append(f"Strong {commodity} YTD performance (+{performance.ytd_change_pct:.1f}%) suggests flight-to-safety or inflation hedge demand")
            if performance.daily_change_pct and abs(performance.daily_change_pct) > 2:
                implications.append(f"High daily volatility ({performance.daily_change_pct:+.1f}%) indicates market uncertainty or news-driven trading")
        
        # Base metals implications
        elif commodity == 'copper':
            if performance.monthly_change_pct and performance.monthly_change_pct > 5:
                implications.append("Copper strength indicates robust industrial demand and economic growth expectations")
            elif performance.monthly_change_pct and performance.monthly_change_pct < -5:
                implications.append("Copper weakness may signal economic slowdown concerns or supply normalization")
        
        # Battery metals implications  
        elif commodity in ['lithium', 'cobalt']:
            if performance.yoy_change_pct and performance.yoy_change_pct > 20:
                implications.append(f"{commodity.title()} surge driven by EV adoption and battery manufacturing growth")
            elif performance.monthly_change_pct and performance.monthly_change_pct < -10:
                implications.append(f"{commodity.title()} correction potentially due to supply increases or demand normalization")
        
        # Energy metals implications
        elif commodity == 'uranium':
            if performance.ytd_change_pct and performance.ytd_change_pct > 15:
                implications.append("Uranium strength reflects nuclear power renaissance and supply constraints")
        
        # General momentum implications
        if performance.weekly_change_pct and performance.monthly_change_pct:
            if performance.weekly_change_pct > 0 and performance.monthly_change_pct > 0:
                implications.append("Consistent multi-timeframe gains suggest sustained momentum")
            elif performance.weekly_change_pct < 0 and performance.monthly_change_pct > 0:
                implications.append("Recent weakness against longer-term strength may present tactical buying opportunity")
        
        return implications
        
    def identify_risk_factors(self, commodity: str, performance: TimeSeriesPerformance) -> List[str]:
        """Identify key risk factors based on performance patterns"""
        risks = []
        
        if not performance:
            return risks
            
        # High volatility risks
        if performance.daily_change_pct and abs(performance.daily_change_pct) > 3:
            risks.append("High short-term volatility increases position risk and timing challenges")
        
        # Momentum exhaustion risks
        if performance.ytd_change_pct and performance.ytd_change_pct > 30:
            risks.append("Extended YTD gains may be vulnerable to profit-taking and trend reversal")
        elif performance.ytd_change_pct and performance.ytd_change_pct < -20:
            risks.append("Significant YTD losses suggest fundamental headwinds or oversupply conditions")
        
        # Divergence risks
        if (performance.daily_change_pct and performance.monthly_change_pct and 
            performance.daily_change_pct * performance.monthly_change_pct < 0):
            risks.append("Short-term vs long-term trend divergence indicates potential inflection point")
        
        # Commodity-specific risks
        if commodity in ['gold', 'silver']:
            risks.append("Dollar strength and rising real yields pose headwinds to precious metals")
        elif commodity == 'copper':
            risks.append("Global manufacturing slowdown and China demand concerns")
        elif commodity in ['lithium', 'cobalt']:
            risks.append("EV market volatility and rapid supply capacity additions")
        elif commodity == 'uranium':
            risks.append("Political and regulatory changes affecting nuclear power development")
        
        return risks
        
    def assess_opportunity(self, performance: TimeSeriesPerformance, momentum_score: float) -> str:
        """Assess investment opportunity based on performance and momentum"""
        if not performance:
            return "neutral"
            
        # Strong positive momentum with reasonable valuations
        if momentum_score > 5 and performance.ytd_change_pct and performance.ytd_change_pct < 25:
            return "attractive"
        
        # Oversold conditions with stabilizing momentum
        elif momentum_score > -2 and performance.ytd_change_pct and performance.ytd_change_pct < -15:
            return "contrarian_opportunity"
        
        # Extended gains with high momentum
        elif momentum_score > 7 and performance.ytd_change_pct and performance.ytd_change_pct > 35:
            return "proceed_with_caution"
        
        # Weak momentum and poor performance
        elif momentum_score < -5 and performance.ytd_change_pct and performance.ytd_change_pct < -10:
            return "avoid"
        
        return "neutral"
        
    def calculate_confidence_score(self, performance: TimeSeriesPerformance, source_name: str) -> float:
        """Calculate confidence score for extracted data"""
        score = 0.0
        
        # Base score for having a valid price
        if performance.current_price and performance.current_price > 0:
            score += 0.3
        
        # Bonus for having change data
        if performance.daily_change_pct is not None:
            score += 0.2
        if performance.weekly_change_pct is not None:
            score += 0.15
        if performance.monthly_change_pct is not None:
            score += 0.15
        if performance.ytd_change_pct is not None:
            score += 0.1
        if performance.yoy_change_pct is not None:
            score += 0.1
        
        # Source reliability bonus
        source_reliability = {
            'kitco': 0.95,
            'trading_economics': 0.85,
            'yahoo_finance': 0.90,
            'marketwatch': 0.80,
            'lme': 0.95
        }
        
        score *= source_reliability.get(source_name, 0.70)
        
        return min(1.0, score)
        
    def generate_performance_rankings(self, commodity_analysis: Dict) -> Dict[str, Any]:
        """Generate performance rankings across different timeframes"""
        rankings = {
            'daily_performers': {'best': [], 'worst': []},
            'weekly_performers': {'best': [], 'worst': []},
            'monthly_performers': {'best': [], 'worst': []},
            'ytd_performers': {'best': [], 'worst': []},
            'yoy_performers': {'best': [], 'worst': []},
            'momentum_leaders': {'bullish': [], 'bearish': []},
            'opportunity_rankings': {'attractive': [], 'contrarian': [], 'caution': [], 'avoid': []}
        }
        
        # Collect all commodities with performance data
        all_commodities = []
        for category, commodities in commodity_analysis.items():
            for commodity, analysis in commodities.items():
                if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance:
                    all_commodities.append({
                        'commodity': commodity,
                        'category': category,
                        'analysis': analysis,
                        'performance': analysis.consensus_performance
                    })
        
        # Daily performance rankings
        daily_commodities = [c for c in all_commodities if c['performance'].daily_change_pct is not None]
        daily_sorted = sorted(daily_commodities, key=lambda x: x['performance'].daily_change_pct, reverse=True)
        
        rankings['daily_performers']['best'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].daily_change_pct,
                'change_abs': c['performance'].daily_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in daily_sorted[:5]
        ]
        
        rankings['daily_performers']['worst'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'], 
                'change_pct': c['performance'].daily_change_pct,
                'change_abs': c['performance'].daily_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in daily_sorted[-5:]
        ]
        
        # Weekly performance rankings
        weekly_commodities = [c for c in all_commodities if c['performance'].weekly_change_pct is not None]
        weekly_sorted = sorted(weekly_commodities, key=lambda x: x['performance'].weekly_change_pct, reverse=True)
        
        rankings['weekly_performers']['best'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].weekly_change_pct,
                'change_abs': c['performance'].weekly_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in weekly_sorted[:5]
        ]
        
        rankings['weekly_performers']['worst'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].weekly_change_pct,
                'change_abs': c['performance'].weekly_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in weekly_sorted[-5:]
        ]
        
        # Monthly performance rankings
        monthly_commodities = [c for c in all_commodities if c['performance'].monthly_change_pct is not None]
        monthly_sorted = sorted(monthly_commodities, key=lambda x: x['performance'].monthly_change_pct, reverse=True)
        
        rankings['monthly_performers']['best'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].monthly_change_pct,
                'change_abs': c['performance'].monthly_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in monthly_sorted[:5]
        ]
        
        rankings['monthly_performers']['worst'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].monthly_change_pct,
                'change_abs': c['performance'].monthly_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in monthly_sorted[-5:]
        ]
        
        # YTD performance rankings
        ytd_commodities = [c for c in all_commodities if c['performance'].ytd_change_pct is not None]
        ytd_sorted = sorted(ytd_commodities, key=lambda x: x['performance'].ytd_change_pct, reverse=True)
        
        rankings['ytd_performers']['best'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].ytd_change_pct,
                'change_abs': c['performance'].ytd_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in ytd_sorted[:5]
        ]
        
        rankings['ytd_performers']['worst'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].ytd_change_pct,
                'change_abs': c['performance'].ytd_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in ytd_sorted[-5:]
        ]
        
        # YoY performance rankings
        yoy_commodities = [c for c in all_commodities if c['performance'].yoy_change_pct is not None]
        yoy_sorted = sorted(yoy_commodities, key=lambda x: x['performance'].yoy_change_pct, reverse=True)
        
        rankings['yoy_performers']['best'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].yoy_change_pct,
                'change_abs': c['performance'].yoy_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in yoy_sorted[:5]
        ]
        
        rankings['yoy_performers']['worst'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'change_pct': c['performance'].yoy_change_pct,
                'change_abs': c['performance'].yoy_change_abs,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in yoy_sorted[-5:]
        ]
        
        # Momentum rankings
        momentum_sorted = sorted(all_commodities, key=lambda x: x['analysis'].momentum_score, reverse=True)
        
        rankings['momentum_leaders']['bullish'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'momentum_score': c['analysis'].momentum_score,
                'trend_direction': c['analysis'].trend_direction,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in momentum_sorted[:5] if c['analysis'].momentum_score > 0
        ]
        
        rankings['momentum_leaders']['bearish'] = [
            {
                'commodity': c['commodity'],
                'category': c['category'],
                'momentum_score': c['analysis'].momentum_score,
                'trend_direction': c['analysis'].trend_direction,
                'current_price': c['performance'].current_price,
                'unit': c['performance'].unit
            }
            for c in momentum_sorted[-5:] if c['analysis'].momentum_score < 0
        ]
        
        # Opportunity rankings
        for commodity_data in all_commodities:
            opportunity = commodity_data['analysis'].opportunity_assessment
            commodity_info = {
                'commodity': commodity_data['commodity'],
                'category': commodity_data['category'],
                'opportunity_assessment': opportunity,
                'momentum_score': commodity_data['analysis'].momentum_score,
                'current_price': commodity_data['performance'].current_price,
                'unit': commodity_data['performance'].unit,
                'ytd_change_pct': commodity_data['performance'].ytd_change_pct
            }
            
            if opportunity == 'attractive':
                rankings['opportunity_rankings']['attractive'].append(commodity_info)
            elif opportunity == 'contrarian_opportunity':
                rankings['opportunity_rankings']['contrarian'].append(commodity_info)
            elif opportunity == 'proceed_with_caution':
                rankings['opportunity_rankings']['caution'].append(commodity_info)
            elif opportunity == 'avoid':
                rankings['opportunity_rankings']['avoid'].append(commodity_info)
        
        return rankings
        
    def generate_market_intelligence(self, commodity_analysis: Dict) -> Dict[str, Any]:
        """Generate comprehensive market intelligence and insights"""
        intelligence = {
            'market_overview': {},
            'sector_analysis': {},
            'cross_commodity_correlations': {},
            'macro_economic_implications': {},
            'trading_opportunities': {},
            'risk_assessment': {},
            'outlook_summary': {}
        }
        
        # Market overview
        all_commodities = []
        for category, commodities in commodity_analysis.items():
            for commodity, analysis in commodities.items():
                if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance:
                    all_commodities.append({
                        'commodity': commodity,
                        'category': category,
                        'analysis': analysis
                    })
        
        total_commodities = len(all_commodities)
        bullish_count = len([c for c in all_commodities if c['analysis'].trend_direction == 'bullish'])
        bearish_count = len([c for c in all_commodities if c['analysis'].trend_direction == 'bearish'])
        neutral_count = total_commodities - bullish_count - bearish_count
        
        intelligence['market_overview'] = {
            'total_commodities_analyzed': total_commodities,
            'market_sentiment_distribution': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            },
            'overall_market_sentiment': 'bullish' if bullish_count > bearish_count else 'bearish' if bearish_count > bullish_count else 'mixed',
            'high_momentum_commodities': len([c for c in all_commodities if c['analysis'].momentum_score > 5]),
            'volatile_commodities': len([c for c in all_commodities if c['analysis'].volatility_index > 5])
        }
        
        # Sector analysis
        for category in self.target_commodities.keys():
            if category in commodity_analysis:
                sector_commodities = [
                    (commodity, analysis) for commodity, analysis in commodity_analysis[category].items()
                    if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance
                ]
                
                if sector_commodities:
                    sector_momentum = sum(analysis.momentum_score for _, analysis in sector_commodities) / len(sector_commodities)
                    sector_volatility = sum(analysis.volatility_index for _, analysis in sector_commodities) / len(sector_commodities)
                    
                    ytd_changes = [
                        analysis.consensus_performance.ytd_change_pct 
                        for _, analysis in sector_commodities 
                        if analysis.consensus_performance.ytd_change_pct is not None
                    ]
                    avg_ytd = sum(ytd_changes) / len(ytd_changes) if ytd_changes else 0
                    
                    intelligence['sector_analysis'][category] = {
                        'commodities_count': len(sector_commodities),
                        'average_momentum_score': round(sector_momentum, 1),
                        'average_volatility': round(sector_volatility, 1),
                        'average_ytd_performance': round(avg_ytd, 1),
                        'sector_outlook': 'positive' if sector_momentum > 2 else 'negative' if sector_momentum < -2 else 'neutral'
                    }
        
        # Cross-commodity correlations (simplified analysis)
        intelligence['cross_commodity_correlations'] = {
            'precious_metals_cohesion': 'Analyzing gold-silver correlation and precious metals trends',
            'base_metals_industrial_proxy': 'Base metals reflecting global industrial demand',
            'battery_metals_ev_theme': 'Lithium and cobalt driven by electric vehicle adoption',
            'safe_haven_vs_cyclical': 'Flight-to-quality vs. growth trade dynamics'
        }
        
        # Macro-economic implications
        gold_performance = None
        copper_performance = None
        
        for category, commodities in commodity_analysis.items():
            if 'gold' in commodities and hasattr(commodities['gold'], 'consensus_performance'):
                gold_performance = commodities['gold'].consensus_performance
            if 'copper' in commodities and hasattr(commodities['copper'], 'consensus_performance'):
                copper_performance = commodities['copper'].consensus_performance
        
        macro_signals = []
        if gold_performance and gold_performance.ytd_change_pct:
            if gold_performance.ytd_change_pct > 15:
                macro_signals.append("Strong gold performance suggests inflation concerns or geopolitical tensions")
            elif gold_performance.ytd_change_pct < -10:
                macro_signals.append("Gold weakness indicates confidence in risk assets and dollar strength")
        
        if copper_performance and copper_performance.monthly_change_pct:
            if copper_performance.monthly_change_pct > 5:
                macro_signals.append("Copper strength indicates robust global manufacturing and construction demand")
            elif copper_performance.monthly_change_pct < -5:
                macro_signals.append("Copper weakness suggests economic slowdown concerns")
        
        intelligence['macro_economic_implications'] = {
            'signals_identified': macro_signals,
            'inflation_indicators': 'Analyzing precious metals and energy commodity trends',
            'growth_indicators': 'Monitoring base metals and industrial commodity demand',
            'sentiment_indicators': 'Safe-haven vs. risk-on asset performance'
        }
        
        # Trading opportunities
        opportunities = []
        for commodity_data in all_commodities:
            analysis = commodity_data['analysis']
            if analysis.opportunity_assessment == 'attractive':
                opportunities.append({
                    'commodity': commodity_data['commodity'],
                    'rationale': f"Strong momentum ({analysis.momentum_score}) with reasonable valuation levels",
                    'timeframe': 'Medium-term',
                    'risk_level': 'Moderate'
                })
            elif analysis.opportunity_assessment == 'contrarian_opportunity':
                opportunities.append({
                    'commodity': commodity_data['commodity'],
                    'rationale': "Oversold conditions with stabilizing momentum present contrarian opportunity",
                    'timeframe': 'Long-term',
                    'risk_level': 'High'
                })
        
        intelligence['trading_opportunities'] = {
            'identified_opportunities': opportunities[:5],  # Top 5 opportunities
            'market_timing_considerations': 'Monitor key support/resistance levels and momentum shifts',
            'risk_management_notes': 'Use position sizing and stop-losses given commodity volatility'
        }
        
        # Risk assessment
        high_risk_commodities = [
            c['commodity'] for c in all_commodities 
            if c['analysis'].volatility_index > 7 or c['analysis'].opportunity_assessment == 'avoid'
        ]
        
        intelligence['risk_assessment'] = {
            'high_volatility_commodities': high_risk_commodities,
            'market_risks': [
                'Dollar strength pressuring commodity prices',
                'Central bank policy changes affecting liquidity',
                'Geopolitical tensions creating supply disruptions',
                'Economic slowdown reducing demand'
            ],
            'commodity_specific_risks': 'Individual commodity risk factors identified in detailed analysis'
        }
        
        # Outlook summary
        bullish_sectors = [
            sector for sector, data in intelligence['sector_analysis'].items()
            if data['sector_outlook'] == 'positive'
        ]
        bearish_sectors = [
            sector for sector, data in intelligence['sector_analysis'].items()
            if data['sector_outlook'] == 'negative'
        ]
        
        intelligence['outlook_summary'] = {
            'positive_sectors': bullish_sectors,
            'challenging_sectors': bearish_sectors,
            'key_themes': [
                'EV transition driving battery metals demand',
                'Inflation hedge demand supporting precious metals',
                'Global manufacturing cycle affecting base metals',
                'Energy transition impacting uranium and critical materials'
            ],
            'market_outlook': intelligence['market_overview']['overall_market_sentiment']
        }
        
        return intelligence
        
    def compile_data_sources_summary(self) -> Dict[str, Any]:
        """Compile summary of data sources used and their performance"""
        sources_summary = {}
        
        for source_name, config in self.data_sources.items():
            source_logs = [log for log in self.performance_log if log.get('source') == source_name]
            
            successful_requests = [log for log in source_logs if log.get('success', False)]
            failed_requests = [log for log in source_logs if not log.get('success', False)]
            
            if source_logs:
                avg_response_time = sum(log['response_time'] for log in successful_requests) / len(successful_requests) if successful_requests else 0
                
                sources_summary[source_name] = {
                    'display_name': config['name'],
                    'specialties': config['specialties'],
                    'total_requests': len(source_logs),
                    'successful_requests': len(successful_requests),
                    'failed_requests': len(failed_requests),
                    'success_rate': len(successful_requests) / len(source_logs) if source_logs else 0,
                    'average_response_time': round(avg_response_time, 2),
                    'commodities_scraped': list(set(log.get('commodity', '') for log in successful_requests))
                }
        
        return sources_summary
        
    def generate_comprehensive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of the scraping session"""
        summary = {
            'session_overview': {},
            'data_quality_metrics': {},
            'performance_metrics': {},
            'key_findings': {},
            'recommendations': {}
        }
        
        # Session overview
        total_commodities_attempted = sum(len(commodities) for commodities in self.target_commodities.values())
        commodities_with_data = 0
        
        for category, commodities in results['commodity_analysis'].items():
            for commodity, analysis in commodities.items():
                if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance:
                    commodities_with_data += 1
        
        summary['session_overview'] = {
            'total_commodities_attempted': total_commodities_attempted,
            'commodities_with_data': commodities_with_data,
            'data_coverage_rate': commodities_with_data / total_commodities_attempted if total_commodities_attempted > 0 else 0,
            'total_duration_seconds': results.get('total_duration', 0),
            'errors_encountered': len(results.get('errors', []))
        }
        
        # Data quality metrics
        high_confidence_count = 0
        time_series_coverage = {
            'daily': 0, 'weekly': 0, 'monthly': 0, 'ytd': 0, 'yoy': 0
        }
        
        for category, commodities in results['commodity_analysis'].items():
            for commodity, analysis in commodities.items():
                if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance:
                    perf = analysis.consensus_performance
                    if perf.confidence_score > 0.7:
                        high_confidence_count += 1
                    
                    if perf.daily_change_pct is not None:
                        time_series_coverage['daily'] += 1
                    if perf.weekly_change_pct is not None:
                        time_series_coverage['weekly'] += 1
                    if perf.monthly_change_pct is not None:
                        time_series_coverage['monthly'] += 1
                    if perf.ytd_change_pct is not None:
                        time_series_coverage['ytd'] += 1
                    if perf.yoy_change_pct is not None:
                        time_series_coverage['yoy'] += 1
        
        summary['data_quality_metrics'] = {
            'high_confidence_data_points': high_confidence_count,
            'time_series_coverage': time_series_coverage,
            'data_sources_utilized': len(results.get('data_sources_used', {})),
            'consensus_prices_calculated': commodities_with_data
        }
        
        # Performance metrics
        successful_requests = len([log for log in self.performance_log if log.get('success', False)])
        total_requests = len(self.performance_log)
        
        if successful_requests > 0:
            avg_response_time = sum(
                log['response_time'] for log in self.performance_log if log.get('success', False)
            ) / successful_requests
        else:
            avg_response_time = 0
        
        summary['performance_metrics'] = {
            'total_requests_made': total_requests,
            'successful_requests': successful_requests,
            'request_success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'average_response_time': round(avg_response_time, 2),
            'rate_limiting_encountered': len([log for log in self.performance_log if 'rate limit' in log.get('error', '').lower()]),
            'bot_detection_encountered': len([log for log in self.performance_log if '403' in str(log.get('error', ''))])
        }
        
        # Key findings
        findings = []
        
        # Market sentiment finding
        market_sentiment = results.get('market_intelligence', {}).get('market_overview', {}).get('overall_market_sentiment', 'unknown')
        if market_sentiment != 'unknown':
            findings.append(f"Overall commodity market sentiment: {market_sentiment}")
        
        # Top performers
        ytd_performers = results.get('performance_rankings', {}).get('ytd_performers', {}).get('best', [])
        if ytd_performers:
            top_performer = ytd_performers[0]
            findings.append(f"Top YTD performer: {top_performer['commodity'].title()} (+{top_performer['change_pct']:.1f}%)")
        
        # Sector insights
        sector_analysis = results.get('market_intelligence', {}).get('sector_analysis', {})
        for sector, data in sector_analysis.items():
            if data['sector_outlook'] == 'positive':
                findings.append(f"{sector.replace('_', ' ').title()} sector showing positive momentum")
        
        summary['key_findings'] = findings
        
        # Recommendations
        recommendations = []
        
        if summary['data_quality_metrics']['high_confidence_data_points'] < commodities_with_data * 0.7:
            recommendations.append("Consider additional data sources to improve confidence scores")
        
        if summary['performance_metrics']['request_success_rate'] < 0.8:
            recommendations.append("Review failed requests and implement additional anti-bot measures")
        
        opportunities = results.get('market_intelligence', {}).get('trading_opportunities', {}).get('identified_opportunities', [])
        if opportunities:
            recommendations.append(f"Monitor {len(opportunities)} identified trading opportunities across different timeframes")
        
        if not recommendations:
            recommendations.append("Data quality and scraping performance are satisfactory")
        
        summary['recommendations'] = recommendations
        
        return summary
        
    async def save_comprehensive_results(self, results: Dict[str, Any]):
        """Save comprehensive results to JSON and generate markdown report"""
        
        # Save raw JSON data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = Path(f"/Projects/Resource Capital/reports/2025-08-04/enhanced_commodity_analysis_{timestamp}.json")
        
        # Convert dataclass objects to dictionaries for JSON serialization
        serializable_results = self.convert_to_serializable(results)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Comprehensive results saved to: {json_file}")
        
        # Generate markdown report
        await self.generate_markdown_report(results)
        
    def convert_to_serializable(self, obj):
        """Convert dataclass objects and other non-serializable objects to dictionaries"""
        if isinstance(obj, dict):
            return {k: self.convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Convert dataclass or object with __dict__ to dictionary
            return {k: self.convert_to_serializable(v) for k, v in obj.__dict__.items()}
        else:
            return obj
            
    async def generate_markdown_report(self, results: Dict[str, Any]):
        """Generate comprehensive markdown report"""
        
        report_content = f"""# Enhanced Commodity Time-Series Analysis Report
## Date: {datetime.now().strftime('%B %d, %Y')}

---

## Executive Summary

This comprehensive analysis provides detailed time-series performance metrics for major mining commodities across multiple timeframes. The data is sourced from leading financial platforms including Kitco, Trading Economics, MarketWatch, Yahoo Finance, and the London Metal Exchange.

### Key Highlights
- **Total Commodities Analyzed**: {results['summary']['session_overview']['commodities_with_data']}
- **Data Coverage Rate**: {results['summary']['session_overview']['data_coverage_rate']:.1%}
- **Overall Market Sentiment**: {results['market_intelligence']['market_overview']['overall_market_sentiment'].title()}
- **Analysis Duration**: {results['summary']['session_overview']['total_duration_seconds']:.1f} seconds

---

## Commodity Performance Analysis

### 📊 Performance Rankings

#### Top YTD Performers
"""
        
        # Add YTD performers
        ytd_best = results.get('performance_rankings', {}).get('ytd_performers', {}).get('best', [])
        if ytd_best:
            report_content += "\n| Commodity | Category | YTD Change | Current Price |\n"
            report_content += "|-----------|----------|------------|---------------|\n"
            for performer in ytd_best[:5]:
                report_content += f"| {performer['commodity'].title()} | {performer['category'].replace('_', ' ').title()} | {performer['change_pct']:+.1f}% | ${performer['current_price']:.2f} {performer['unit']} |\n"
        
        report_content += "\n#### Worst YTD Performers\n"
        ytd_worst = results.get('performance_rankings', {}).get('ytd_performers', {}).get('worst', [])
        if ytd_worst:
            report_content += "\n| Commodity | Category | YTD Change | Current Price |\n"
            report_content += "|-----------|----------|------------|---------------|\n"
            for performer in ytd_worst[:5]:
                report_content += f"| {performer['commodity'].title()} | {performer['category'].replace('_', ' ').title()} | {performer['change_pct']:+.1f}% | ${performer['current_price']:.2f} {performer['unit']} |\n"
        
        # Add detailed commodity analysis
        report_content += "\n---\n\n## Detailed Commodity Analysis\n\n"
        
        for category, commodities in results['commodity_analysis'].items():
            if commodities:
                report_content += f"### {category.replace('_', ' ').title()}\n\n"
                
                for commodity, analysis in commodities.items():
                    if hasattr(analysis, 'consensus_performance') and analysis.consensus_performance:
                        perf = analysis.consensus_performance
                        report_content += f"#### {commodity.upper()}\n"
                        report_content += f"- **Current Price**: ${perf.current_price:.2f} {perf.unit}\n"
                        
                        if perf.daily_change_pct is not None:
                            sign = "+" if perf.daily_change_pct >= 0 else ""
                            report_content += f"- **Daily Change**: {sign}{perf.daily_change_pct:.2f}%"
                            if perf.daily_change_abs is not None:
                                abs_sign = "+" if perf.daily_change_abs >= 0 else ""
                                report_content += f" ({abs_sign}${perf.daily_change_abs:.2f})"
                            report_content += "\n"
                        
                        if perf.weekly_change_pct is not None:
                            sign = "+" if perf.weekly_change_pct >= 0 else ""
                            report_content += f"- **Weekly Change**: {sign}{perf.weekly_change_pct:.2f}%"
                            if perf.weekly_change_abs is not None:
                                abs_sign = "+" if perf.weekly_change_abs >= 0 else ""
                                report_content += f" ({abs_sign}${perf.weekly_change_abs:.2f})"
                            report_content += "\n"
                        
                        if perf.monthly_change_pct is not None:
                            sign = "+" if perf.monthly_change_pct >= 0 else ""
                            report_content += f"- **Monthly Change**: {sign}{perf.monthly_change_pct:.2f}%"
                            if perf.monthly_change_abs is not None:
                                abs_sign = "+" if perf.monthly_change_abs >= 0 else ""
                                report_content += f" ({abs_sign}${perf.monthly_change_abs:.2f})"
                            report_content += "\n"
                        
                        if perf.ytd_change_pct is not None:
                            sign = "+" if perf.ytd_change_pct >= 0 else ""
                            report_content += f"- **Year-to-Date**: {sign}{perf.ytd_change_pct:.2f}%"
                            if perf.ytd_change_abs is not None:
                                abs_sign = "+" if perf.ytd_change_abs >= 0 else ""
                                report_content += f" ({abs_sign}${perf.ytd_change_abs:.2f})"
                            report_content += "\n"
                        
                        if perf.yoy_change_pct is not None:
                            sign = "+" if perf.yoy_change_pct >= 0 else ""
                            report_content += f"- **Year-over-Year**: {sign}{perf.yoy_change_pct:.2f}%"
                            if perf.yoy_change_abs is not None:
                                abs_sign = "+" if perf.yoy_change_abs >= 0 else ""
                                report_content += f" ({abs_sign}${perf.yoy_change_abs:.2f})"
                            report_content += "\n"
                        
                        # Add analysis metrics
                        report_content += f"- **Momentum Score**: {analysis.momentum_score}/10\n"
                        report_content += f"- **Trend Direction**: {analysis.trend_direction.title()}\n"
                        report_content += f"- **Volatility Index**: {analysis.volatility_index:.1f}\n"
                        report_content += f"- **Opportunity Assessment**: {analysis.opportunity_assessment.replace('_', ' ').title()}\n"
                        
                        # Add investment implications
                        if analysis.investment_implications:
                            report_content += f"- **Investment Implications**:\n"
                            for implication in analysis.investment_implications:
                                report_content += f"  - {implication}\n"
                        
                        # Add risk factors
                        if analysis.risk_factors:
                            report_content += f"- **Risk Factors**:\n"
                            for risk in analysis.risk_factors:
                                report_content += f"  - {risk}\n"
                        
                        report_content += f"- **Data Confidence**: {perf.confidence_score:.1%}\n\n"
        
        # Market Intelligence Section
        report_content += "---\n\n## Market Intelligence\n\n"
        
        market_intel = results.get('market_intelligence', {})
        
        # Market Overview
        market_overview = market_intel.get('market_overview', {})
        if market_overview:
            report_content += "### Market Overview\n"
            sentiment_dist = market_overview.get('market_sentiment_distribution', {})
            report_content += f"- **Market Sentiment**: {market_overview.get('overall_market_sentiment', 'Unknown').title()}\n"
            report_content += f"- **Bullish Commodities**: {sentiment_dist.get('bullish', 0)}\n"
            report_content += f"- **Bearish Commodities**: {sentiment_dist.get('bearish', 0)}\n"
            report_content += f"- **Neutral Commodities**: {sentiment_dist.get('neutral', 0)}\n"
            report_content += f"- **High Momentum Commodities**: {market_overview.get('high_momentum_commodities', 0)}\n"
            report_content += f"- **Volatile Commodities**: {market_overview.get('volatile_commodities', 0)}\n\n"
        
        # Sector Analysis
        sector_analysis = market_intel.get('sector_analysis', {})
        if sector_analysis:
            report_content += "### Sector Analysis\n\n"
            for sector, data in sector_analysis.items():
                report_content += f"#### {sector.replace('_', ' ').title()}\n"
                report_content += f"- **Commodities Analyzed**: {data['commodities_count']}\n"
                report_content += f"- **Average Momentum**: {data['average_momentum_score']}/10\n"
                report_content += f"- **Average Volatility**: {data['average_volatility']:.1f}\n"
                report_content += f"- **Average YTD Performance**: {data['average_ytd_performance']:+.1f}%\n"
                report_content += f"- **Sector Outlook**: {data['sector_outlook'].title()}\n\n"
        
        # Trading Opportunities
        opportunities = market_intel.get('trading_opportunities', {}).get('identified_opportunities', [])
        if opportunities:
            report_content += "### Trading Opportunities\n\n"
            for i, opp in enumerate(opportunities, 1):
                report_content += f"{i}. **{opp['commodity'].title()}**\n"
                report_content += f"   - Rationale: {opp['rationale']}\n"
                report_content += f"   - Timeframe: {opp['timeframe']}\n"
                report_content += f"   - Risk Level: {opp['risk_level']}\n\n"
        
        # Performance Summary
        report_content += "---\n\n## Data Quality & Performance Summary\n\n"
        
        summary = results.get('summary', {})
        data_quality = summary.get('data_quality_metrics', {})
        performance = summary.get('performance_metrics', {})
        
        report_content += "### Data Quality Metrics\n"
        report_content += f"- **High Confidence Data Points**: {data_quality.get('high_confidence_data_points', 0)}\n"
        report_content += f"- **Data Sources Utilized**: {data_quality.get('data_sources_utilized', 0)}\n"
        report_content += f"- **Consensus Prices Calculated**: {data_quality.get('consensus_prices_calculated', 0)}\n"
        
        time_series = data_quality.get('time_series_coverage', {})
        report_content += f"- **Time-Series Coverage**:\n"
        report_content += f"  - Daily: {time_series.get('daily', 0)} commodities\n"
        report_content += f"  - Weekly: {time_series.get('weekly', 0)} commodities\n"
        report_content += f"  - Monthly: {time_series.get('monthly', 0)} commodities\n"
        report_content += f"  - YTD: {time_series.get('ytd', 0)} commodities\n"
        report_content += f"  - YoY: {time_series.get('yoy', 0)} commodities\n\n"
        
        report_content += "### Scraping Performance\n"
        report_content += f"- **Total Requests**: {performance.get('total_requests_made', 0)}\n"
        report_content += f"- **Success Rate**: {performance.get('request_success_rate', 0):.1%}\n"
        report_content += f"- **Average Response Time**: {performance.get('average_response_time', 0):.2f} seconds\n"
        report_content += f"- **Rate Limiting Encountered**: {performance.get('rate_limiting_encountered', 0)} instances\n"
        report_content += f"- **Bot Detection Encountered**: {performance.get('bot_detection_encountered', 0)} instances\n\n"
        
        # Data Sources Summary
        sources_used = results.get('data_sources_used', {})
        if sources_used:
            report_content += "### Data Sources Performance\n\n"
            for source, data in sources_used.items():
                report_content += f"#### {data['display_name']}\n"
                report_content += f"- **Success Rate**: {data['success_rate']:.1%} ({data['successful_requests']}/{data['total_requests']})\n"
                report_content += f"- **Average Response Time**: {data['average_response_time']:.2f}s\n"
                report_content += f"- **Commodities Scraped**: {', '.join(data['commodities_scraped'])}\n"
                report_content += f"- **Specialties**: {', '.join(data['specialties'])}\n\n"
        
        # Key Findings and Recommendations
        findings = summary.get('key_findings', [])
        if findings:
            report_content += "### Key Findings\n"
            for finding in findings:
                report_content += f"- {finding}\n"
            report_content += "\n"
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report_content += "### Recommendations\n"
            for rec in recommendations:
                report_content += f"- {rec}\n"
            report_content += "\n"
        
        # Footer
        report_content += "---\n\n"
        report_content += f"*Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}*\n"
        report_content += f"*Analysis powered by Enhanced Commodity Time-Series Scraper*\n"
        report_content += f"*Data sources: Kitco, Trading Economics, MarketWatch, Yahoo Finance, LME*\n"
        
        # Save markdown report
        report_file = Path("/Projects/Resource Capital/reports/2025-08-04/ENHANCED_COMMODITY_ANALYSIS_2025-08-04.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Enhanced commodity analysis report saved to: {report_file}")
        print(f"✅ Enhanced commodity analysis report generated: {report_file}")

# Main execution function
async def run_enhanced_commodity_analysis():
    """Execute the enhanced commodity time-series analysis"""
    scraper = EnhancedCommodityTimeScraper()
    
    try:
        print("🚀 Starting Enhanced Commodity Time-Series Analysis...")
        print("=" * 80)
        
        results = await scraper.scrape_comprehensive_commodity_data()
        
        print(f"\n📊 ANALYSIS COMPLETE")
        print(f"Total Duration: {results['total_duration']:.1f} seconds")
        print(f"Commodities Analyzed: {results['summary']['session_overview']['commodities_with_data']}")
        print(f"Data Coverage: {results['summary']['session_overview']['data_coverage_rate']:.1%}")
        print(f"Overall Market Sentiment: {results['market_intelligence']['market_overview']['overall_market_sentiment'].title()}")
        
        if results['errors']:
            print(f"⚠️  Errors Encountered: {len(results['errors'])}")
        
        print(f"\n📁 Reports saved to: /Projects/Resource Capital/reports/2025-08-04/")
        print(f"   - Enhanced Analysis: ENHANCED_COMMODITY_ANALYSIS_2025-08-04.md")
        print(f"   - Raw Data: enhanced_commodity_analysis_*.json")
        
        return results
        
    except Exception as e:
        logger.error(f"Critical error in enhanced commodity analysis: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_enhanced_commodity_analysis())