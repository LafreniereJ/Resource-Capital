#!/usr/bin/env python3
"""
Real Numerical Intelligence Scanner
Uses yfinance to get actual numerical data for TSX mining companies
"""

import yfinance as yf
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import sqlite3

def get_company_list():
    """Get company list from database"""
    try:
        conn = sqlite3.connect('mining_companies.db')
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, name, market_cap FROM companies ORDER BY market_cap DESC LIMIT 20')
        companies = cursor.fetchall()
        conn.close()
        return [(row[0], row[1], row[2]) for row in companies]
    except:
        # Fallback list of major TSX mining companies
        return [
            ('AEM.TO', 'Agnico Eagle Mines', None),
            ('K.TO', 'Kinross Gold', None),
            ('ABX.TO', 'Barrick Gold', None),
            ('FNV.TO', 'Franco-Nevada', None),
            ('FM.TO', 'First Quantum', None),
            ('LUN.TO', 'Lundin Mining', None),
            ('HBM.TO', 'Hudbay Minerals', None),
            ('ELD.TO', 'Eldorado Gold', None),
            ('CG.TO', 'Centerra Gold', None),
            ('IMG.TO', 'Iamgold', None)
        ]

def get_stock_data(symbols):
    """Get actual stock data using yfinance"""
    
    stock_data = {}
    
    for symbol, name, market_cap in symbols:
        try:
            ticker = yf.Ticker(symbol)
            
            # Get 5 days of data
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'][-1]
                previous_close = hist['Close'][-2] if len(hist) >= 2 else current_price
                
                price_change = current_price - previous_close
                percent_change = (price_change / previous_close) * 100
                volume = hist['Volume'][-1]
                
                # Get 52-week range
                info = ticker.info
                fifty_two_week_high = info.get('fiftyTwoWeekHigh', 'N/A')
                fifty_two_week_low = info.get('fiftyTwoWeekLow', 'N/A')
                market_cap_current = info.get('marketCap', 'N/A')
                
                stock_data[symbol] = {
                    'name': name,
                    'current_price': round(float(current_price), 2),
                    'price_change': round(float(price_change), 2),
                    'percent_change': round(float(percent_change), 2),
                    'volume': int(volume),
                    'fifty_two_week_high': fifty_two_week_high,
                    'fifty_two_week_low': fifty_two_week_low,
                    'market_cap': market_cap_current,
                    'date': hist.index[-1].strftime('%Y-%m-%d')
                }
                
                print(f"✓ {symbol}: ${current_price:.2f} ({percent_change:+.1f}%)")
        
        except Exception as e:
            print(f"✗ Error fetching {symbol}: {e}")
            continue
    
    return stock_data

def get_tsx_composite():
    """Get TSX Composite Index data"""
    
    try:
        tsx = yf.Ticker("^GSPTSE")
        hist = tsx.history(period="5d")
        
        if not hist.empty:
            current_level = hist['Close'][-1]
            previous_close = hist['Close'][-2] if len(hist) >= 2 else current_level
            
            change = current_level - previous_close
            percent_change = (change / previous_close) * 100
            volume = hist['Volume'][-1]
            
            return {
                'level': round(float(current_level), 2),
                'change': round(float(change), 2),
                'percent_change': round(float(percent_change), 2),
                'volume': int(volume),
                'date': hist.index[-1].strftime('%Y-%m-%d')
            }
    
    except Exception as e:
        print(f"Error fetching TSX data: {e}")
        return None

def get_gold_price():
    """Get gold futures price"""
    
    try:
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="5d")
        
        if not hist.empty:
            current_price = hist['Close'][-1]
            previous_close = hist['Close'][-2] if len(hist) >= 2 else current_price
            
            change = current_price - previous_close
            percent_change = (change / previous_close) * 100
            
            return {
                'price': round(float(current_price), 2),
                'change': round(float(change), 2),
                'percent_change': round(float(percent_change), 2),
                'date': hist.index[-1].strftime('%Y-%m-%d')
            }
    
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return None

def get_bank_of_canada_data():
    """Get Bank of Canada data"""
    
    data = {}
    
    try:
        # USD/CAD
        usd_cad_url = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=5"
        response = requests.get(usd_cad_url, timeout=10)
        
        if response.status_code == 200:
            boc_data = response.json()
            if boc_data.get('observations'):
                latest = boc_data['observations'][-1]
                data['usd_cad'] = {
                    'rate': float(latest['FXUSDCAD']['v']),
                    'date': latest['d']
                }
                
                # Weekly change
                if len(boc_data['observations']) >= 5:
                    week_ago = boc_data['observations'][0]
                    current = float(latest['FXUSDCAD']['v'])
                    previous = float(week_ago['FXUSDCAD']['v'])
                    data['usd_cad']['weekly_change'] = round(((current - previous) / previous) * 100, 2)
    
    except Exception as e:
        print(f"Error fetching BoC data: {e}")
    
    try:
        # Interest rate
        rate_url = "https://www.bankofcanada.ca/valet/observations/V122530/json?recent=1"
        response = requests.get(rate_url, timeout=10)
        
        if response.status_code == 200:
            rate_data = response.json()
            if rate_data.get('observations'):
                latest = rate_data['observations'][0]
                data['interest_rate'] = {
                    'rate': float(latest['V122530']['v']),
                    'date': latest['d']
                }
    
    except Exception as e:
        print(f"Error fetching BoC rate: {e}")
    
    return data

def generate_numerical_report():
    """Generate purely numerical report"""
    
    print("📊 REAL-TIME TSX MINING NUMERICAL DATA")
    print("=" * 42)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
    print(f"🕐 {datetime.now().strftime('%H:%M:%S')} UTC")
    print("")
    
    # Get companies
    companies = get_company_list()
    print(f"📋 Analyzing {len(companies)} TSX mining companies...")
    print("")
    
    # Get stock data
    print("📈 FETCHING STOCK DATA...")
    stock_data = get_stock_data(companies)
    
    print(f"\n📊 STOCK PERFORMANCE DATA")
    print("-" * 30)
    
    # Sort by percent change
    sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1]['percent_change'], reverse=True)
    
    for symbol, data in sorted_stocks:
        direction = "📈" if data['percent_change'] > 0 else "📉" if data['percent_change'] < 0 else "➡️"
        print(f"{direction} {symbol}:")
        print(f"   Price: ${data['current_price']}")
        print(f"   Change: ${data['price_change']:+.2f} ({data['percent_change']:+.1f}%)")
        print(f"   Volume: {data['volume']:,}")
        if data['fifty_two_week_high'] != 'N/A':
            print(f"   52W High: ${data['fifty_two_week_high']}")
        if data['fifty_two_week_low'] != 'N/A':
            print(f"   52W Low: ${data['fifty_two_week_low']}")
        if data['market_cap'] != 'N/A':
            print(f"   Market Cap: ${data['market_cap']:,}")
        print(f"   Date: {data['date']}")
        print("")
    
    # TSX Composite
    print("📊 TSX COMPOSITE INDEX")
    print("-" * 20)
    tsx_data = get_tsx_composite()
    if tsx_data:
        direction = "📈" if tsx_data['percent_change'] > 0 else "📉" if tsx_data['percent_change'] < 0 else "➡️"
        print(f"{direction} TSX Composite:")
        print(f"   Level: {tsx_data['level']:,.2f}")
        print(f"   Change: {tsx_data['change']:+.2f} ({tsx_data['percent_change']:+.1f}%)")
        print(f"   Volume: {tsx_data['volume']:,}")
        print(f"   Date: {tsx_data['date']}")
    else:
        print("TSX data unavailable")
    print("")
    
    # Gold Price
    print("🥇 GOLD FUTURES")
    print("-" * 13)
    gold_data = get_gold_price()
    if gold_data:
        direction = "📈" if gold_data['percent_change'] > 0 else "📉" if gold_data['percent_change'] < 0 else "➡️"
        print(f"{direction} Gold (GC=F):")
        print(f"   Price: ${gold_data['price']:.2f}")
        print(f"   Change: ${gold_data['change']:+.2f} ({gold_data['percent_change']:+.1f}%)")
        print(f"   Date: {gold_data['date']}")
    else:
        print("Gold price data unavailable")
    print("")
    
    # Bank of Canada
    print("🏦 BANK OF CANADA DATA")
    print("-" * 22)
    boc_data = get_bank_of_canada_data()
    if boc_data:
        if 'usd_cad' in boc_data:
            usd_cad = boc_data['usd_cad']
            print(f"USD/CAD Exchange Rate:")
            print(f"   Rate: {usd_cad['rate']:.4f}")
            if 'weekly_change' in usd_cad:
                print(f"   Weekly Change: {usd_cad['weekly_change']:+.2f}%")
            print(f"   Date: {usd_cad['date']}")
            print("")
        
        if 'interest_rate' in boc_data:
            rate = boc_data['interest_rate']
            print(f"Key Interest Rate:")
            print(f"   Rate: {rate['rate']:.2f}%")
            print(f"   Date: {rate['date']}")
    else:
        print("BoC data unavailable")
    print("")
    
    # Summary Statistics
    print("📋 NUMERICAL SUMMARY")
    print("-" * 18)
    
    if stock_data:
        positive_movers = len([s for s in stock_data.values() if s['percent_change'] > 0])
        negative_movers = len([s for s in stock_data.values() if s['percent_change'] < 0])
        flat_movers = len([s for s in stock_data.values() if s['percent_change'] == 0])
        
        avg_change = sum(s['percent_change'] for s in stock_data.values()) / len(stock_data)
        total_volume = sum(s['volume'] for s in stock_data.values())
        
        print(f"Stocks analyzed: {len(stock_data)}")
        print(f"Positive movers: {positive_movers}")
        print(f"Negative movers: {negative_movers}")
        print(f"Flat movers: {flat_movers}")
        print(f"Average change: {avg_change:+.2f}%")
        print(f"Total volume: {total_volume:,}")
        
        # Biggest movers
        if stock_data:
            biggest_gainer = max(stock_data.items(), key=lambda x: x[1]['percent_change'])
            biggest_loser = min(stock_data.items(), key=lambda x: x[1]['percent_change'])
            
            print(f"Biggest gainer: {biggest_gainer[0]} ({biggest_gainer[1]['percent_change']:+.1f}%)")
            print(f"Biggest loser: {biggest_loser[0]} ({biggest_loser[1]['percent_change']:+.1f}%)")
    
    print(f"\nData points collected: {len(stock_data) * 8 + (4 if tsx_data else 0) + (3 if gold_data else 0) + len(boc_data) * 2}")
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    return stock_data, tsx_data, gold_data, boc_data

if __name__ == "__main__":
    stock_data, tsx_data, gold_data, boc_data = generate_numerical_report()
    
    print("\n✅ Real-time numerical intelligence completed")
    print("🔢 All data sourced from live market feeds")