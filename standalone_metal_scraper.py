#!/usr/bin/env python3
"""
Standalone Metal Prices Scraper for August 4, 2025
Targets the 4 specific mining intelligence sites requested
"""

import asyncio
import json
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urljoin
import sys

# Simple scraper class without complex dependencies
class SimpleMetalPricesScraper:
    """Simplified metal prices scraper using only requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Target sites configuration
        self.target_sites = [
            {
                'name': 'trading_economics',
                'display_name': 'Trading Economics Commodities',
                'url': 'https://tradingeconomics.com/commodities',
                'commodities': ['gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lithium', 'uranium', 'cobalt']
            },
            {
                'name': 'daily_metal_price',
                'display_name': 'Daily Metal Price',
                'url': 'https://www.dailymetalprice.com/',
                'commodities': ['gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lithium']
            },
            {
                'name': 'kitco_precious',
                'display_name': 'Kitco Precious Metals',
                'url': 'https://www.kitco.com/price/precious-metals',
                'commodities': ['gold', 'silver', 'platinum', 'palladium']
            },
            {
                'name': 'kitco_base',
                'display_name': 'Kitco Base Metals',
                'url': 'https://www.kitco.com/price/base-metals',
                'commodities': ['copper', 'nickel', 'zinc', 'aluminum']
            }
        ]
    
    def scrape_all_sites(self) -> Dict[str, Any]:
        """Scrape all target sites for metal prices"""
        
        print("💰 Starting targeted metal prices scraping for mining intelligence...")
        print("🎯 Target Sites: Trading Economics, Daily Metal Price, Kitco Precious, Kitco Base")
        
        results = {
            'scraping_started': datetime.now().isoformat(),
            'target_date': '2025-08-04',
            'sites_scraped': {},
            'commodity_data': {
                'precious_metals': {},
                'base_metals': {},
                'critical_metals': {}
            },
            'market_analysis': {},
            'performance_log': [],
            'errors': [],
            'summary': {}
        }
        
        # Scrape each site
        for site_config in self.target_sites:
            site_start_time = time.time()
            print(f"\n🌐 Scraping {site_config['display_name']}...")
            
            try:
                site_data = self._scrape_site(site_config)
                results['sites_scraped'][site_config['name']] = site_data
                
                # Categorize commodities
                for commodity, commodity_data in site_data.get('commodities', {}).items():
                    if commodity in ['gold', 'silver', 'platinum', 'palladium']:
                        category = 'precious_metals'
                    elif commodity in ['lithium', 'uranium', 'cobalt']:
                        category = 'critical_metals'
                    else:
                        category = 'base_metals'
                    
                    if commodity not in results['commodity_data'][category]:
                        results['commodity_data'][category][commodity] = {}
                    
                    results['commodity_data'][category][commodity][site_config['name']] = commodity_data
                
                # Log performance
                site_duration = time.time() - site_start_time
                performance_entry = {
                    'site': site_config['name'],
                    'display_name': site_config['display_name'],
                    'url': site_config['url'],
                    'success': True,
                    'response_time': site_duration,
                    'commodities_found': len(site_data.get('commodities', {})),
                    'content_size': len(site_data.get('raw_content', '')),
                    'timestamp': datetime.now().isoformat()
                }
                results['performance_log'].append(performance_entry)
                
                print(f"✅ {site_config['display_name']}: {len(site_data.get('commodities', {}))} commodities in {site_duration:.1f}s")
                
            except Exception as e:
                error_msg = f"Failed to scrape {site_config['display_name']}: {str(e)}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                
                # Log failed performance
                site_duration = time.time() - site_start_time
                performance_entry = {
                    'site': site_config['name'],
                    'display_name': site_config['display_name'],
                    'url': site_config['url'],
                    'success': False,
                    'response_time': site_duration,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['performance_log'].append(performance_entry)
            
            # Rate limiting
            time.sleep(2)
        
        # Generate analysis and summary
        results['market_analysis'] = self._generate_market_analysis(results)
        results['scraping_completed'] = datetime.now().isoformat()
        results['summary'] = self._generate_summary(results)
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _scrape_site(self, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a specific site for commodity data"""
        
        site_data = {
            'site_name': site_config['name'],
            'display_name': site_config['display_name'],
            'url': site_config['url'],
            'scraped_at': datetime.now().isoformat(),
            'commodities': {},
            'market_commentary': [],
            'raw_content': '',
            'scraper_used': 'requests'
        }
        
        try:
            print(f"  📡 Fetching {site_config['url']}...")
            response = self.session.get(site_config['url'], timeout=30)
            response.raise_for_status()
            
            content = response.text
            site_data['raw_content'] = content
            print(f"  📄 Retrieved {len(content)} characters")
            
            # Extract commodities based on site type
            if site_config['name'] == 'trading_economics':
                commodities = self._extract_trading_economics(content)
            elif site_config['name'] == 'daily_metal_price':
                commodities = self._extract_daily_metal_price(content)
            elif site_config['name'] in ['kitco_precious', 'kitco_base']:
                commodities = self._extract_kitco(content, site_config['name'])
            else:
                commodities = {}
            
            site_data['commodities'] = commodities
            
            # Extract market commentary
            commentary = self._extract_commentary(content, site_config['name'])
            site_data['market_commentary'] = commentary
            
            print(f"  ✅ Extracted {len(commodities)} commodities")
            
        except Exception as e:
            print(f"  💥 Error: {str(e)}")
            site_data['error'] = str(e)
        
        return site_data
    
    def _extract_trading_economics(self, content: str) -> Dict[str, Any]:
        """Extract commodity data from Trading Economics"""
        
        commodities = {}
        
        # Enhanced patterns for Trading Economics table data
        patterns = [
            # Table row pattern with commodity name, price, and change
            r'<tr[^>]*>.*?<td[^>]*>.*?<a[^>]*[^>]*>.*?(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt).*?</a>.*?</td>.*?<td[^>]*>.*?([\d,]+\.?\d*).*?</td>.*?<td[^>]*>.*?([+-]?[\d.]+).*?</td>',
            # Alternative pattern for different table structures
            r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt)[^<]*</a>[^<]*</td>[^<]*<td[^>]*>([^<]*[\d,]+\.?\d*)[^<]*</td>[^<]*<td[^>]*>([^<]*[+-]?[\d.]+)',
            # Simple name-price-change pattern
            r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt).*?([\d,]+\.?\d*).*?([+-]?[\d.]+%?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) >= 3:
                    try:
                        metal_name = match[0].lower().strip()
                        price_str = re.sub(r'[^\d.,]', '', match[1])
                        change_str = match[2].strip()
                        
                        if price_str:
                            price = float(price_str.replace(',', ''))
                            commodities[metal_name] = {
                                'price': price,
                                'change': change_str,
                                'unit': 'USD/oz' if metal_name in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/ton',
                                'source': 'trading_economics',
                                'timestamp': datetime.now().isoformat()
                            }
                    except (ValueError, IndexError) as e:
                        continue
        
        return commodities
    
    def _extract_daily_metal_price(self, content: str) -> Dict[str, Any]:
        """Extract commodity data from Daily Metal Price"""
        
        commodities = {}
        
        # Patterns for Daily Metal Price
        patterns = [
            # Table pattern
            r'<tr[^>]*>.*?<td[^>]*>.*?(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium).*?</td>.*?<td[^>]*>.*?\$?([\d,]+\.?\d*).*?</td>.*?<td[^>]*>.*?([+-]?[\d.]+%?).*?</td>',
            # Price display pattern
            r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium)\s+Price[^$]*\$?([\d,]+\.?\d*).*?([+-]?[\d.]+%?)',
            # Alternative format
            r'<h\d[^>]*>(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium)[^<]*</h\d>.*?price[^$]*\$?([\d,]+\.?\d*).*?([+-]?[\d.]+%?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) >= 3:
                    try:
                        metal_name = match[0].lower().strip()
                        price_str = match[1].replace(',', '')
                        change_str = match[2].strip()
                        
                        if price_str:
                            price = float(price_str)
                            commodities[metal_name] = {
                                'price': price,
                                'change': change_str,
                                'unit': 'USD/oz' if metal_name in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/lb',
                                'source': 'daily_metal_price',
                                'timestamp': datetime.now().isoformat()
                            }
                    except (ValueError, IndexError):
                        continue
        
        return commodities
    
    def _extract_kitco(self, content: str, site_type: str) -> Dict[str, Any]:
        """Extract commodity data from Kitco sites"""
        
        commodities = {}
        
        if site_type == 'kitco_precious':
            target_metals = ['gold', 'silver', 'platinum', 'palladium']
        else:
            target_metals = ['copper', 'nickel', 'zinc', 'aluminum']
        
        for metal in target_metals:
            # Kitco-specific patterns
            patterns = [
                rf'{metal.title()}[^$]*\$?([\d,]+\.?\d*)[^+-]*([+-]?[\d.]+%?)',
                rf'<td[^>]*>{metal.title()}</td>.*?<td[^>]*>\$?([\d,]+\.?\d*)</td>.*?<td[^>]*>([+-]?[\d.]+%?)</td>',
                rf'id="[^"]*{metal}[^"]*"[^>]*>\$?([\d,]+\.?\d*)<.*?([+-]?[\d.]+%?)',
                rf'{metal}.*?(\$?[\d,]+\.?\d*).*?([+-]?[\d.]+%?)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        price_str = match.group(1).replace('$', '').replace(',', '')
                        change_str = match.group(2).strip()
                        
                        if price_str:
                            price = float(price_str)
                            commodities[metal] = {
                                'price': price,
                                'change': change_str,
                                'unit': 'USD/oz' if metal in ['gold', 'silver', 'platinum', 'palladium'] else 'USD/lb',
                                'source': site_type,
                                'timestamp': datetime.now().isoformat()
                            }
                            break
                    except (ValueError, IndexError):
                        continue
        
        return commodities
    
    def _extract_commentary(self, content: str, site_name: str) -> List[str]:
        """Extract market commentary from content"""
        
        commentary = []
        
        # Commentary patterns
        patterns = [
            r'<p[^>]*>(.*?market.*?)</p>',
            r'<p[^>]*>(.*?outlook.*?)</p>',
            r'<p[^>]*>(.*?forecast.*?)</p>',
            r'<p[^>]*>(.*?analysis.*?)</p>',
            r'<div[^>]*commentary[^>]*>.*?<p[^>]*>(.*?)</p>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_text) > 50 and len(clean_text) < 300 and 'cookie' not in clean_text.lower():
                    commentary.append(clean_text)
        
        return commentary[:3]
    
    def _generate_market_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market analysis from scraped data"""
        
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'price_consensus': {},
            'significant_movements': [],
            'market_sentiment': 'neutral',
            'investment_implications': []
        }
        
        # Calculate consensus prices
        all_commodities = {}
        for category in ['precious_metals', 'base_metals', 'critical_metals']:
            for commodity, sources in results['commodity_data'][category].items():
                all_commodities[commodity] = sources
        
        for commodity, sources in all_commodities.items():
            prices = []
            changes = []
            
            for source_data in sources.values():
                if 'price' in source_data:
                    prices.append(source_data['price'])
                if 'change' in source_data:
                    # Extract numeric change
                    change_match = re.search(r'([+-]?[\d.]+)', str(source_data['change']))
                    if change_match:
                        try:
                            changes.append(float(change_match.group(1)))
                        except ValueError:
                            pass
            
            if prices:
                avg_price = sum(prices) / len(prices)
                avg_change = sum(changes) / len(changes) if changes else 0
                
                analysis['price_consensus'][commodity] = {
                    'average_price': avg_price,
                    'price_range': f"${min(prices):.2f} - ${max(prices):.2f}",
                    'sources_count': len(prices),
                    'price_spread': max(prices) - min(prices) if len(prices) > 1 else 0,
                    'average_change': avg_change
                }
                
                # Identify significant movements (>2%)
                if abs(avg_change) > 2.0:
                    direction = "up" if avg_change > 0 else "down"
                    analysis['significant_movements'].append({
                        'commodity': commodity,
                        'direction': direction,
                        'magnitude': abs(avg_change),
                        'impact': 'high' if abs(avg_change) > 5 else 'moderate'
                    })
        
        # Determine market sentiment
        if analysis['significant_movements']:
            positive = sum(1 for m in analysis['significant_movements'] if m['direction'] == 'up')
            negative = sum(1 for m in analysis['significant_movements'] if m['direction'] == 'down')
            
            if positive > negative:
                analysis['market_sentiment'] = 'bullish'
            elif negative > positive:
                analysis['market_sentiment'] = 'bearish'
            else:
                analysis['market_sentiment'] = 'mixed'
        
        # Investment implications
        for move in analysis['significant_movements']:
            if move['commodity'] in ['gold', 'silver'] and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    f"Rising {move['commodity']} prices may indicate flight to safety or inflation concerns"
                )
            elif move['commodity'] == 'copper' and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    "Copper price increase suggests economic growth expectations"
                )
            elif move['commodity'] in ['lithium', 'cobalt'] and move['direction'] == 'up':
                analysis['investment_implications'].append(
                    f"{move['commodity'].title()} price rise driven by EV and battery demand"
                )
        
        return analysis
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scraping session summary"""
        
        summary = {
            'scraping_session': {
                'target_date': '2025-08-04',
                'sites_attempted': len(results['performance_log']),
                'sites_successful': len([p for p in results['performance_log'] if p.get('success', False)]),
                'total_duration': None
            },
            'data_quality': {
                'commodities_found': 0,
                'consensus_prices': len(results.get('market_analysis', {}).get('price_consensus', {})),
                'market_commentary_pieces': 0
            },
            'performance_metrics': {
                'average_response_time': 0.0,
                'fastest_site': None,
                'slowest_site': None,
                'most_data_rich_site': None
            },
            'market_highlights': [],
            'scraping_challenges': results.get('errors', [])
        }
        
        # Calculate commodities found
        for category in results['commodity_data'].values():
            for commodity_sources in category.values():
                summary['data_quality']['commodities_found'] += len(commodity_sources)
        
        # Performance metrics
        successful_entries = [p for p in results['performance_log'] if p.get('success', False)]
        if successful_entries:
            response_times = [p['response_time'] for p in successful_entries]
            summary['performance_metrics']['average_response_time'] = sum(response_times) / len(response_times)
            
            fastest = min(successful_entries, key=lambda x: x['response_time'])
            slowest = max(successful_entries, key=lambda x: x['response_time'])
            most_data = max(successful_entries, key=lambda x: x.get('commodities_found', 0))
            
            summary['performance_metrics']['fastest_site'] = f"{fastest['display_name']} ({fastest['response_time']:.1f}s)"
            summary['performance_metrics']['slowest_site'] = f"{slowest['display_name']} ({slowest['response_time']:.1f}s)"
            summary['performance_metrics']['most_data_rich_site'] = f"{most_data['display_name']} ({most_data.get('commodities_found', 0)} commodities)"
        
        # Market highlights
        market_analysis = results.get('market_analysis', {})
        for move in market_analysis.get('significant_movements', []):
            summary['market_highlights'].append(
                f"{move['commodity'].title()} {move['direction']} {move['magnitude']:.1f}% - {move['impact']} impact"
            )
        
        # Calculate total duration
        if results.get('scraping_started') and results.get('scraping_completed'):
            start = datetime.fromisoformat(results['scraping_started'])
            end = datetime.fromisoformat(results['scraping_completed'])
            summary['scraping_session']['total_duration'] = (end - start).total_seconds()
        
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """Save results to files"""
        
        # Create reports directory
        reports_dir = Path("/Projects/Resource Capital/reports/2025-08-04")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main results file
        results_file = reports_dir / "metal_prices_data.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Results saved to: {results_file}")


def main():
    """Main execution function"""
    
    print("🎯 METAL PRICES INTELLIGENCE SCRAPING - AUGUST 4, 2025")
    print("=" * 60)
    print("Target Sites:")
    print("  1. Trading Economics Commodities")
    print("  2. Daily Metal Price")
    print("  3. Kitco Precious Metals")
    print("  4. Kitco Base Metals")
    print()
    print("Target Commodities: gold, silver, copper, platinum, palladium, nickel, zinc, lithium, uranium, cobalt")
    print("=" * 60)
    
    try:
        scraper = SimpleMetalPricesScraper()
        results = scraper.scrape_all_sites()
        
        print("\n" + "=" * 60)
        print("📊 SCRAPING COMPLETED - RESULTS SUMMARY")
        print("=" * 60)
        
        # Display summary
        summary = results.get('summary', {})
        scraping_session = summary.get('scraping_session', {})
        data_quality = summary.get('data_quality', {})
        performance_metrics = summary.get('performance_metrics', {})
        
        print(f"🕒 Scraping Duration: {scraping_session.get('total_duration', 0):.1f} seconds")
        print(f"🌐 Sites Attempted: {scraping_session.get('sites_attempted', 0)}")
        print(f"✅ Sites Successful: {scraping_session.get('sites_successful', 0)}")
        print(f"📈 Commodities Found: {data_quality.get('commodities_found', 0)}")
        print(f"🎯 Consensus Prices: {data_quality.get('consensus_prices', 0)}")
        print(f"⚡ Average Response Time: {performance_metrics.get('average_response_time', 0):.1f}s")
        
        if performance_metrics.get('fastest_site'):
            print(f"🏃 Fastest Site: {performance_metrics['fastest_site']}")
        if performance_metrics.get('most_data_rich_site'):
            print(f"📊 Most Data Rich: {performance_metrics['most_data_rich_site']}")
        
        # Display market highlights
        market_highlights = summary.get('market_highlights', [])
        if market_highlights:
            print(f"\n🔥 MARKET HIGHLIGHTS:")
            for highlight in market_highlights:
                print(f"   • {highlight}")
        
        # Display commodity consensus prices
        market_analysis = results.get('market_analysis', {})
        price_consensus = market_analysis.get('price_consensus', {})
        
        if price_consensus:
            print(f"\n💰 COMMODITY PRICE CONSENSUS:")
            for commodity, consensus in price_consensus.items():
                avg_price = consensus.get('average_price', 0)
                avg_change = consensus.get('average_change', 0)
                sources = consensus.get('sources_count', 0)
                change_direction = "↑" if avg_change > 0 else "↓" if avg_change < 0 else "→"
                
                print(f"   {commodity.title()}: ${avg_price:.2f} {change_direction} {avg_change:+.1f}% (from {sources} sources)")
        
        # Market sentiment
        sentiment = market_analysis.get('market_sentiment', 'neutral')
        sentiment_emoji = "🐂" if sentiment == 'bullish' else "🐻" if sentiment == 'bearish' else "😐"
        print(f"\n{sentiment_emoji} Market Sentiment: {sentiment.title()}")
        
        # Investment implications
        implications = market_analysis.get('investment_implications', [])
        if implications:
            print(f"\n💡 INVESTMENT IMPLICATIONS:")
            for implication in implications:
                print(f"   • {implication}")
        
        # Display errors if any
        errors = results.get('errors', [])
        if errors:
            print(f"\n⚠️  SCRAPING CHALLENGES:")
            for error in errors:
                print(f"   • {error}")
        
        print("=" * 60)
        print("🎉 Metal prices intelligence collection completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Critical error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()