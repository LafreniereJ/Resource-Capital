#!/usr/bin/env python3
"""
Analyze Company Dataset Quality
Review the Canadian mining companies Excel file to identify quality issues
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_canadian_mining_dataset():
    """Analyze the Canadian mining companies dataset"""
    print("📊 Analyzing Canadian Mining Companies Dataset")
    print("=" * 60)
    
    try:
        # Read the Excel file
        xlsx_file = "data/processed/canadian_mining_companies_filtered.xlsx"
        
        # Try to read different sheet names
        excel_file = pd.ExcelFile(xlsx_file)
        print(f"📋 Available sheets: {excel_file.sheet_names}")
        
        all_companies = []
        
        # Read all sheets
        for sheet_name in excel_file.sheet_names:
            print(f"\n📊 Analyzing sheet: {sheet_name}")
            df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
            
            print(f"   Columns: {list(df.columns)}")
            print(f"   Total rows: {len(df)}")
            
            # Add sheet info
            df['Sheet_Source'] = sheet_name
            all_companies.append(df)
        
        # Combine all sheets
        combined_df = pd.concat(all_companies, ignore_index=True)
        print(f"\n🔢 TOTAL DATASET OVERVIEW:")
        print(f"   Total companies across all sheets: {len(combined_df)}")
        
        # Analyze key columns if they exist
        if 'Market Cap' in combined_df.columns:
            analyze_market_caps(combined_df)
        
        if 'Root Ticker' in combined_df.columns:
            analyze_tickers(combined_df)
        
        if 'Company Name' in combined_df.columns:
            analyze_company_names(combined_df)
        
        # Analyze by exchange
        if 'Sheet_Source' in combined_df.columns:
            analyze_by_exchange(combined_df)
        
        # Look for quality issues
        identify_quality_issues(combined_df)
        
        return combined_df
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None

def analyze_market_caps(df):
    """Analyze market cap distribution"""
    print(f"\n💰 MARKET CAP ANALYSIS:")
    
    if 'Market Cap' in df.columns:
        # Clean market cap data
        market_caps = pd.to_numeric(df['Market Cap'], errors='coerce')
        market_caps = market_caps.dropna()
        
        if len(market_caps) > 0:
            print(f"   Companies with market cap data: {len(market_caps)}")
            print(f"   Median market cap: ${market_caps.median():,.0f}")
            print(f"   Mean market cap: ${market_caps.mean():,.0f}")
            print(f"   Min market cap: ${market_caps.min():,.0f}")
            print(f"   Max market cap: ${market_caps.max():,.0f}")
            
            # Market cap distribution
            micro_cap = len(market_caps[market_caps < 50_000_000])  # Under $50M
            small_cap = len(market_caps[(market_caps >= 50_000_000) & (market_caps < 500_000_000)])  # $50M-$500M
            mid_cap = len(market_caps[(market_caps >= 500_000_000) & (market_caps < 2_000_000_000)])  # $500M-$2B
            large_cap = len(market_caps[market_caps >= 2_000_000_000])  # Over $2B
            
            print(f"\n   📊 Market Cap Distribution:")
            print(f"      Micro-cap (<$50M): {micro_cap} companies ({micro_cap/len(market_caps)*100:.1f}%)")
            print(f"      Small-cap ($50M-$500M): {small_cap} companies ({small_cap/len(market_caps)*100:.1f}%)")
            print(f"      Mid-cap ($500M-$2B): {mid_cap} companies ({mid_cap/len(market_caps)*100:.1f}%)")
            print(f"      Large-cap (>$2B): {large_cap} companies ({large_cap/len(market_caps)*100:.1f}%)")
            
            # Identify problematic companies
            problematic = market_caps[market_caps < 10_000_000]  # Under $10M
            if len(problematic) > 0:
                print(f"\n   ⚠️ Companies under $10M market cap: {len(problematic)}")
                print(f"      These are likely too small for quality analysis")

def analyze_tickers(df):
    """Analyze ticker symbols"""
    print(f"\n🎯 TICKER ANALYSIS:")
    
    if 'Root Ticker' in df.columns:
        tickers = df['Root Ticker'].dropna()
        print(f"   Companies with tickers: {len(tickers)}")
        print(f"   Unique tickers: {len(tickers.unique())}")
        
        # Check for duplicates
        duplicates = tickers[tickers.duplicated()]
        if len(duplicates) > 0:
            print(f"   ⚠️ Duplicate tickers found: {len(duplicates)}")
        
        # Check ticker format
        if len(tickers) > 0:
            sample_tickers = tickers.head(10).tolist()
            print(f"   Sample tickers: {sample_tickers}")

def analyze_company_names(df):
    """Analyze company names for quality"""
    print(f"\n🏢 COMPANY NAME ANALYSIS:")
    
    if 'Company Name' in df.columns:
        names = df['Company Name'].dropna()
        print(f"   Companies with names: {len(names)}")
        
        # Look for concerning patterns
        shell_indicators = ['corp', 'inc.', 'ltd.', 'capital', 'ventures', 'resources']
        exploration_only = names[names.str.lower().str.contains('exploration|prospect', na=False)]
        
        if len(exploration_only) > 0:
            print(f"   Companies with 'exploration' in name: {len(exploration_only)}")
            print(f"   (These might be exploration-only, not producers)")

def analyze_by_exchange(df):
    """Analyze companies by exchange"""
    print(f"\n📈 EXCHANGE ANALYSIS:")
    
    exchange_counts = df['Sheet_Source'].value_counts()
    print(f"   Companies by source sheet:")
    for exchange, count in exchange_counts.items():
        print(f"      {exchange}: {count} companies")

def identify_quality_issues(df):
    """Identify potential quality issues"""
    print(f"\n⚠️ QUALITY ISSUES IDENTIFIED:")
    
    issues = []
    
    # Missing data issues
    if 'Company Name' in df.columns:
        missing_names = df['Company Name'].isna().sum()
        if missing_names > 0:
            issues.append(f"Missing company names: {missing_names}")
    
    if 'Root Ticker' in df.columns:
        missing_tickers = df['Root Ticker'].isna().sum()
        if missing_tickers > 0:
            issues.append(f"Missing tickers: {missing_tickers}")
    
    if 'Market Cap' in df.columns:
        market_caps = pd.to_numeric(df['Market Cap'], errors='coerce')
        missing_market_caps = market_caps.isna().sum()
        if missing_market_caps > 0:
            issues.append(f"Missing market cap data: {missing_market_caps}")
        
        # Very small market caps
        very_small = len(market_caps[market_caps < 5_000_000])
        if very_small > 0:
            issues.append(f"Companies under $5M market cap: {very_small} (likely too small)")
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("   ✅ No major quality issues detected")

def recommend_filtering_strategy(df):
    """Recommend filtering strategy based on analysis"""
    print(f"\n🎯 RECOMMENDED FILTERING STRATEGY:")
    
    if 'Market Cap' in df.columns:
        market_caps = pd.to_numeric(df['Market Cap'], errors='coerce')
        
        # Tier recommendations
        print(f"   📊 Proposed Company Tiers:")
        
        if len(market_caps.dropna()) > 0:
            tier1 = len(market_caps[market_caps >= 1_000_000_000])  # $1B+
            tier2 = len(market_caps[(market_caps >= 100_000_000) & (market_caps < 1_000_000_000)])  # $100M-$1B
            tier3 = len(market_caps[(market_caps >= 25_000_000) & (market_caps < 100_000_000)])  # $25M-$100M
            remove = len(market_caps[market_caps < 25_000_000])  # Under $25M
            
            print(f"      Tier 1 (Major, >$1B): {tier1} companies - Daily focus")
            print(f"      Tier 2 (Mid-cap, $100M-$1B): {tier2} companies - Weekly focus") 
            print(f"      Tier 3 (Small-cap, $25M-$100M): {tier3} companies - Monthly focus")
            print(f"      REMOVE (Micro-cap, <$25M): {remove} companies - Too small")
            
            total_quality = tier1 + tier2 + tier3
            print(f"\n   🎯 Quality universe: {total_quality} companies (vs {len(df)} current)")
            print(f"   📊 Reduction: {(len(df) - total_quality)/len(df)*100:.1f}% fewer companies")
            print(f"   ✅ Focus: {total_quality} high-quality, relevant companies")

def main():
    """Main analysis function"""
    print("🔍 Canadian Mining Companies Dataset Analysis")
    print("=" * 80)
    
    df = analyze_canadian_mining_dataset()
    
    if df is not None:
        recommend_filtering_strategy(df)
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Remove micro-cap companies (<$25M market cap)")
        print(f"   2. Focus on TSX-listed companies first")
        print(f"   3. Verify operational status (producing vs exploring)")
        print(f"   4. Implement tiered monitoring based on market cap")
        print(f"   5. Regular cleanup of delisted/inactive companies")
        
        # Save summary
        summary = {
            'total_companies': len(df),
            'analysis_date': datetime.now().isoformat(),
            'has_market_cap_data': 'Market Cap' in df.columns,
            'has_ticker_data': 'Root Ticker' in df.columns,
            'sheets_analyzed': df['Sheet_Source'].unique().tolist() if 'Sheet_Source' in df.columns else []
        }
        
        print(f"\n📊 Analysis complete. Dataset contains {len(df)} companies total.")
        return summary
    
    else:
        print("❌ Unable to complete analysis")
        return None

if __name__ == "__main__":
    main()