#!/usr/bin/env python3
"""
Detailed Company Analysis
Deep dive into the 999 Canadian mining companies to identify quality issues
"""

import pandas as pd
import numpy as np
from datetime import datetime

def detailed_analysis():
    """Perform detailed analysis of the mining companies dataset"""
    print("🔍 DETAILED CANADIAN MINING COMPANIES ANALYSIS")
    print("=" * 80)
    
    # Read the Excel file
    tsx_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                          sheet_name='TSX Canadian Companies')
    tsxv_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                           sheet_name='TSXV Canadian Companies')
    
    print(f"📊 TSX Companies: {len(tsx_df)}")
    print(f"📊 TSXV Companies: {len(tsxv_df)}")
    
    # Analyze market caps
    analyze_market_caps_detailed(tsx_df, "TSX")
    analyze_market_caps_detailed(tsxv_df, "TSXV")
    
    # Analyze sectors
    analyze_sectors(tsx_df, tsxv_df)
    
    # Analyze trading activity
    analyze_trading_activity(tsx_df, tsxv_df)
    
    # Identify problematic companies
    identify_problematic_companies(tsx_df, tsxv_df)
    
    # Recommend filtering
    recommend_quality_filters(tsx_df, tsxv_df)

def analyze_market_caps_detailed(df, exchange):
    """Detailed market cap analysis"""
    print(f"\n💰 {exchange} MARKET CAP ANALYSIS:")
    
    market_cap_col = 'Market Cap (C$) 30-June-2025'
    if market_cap_col in df.columns:
        # Clean and convert market cap data
        market_caps = pd.to_numeric(df[market_cap_col], errors='coerce')
        valid_caps = market_caps.dropna()
        
        print(f"   Total companies: {len(df)}")
        print(f"   Companies with market cap data: {len(valid_caps)}")
        print(f"   Missing market cap data: {len(df) - len(valid_caps)}")
        
        if len(valid_caps) > 0:
            print(f"\n   📊 Market Cap Statistics (CAD):")
            print(f"      Median: ${valid_caps.median():,.0f}")
            print(f"      Mean: ${valid_caps.mean():,.0f}")
            print(f"      Min: ${valid_caps.min():,.0f}")
            print(f"      Max: ${valid_caps.max():,.0f}")
            
            # Detailed distribution
            ranges = [
                ("Micro (<$10M)", 0, 10_000_000),
                ("Small ($10M-$50M)", 10_000_000, 50_000_000),
                ("Small-Mid ($50M-$250M)", 50_000_000, 250_000_000),
                ("Mid ($250M-$1B)", 250_000_000, 1_000_000_000),
                ("Large ($1B-$5B)", 1_000_000_000, 5_000_000_000),
                ("Mega (>$5B)", 5_000_000_000, float('inf'))
            ]
            
            print(f"\n   📈 Detailed Size Distribution:")
            total_companies = len(valid_caps)
            
            for range_name, min_val, max_val in ranges:
                if max_val == float('inf'):
                    count = len(valid_caps[valid_caps >= min_val])
                else:
                    count = len(valid_caps[(valid_caps >= min_val) & (valid_caps < max_val)])
                
                percentage = (count / total_companies) * 100
                print(f"      {range_name}: {count} companies ({percentage:.1f}%)")
            
            # Show some examples
            print(f"\n   💎 {exchange} Examples by Size:")
            
            # Largest companies
            largest = df.nlargest(5, market_cap_col)
            if not largest.empty:
                print(f"      🏆 Top 5 Largest:")
                for idx, row in largest.iterrows():
                    name = str(row['Name'])[:40] + "..." if len(str(row['Name'])) > 40 else row['Name']
                    market_cap = row[market_cap_col]
                    ticker = row['Root Ticker']
                    print(f"         {ticker}: {name} (${market_cap:,.0f})")
            
            # Smallest companies (but with data)
            smallest = df.nsmallest(5, market_cap_col)
            if not smallest.empty:
                print(f"      ⚠️ Bottom 5 Smallest:")
                for idx, row in smallest.iterrows():
                    name = str(row['Name'])[:40] + "..." if len(str(row['Name'])) > 40 else row['Name']
                    market_cap = row[market_cap_col]
                    ticker = row['Root Ticker']
                    print(f"         {ticker}: {name} (${market_cap:,.0f})")

def analyze_sectors(tsx_df, tsxv_df):
    """Analyze sector distribution"""
    print(f"\n🏭 SECTOR ANALYSIS:")
    
    # TSX sectors
    if 'Sector' in tsx_df.columns:
        tsx_sectors = tsx_df['Sector'].value_counts()
        print(f"\n   📊 TSX Sectors:")
        for sector, count in tsx_sectors.head(10).items():
            print(f"      {sector}: {count} companies")
    
    # TSXV sectors  
    if 'Sector' in tsxv_df.columns:
        tsxv_sectors = tsxv_df['Sector'].value_counts()
        print(f"\n   📊 TSXV Sectors:")
        for sector, count in tsxv_sectors.head(10).items():
            print(f"      {sector}: {count} companies")

def analyze_trading_activity(tsx_df, tsxv_df):
    """Analyze trading activity"""
    print(f"\n📈 TRADING ACTIVITY ANALYSIS:")
    
    volume_col = 'Volume YTD 30-June-2025'
    
    for exchange, df in [("TSX", tsx_df), ("TSXV", tsxv_df)]:
        if volume_col in df.columns:
            volumes = pd.to_numeric(df[volume_col], errors='coerce')
            valid_volumes = volumes.dropna()
            
            if len(valid_volumes) > 0:
                zero_volume = len(valid_volumes[valid_volumes == 0])
                low_volume = len(valid_volumes[(valid_volumes > 0) & (valid_volumes < 100000)])
                
                print(f"\n   📊 {exchange} Trading Activity:")
                print(f"      Companies with volume data: {len(valid_volumes)}")
                print(f"      Zero volume (inactive): {zero_volume} ({zero_volume/len(valid_volumes)*100:.1f}%)")
                print(f"      Low volume (<100K): {low_volume} ({low_volume/len(valid_volumes)*100:.1f}%)")
                print(f"      Median volume: {valid_volumes.median():,.0f}")

def identify_problematic_companies(tsx_df, tsxv_df):
    """Identify companies that should be filtered out"""
    print(f"\n⚠️ PROBLEMATIC COMPANIES IDENTIFICATION:")
    
    market_cap_col = 'Market Cap (C$) 30-June-2025'
    volume_col = 'Volume YTD 30-June-2025'
    
    total_problematic = 0
    
    for exchange, df in [("TSX", tsx_df), ("TSXV", tsxv_df)]:
        print(f"\n   🔍 {exchange} Issues:")
        
        # Market cap issues
        if market_cap_col in df.columns:
            market_caps = pd.to_numeric(df[market_cap_col], errors='coerce')
            
            # Very small market caps
            micro_caps = len(market_caps[market_caps < 5_000_000])  # Under $5M
            tiny_caps = len(market_caps[market_caps < 1_000_000])   # Under $1M
            
            print(f"      Micro-cap (<$5M): {micro_caps} companies")
            print(f"      Tiny-cap (<$1M): {tiny_caps} companies")
            total_problematic += micro_caps
        
        # Trading activity issues
        if volume_col in df.columns:
            volumes = pd.to_numeric(df[volume_col], errors='coerce')
            inactive = len(volumes[volumes == 0])
            print(f"      Inactive (zero volume): {inactive} companies")
        
        # Name analysis for shell companies
        if 'Name' in df.columns:
            names = df['Name'].astype(str).str.lower()
            
            # Look for exploration-only companies
            exploration_only = names[names.str.contains('exploration|prospect|ventures', na=False)]
            capital_companies = names[names.str.contains(' capital | ventures | holdings', na=False)]
            
            print(f"      Exploration-only names: {len(exploration_only)} companies")
            print(f"      Capital/Holdings/Ventures: {len(capital_companies)} companies")
    
    print(f"\n   📊 Total potentially problematic: ~{total_problematic} companies")

def recommend_quality_filters(tsx_df, tsxv_df):
    """Recommend specific filtering criteria"""
    print(f"\n🎯 RECOMMENDED QUALITY FILTERS:")
    
    market_cap_col = 'Market Cap (C$) 30-June-2025'
    volume_col = 'Volume YTD 30-June-2025'
    
    # Analyze what we'd keep with different thresholds
    print(f"\n   📊 Filter Impact Analysis:")
    
    thresholds = [
        ("Conservative (>$25M)", 25_000_000),
        ("Moderate (>$10M)", 10_000_000),
        ("Aggressive (>$5M)", 5_000_000),
        ("Very Aggressive (>$1M)", 1_000_000)
    ]
    
    for threshold_name, min_cap in thresholds:
        tsx_kept = 0
        tsxv_kept = 0
        
        if market_cap_col in tsx_df.columns:
            tsx_caps = pd.to_numeric(tsx_df[market_cap_col], errors='coerce')
            tsx_kept = len(tsx_caps[tsx_caps >= min_cap])
        
        if market_cap_col in tsxv_df.columns:
            tsxv_caps = pd.to_numeric(tsxv_df[market_cap_col], errors='coerce')
            tsxv_kept = len(tsxv_caps[tsxv_caps >= min_cap])
        
        total_kept = tsx_kept + tsxv_kept
        print(f"      {threshold_name}: {total_kept} companies (TSX: {tsx_kept}, TSXV: {tsxv_kept})")
    
    print(f"\n   🎯 RECOMMENDED APPROACH:")
    print(f"      1. Start with TSX companies (142) - higher quality baseline")
    print(f"      2. Add TSXV companies with market cap > $25M")
    print(f"      3. Add TSXV companies with market cap > $10M that have:")
    print(f"         - Regular trading activity (YTD volume > 100K)")
    print(f"         - Production or near-production status")
    print(f"      4. Exclude exploration-only and shell companies")
    print(f"      5. Focus analysis on top ~200 highest quality companies")

def analyze_specific_examples(tsx_df, tsxv_df):
    """Show specific examples of companies in different categories"""
    print(f"\n📋 SPECIFIC COMPANY EXAMPLES:")
    
    market_cap_col = 'Market Cap (C$) 30-June-2025'
    
    # Show some micro-caps that might be problematic
    combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
    
    if market_cap_col in combined_df.columns:
        market_caps = pd.to_numeric(combined_df[market_cap_col], errors='coerce')
        
        # Very small companies
        micro_caps = combined_df[market_caps < 2_000_000].copy()
        if not micro_caps.empty:
            print(f"\n   ⚠️ Examples of Micro-Cap Companies (<$2M):")
            for idx, row in micro_caps.head(10).iterrows():
                name = str(row['Name'])[:50] + "..." if len(str(row['Name'])) > 50 else row['Name']
                market_cap = row[market_cap_col] if pd.notna(row[market_cap_col]) else "N/A"
                ticker = row['Root Ticker']
                exchange = "TSX" if row['Sheet_Source'] == 'TSX Canadian Companies' else "TSXV"
                
                if pd.notna(market_cap) and market_cap != "N/A":
                    print(f"         {ticker} ({exchange}): {name} - ${market_cap:,.0f}")
                else:
                    print(f"         {ticker} ({exchange}): {name} - No market cap data")

def main():
    """Main analysis function"""
    try:
        detailed_analysis()
        analyze_specific_examples(pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", sheet_name='TSX Canadian Companies'),
                                pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", sheet_name='TSXV Canadian Companies'))
        
        print(f"\n" + "="*80)
        print(f"🎯 CONCLUSION:")
        print(f"   Current dataset: 999 companies (142 TSX + 857 TSXV)")
        print(f"   Quality issue: Many micro-cap and inactive companies")
        print(f"   Recommendation: Filter to ~150-200 quality companies")
        print(f"   Focus: TSX companies + select TSXV companies >$25M market cap")
        print(f"   Result: Higher quality intelligence, less noise, better analysis")
        
    except Exception as e:
        print(f"❌ Error in detailed analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()