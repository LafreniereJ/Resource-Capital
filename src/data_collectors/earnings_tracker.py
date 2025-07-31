"""
Earnings tracker for TSX/TSXV mining companies
Monitors upcoming and recent earnings releases
"""
import json
import requests
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import *

class EarningsTracker:
    def __init__(self):
        self.companies = self.load_companies()
        self.ensure_data_dirs()
    
    def load_companies(self):
        """Load company list from config"""
        with open('config/companies.json', 'r') as f:
            return json.load(f)
    
    def ensure_data_dirs(self):
        """Create data directories if they don't exist"""
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(POSTS_DIR, exist_ok=True)
    
    def get_upcoming_earnings(self):
        """Get upcoming earnings dates for tracked companies"""
        upcoming_earnings = []
        
        for company in self.companies['major_tsx']:
            try:
                ticker = yf.Ticker(company['symbol'])
                
                # Get calendar data
                calendar = ticker.calendar
                if calendar is not None and not calendar.empty:
                    earnings_date = calendar.index[0]
                    
                    upcoming_earnings.append({
                        'symbol': company['symbol'],
                        'name': company['name'],
                        'sector': company['sector'],
                        'earnings_date': earnings_date.strftime('%Y-%m-%d'),
                        'days_until': (earnings_date.date() - datetime.now().date()).days
                    })
                    
                print(f" Processed {company['symbol']}")
                
            except Exception as e:
                print(f" Error processing {company['symbol']}: {str(e)}")
                continue
        
        return upcoming_earnings
    
    def get_recent_earnings(self):
        """Get recent earnings results for tracked companies"""
        recent_earnings = []
        cutoff_date = datetime.now() - timedelta(days=EARNINGS_LOOKBACK_DAYS)
        
        for company in self.companies['major_tsx']:
            try:
                ticker = yf.Ticker(company['symbol'])
                
                # Get recent quarterly results
                quarterly_results = ticker.quarterly_financials
                if quarterly_results is not None and not quarterly_results.empty:
                    latest_quarter = quarterly_results.columns[0]
                    
                    if latest_quarter >= cutoff_date:
                        recent_earnings.append({
                            'symbol': company['symbol'],
                            'name': company['name'],
                            'sector': company['sector'],
                            'quarter_end': latest_quarter.strftime('%Y-%m-%d'),
                            'days_ago': (datetime.now().date() - latest_quarter.date()).days
                        })
                
                print(f" Checked recent earnings for {company['symbol']}")
                
            except Exception as e:
                print(f" Error checking {company['symbol']}: {str(e)}")
                continue
        
        return recent_earnings
    
    def save_earnings_data(self, upcoming, recent):
        """Save earnings data to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save raw data
        earnings_data = {
            'updated_at': datetime.now().isoformat(),
            'upcoming_earnings': upcoming,
            'recent_earnings': recent
        }
        
        with open(f'{RAW_DATA_DIR}/earnings_{timestamp}.json', 'w') as f:
            json.dump(earnings_data, f, indent=2)
        
        # Save latest data
        with open(f'{PROCESSED_DATA_DIR}/latest_earnings.json', 'w') as f:
            json.dump(earnings_data, f, indent=2)
        
        print(f"=¾ Saved earnings data to files")
        return earnings_data
    
    def run_update(self):
        """Run full earnings update process"""
        print("= Starting earnings tracker update...")
        print(f"=Å {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        upcoming = self.get_upcoming_earnings()
        recent = self.get_recent_earnings()
        
        earnings_data = self.save_earnings_data(upcoming, recent)
        
        print(f"\n=Ê Results:")
        print(f"   Upcoming earnings: {len(upcoming)} companies")
        print(f"   Recent earnings: {len(recent)} companies")
        print(" Earnings tracker update complete!")
        
        return earnings_data

if __name__ == "__main__":
    tracker = EarningsTracker()
    tracker.run_update()