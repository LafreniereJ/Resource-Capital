#!/usr/bin/env python3
"""
Quick Metal Prices Scraper for August 4, 2025
Fast, focused scraping of the 4 target sites
"""

import requests
import json
import re
import time
from datetime import datetime
from pathlib import Path


def quick_scrape_trading_economics():
    """Quick scrape of Trading Economics commodities"""
    
    print("🌐 Scraping Trading Economics...")
    url = "https://tradingeconomics.com/commodities"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        commodities = {}
        
        # Look for commodity data in the content
        # Pattern for table data
        pattern = r'(Gold|Silver|Copper|Platinum|Palladium|Nickel|Zinc|Lithium|Uranium|Cobalt)[^0-9]*?([\d,]+\.?\d*)[^0-9+-]*?([+-]?[\d.]+)'
        
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            try:
                metal = match[0].lower()
                price = float(match[1].replace(',', ''))
                change = match[2]
                
                commodities[metal] = {
                    'price': price,
                    'change': change + '%',
                    'source': 'trading_economics'
                }
            except:
                continue
        
        return {
            'success': True,
            'commodities': commodities,
            'content_size': len(content),
            'url': url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'commodities': {},
            'url': url
        }


def quick_scrape_kitco_precious():
    """Quick scrape of Kitco precious metals"""
    
    print("🌐 Scraping Kitco Precious Metals...")
    url = "https://www.kitco.com/price/precious-metals"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        commodities = {}
        
        # Look for precious metals data
        for metal in ['gold', 'silver', 'platinum', 'palladium']:
            pattern = rf'{metal.title()}[^$]*\$?([\d,]+\.?\d*)[^+-]*([+-]?[\d.]+%?)'
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                    change = match.group(2)
                    
                    commodities[metal] = {
                        'price': price,
                        'change': change,
                        'source': 'kitco_precious'
                    }
                except:
                    continue
        
        return {
            'success': True,
            'commodities': commodities,
            'content_size': len(content),
            'url': url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'commodities': {},
            'url': url
        }


def quick_scrape_kitco_base():
    """Quick scrape of Kitco base metals"""
    
    print("🌐 Scraping Kitco Base Metals...")
    url = "https://www.kitco.com/price/base-metals"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        commodities = {}
        
        # Look for base metals data
        for metal in ['copper', 'nickel', 'zinc', 'aluminum']:
            pattern = rf'{metal.title()}[^$]*\$?([\d,]+\.?\d*)[^+-]*([+-]?[\d.]+%?)'
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                    change = match.group(2)
                    
                    commodities[metal] = {
                        'price': price,
                        'change': change,
                        'source': 'kitco_base'
                    }
                except:
                    continue
        
        return {
            'success': True,
            'commodities': commodities,
            'content_size': len(content),
            'url': url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'commodities': {},
            'url': url
        }


def quick_scrape_daily_metal_price():
    """Quick scrape of Daily Metal Price"""
    
    print("🌐 Scraping Daily Metal Price...")
    url = "https://www.dailymetalprice.com/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        commodities = {}
        
        # Look for metal price data
        for metal in ['gold', 'silver', 'copper', 'platinum', 'palladium', 'nickel', 'zinc', 'lithium']:
            # Multiple patterns to try
            patterns = [
                rf'{metal.title()}[^$]*\$?([\d,]+\.?\d*)[^+-]*([+-]?[\d.]+%?)',
                rf'<td[^>]*>{metal.title()}</td>.*?<td[^>]*>\$?([\d,]+\.?\d*)</td>.*?<td[^>]*>([+-]?[\d.]+%?)</td>'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        price = float(match.group(1).replace(',', ''))
                        change = match.group(2)
                        
                        commodities[metal] = {
                            'price': price,
                            'change': change,
                            'source': 'daily_metal_price'
                        }
                        break
                    except:
                        continue
        
        return {
            'success': True,
            'commodities': commodities,
            'content_size': len(content),
            'url': url
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'commodities': {},
            'url': url
        }


def main():
    """Main execution function"""
    
    print("🎯 QUICK METAL PRICES SCRAPING - AUGUST 4, 2025")
    print("=" * 60)
    
    start_time = time.time()
    
    # Results structure
    results = {
        'scraping_started': datetime.now().isoformat(),
        'target_date': '2025-08-04',
        'sites_scraped': {},
        'consolidated_data': {},
        'performance_log': [],
        'errors': [],
        'summary': {}
    }
    
    # Define scrapers
    scrapers = [
        ('trading_economics', quick_scrape_trading_economics),
        ('kitco_precious', quick_scrape_kitco_precious),
        ('kitco_base', quick_scrape_kitco_base),
        ('daily_metal_price', quick_scrape_daily_metal_price)
    ]
    
    # Run each scraper
    for site_name, scraper_func in scrapers:
        site_start = time.time()
        
        try:
            site_data = scraper_func()
            results['sites_scraped'][site_name] = site_data
            
            # Add to consolidated data
            for commodity, data in site_data.get('commodities', {}).items():
                if commodity not in results['consolidated_data']:
                    results['consolidated_data'][commodity] = {}
                results['consolidated_data'][commodity][site_name] = data
            
            # Log performance
            duration = time.time() - site_start
            results['performance_log'].append({
                'site': site_name,
                'success': site_data.get('success', False),
                'response_time': duration,
                'commodities_found': len(site_data.get('commodities', {})),
                'error': site_data.get('error')
            })
            
            if site_data.get('success'):
                print(f"✅ {site_name}: {len(site_data.get('commodities', {}))} commodities in {duration:.1f}s")
            else:
                print(f"❌ {site_name}: {site_data.get('error', 'Unknown error')}")
                results['errors'].append(f"{site_name}: {site_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            duration = time.time() - site_start
            error_msg = f"{site_name}: {str(e)}"
            results['errors'].append(error_msg)
            results['performance_log'].append({
                'site': site_name,
                'success': False,
                'response_time': duration,
                'error': str(e)
            })
            print(f"❌ {site_name}: {str(e)}")
        
        # Rate limiting
        time.sleep(1)
    
    # Generate summary
    total_time = time.time() - start_time
    results['scraping_completed'] = datetime.now().isoformat()
    
    successful_sites = len([p for p in results['performance_log'] if p.get('success', False)])
    total_commodities = len(results['consolidated_data'])
    
    results['summary'] = {
        'total_duration': total_time,
        'sites_attempted': len(scrapers),
        'sites_successful': successful_sites,
        'unique_commodities': total_commodities,
        'total_data_points': sum(len(sources) for sources in results['consolidated_data'].values())
    }
    
    # Calculate consensus prices
    consensus_prices = {}
    for commodity, sources in results['consolidated_data'].items():
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
            consensus_prices[commodity] = {
                'average_price': sum(prices) / len(prices),
                'price_range': f"${min(prices):.2f} - ${max(prices):.2f}",
                'sources_count': len(prices),
                'average_change': sum(changes) / len(changes) if changes else 0
            }
    
    results['consensus_prices'] = consensus_prices
    
    # Save results
    reports_dir = Path("/Projects/Resource Capital/reports/2025-08-04")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = reports_dir / "metal_prices_data.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 QUICK SCRAPING RESULTS")
    print("=" * 60)
    print(f"🕒 Total Duration: {total_time:.1f} seconds")
    print(f"🌐 Sites Successful: {successful_sites}/{len(scrapers)}")
    print(f"📈 Unique Commodities: {total_commodities}")
    print(f"📊 Total Data Points: {results['summary']['total_data_points']}")
    
    if consensus_prices:
        print(f"\n💰 COMMODITY CONSENSUS PRICES:")
        for commodity, consensus in consensus_prices.items():
            avg_price = consensus['average_price']
            avg_change = consensus['average_change']
            sources = consensus['sources_count']
            change_direction = "↑" if avg_change > 0 else "↓" if avg_change < 0 else "→"
            
            print(f"   {commodity.title()}: ${avg_price:.2f} {change_direction} {avg_change:+.1f}% (from {sources} sources)")
    
    if results['errors']:
        print(f"\n⚠️  ERRORS ENCOUNTERED:")
        for error in results['errors']:
            print(f"   • {error}")
    
    print(f"\n💾 Results saved to: {results_file}")
    print("=" * 60)
    print("🎉 Quick metal prices scraping completed successfully!")
    
    return results


if __name__ == "__main__":
    main()