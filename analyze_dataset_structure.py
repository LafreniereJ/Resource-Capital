#!/usr/bin/env python3
"""
Analyze Dataset Structure
Detailed analysis of current Excel dataset structure and available attributes
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

def analyze_current_structure():
    """Analyze the current dataset structure in detail"""
    print("📊 CURRENT DATASET STRUCTURE ANALYSIS")
    print("=" * 80)
    
    # Read both sheets
    tsx_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                          sheet_name='TSX Canadian Companies')
    tsxv_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                           sheet_name='TSXV Canadian Companies')
    
    print("📋 AVAILABLE COLUMNS ANALYSIS:")
    print("=" * 50)
    
    # Analyze TSX columns
    print(f"\n🏢 TSX Columns ({len(tsx_df.columns)} total):")
    tsx_columns = list(tsx_df.columns)
    for i, col in enumerate(tsx_columns, 1):
        print(f"   {i:2d}. {col}")
    
    # Analyze TSXV columns  
    print(f"\n🏢 TSXV Columns ({len(tsxv_df.columns)} total):")
    tsxv_columns = list(tsxv_df.columns)
    for i, col in enumerate(tsxv_columns, 1):
        print(f"   {i:2d}. {col}")
    
    # Find column differences
    tsx_only = set(tsx_columns) - set(tsxv_columns)
    tsxv_only = set(tsxv_columns) - set(tsx_columns)
    common = set(tsx_columns) & set(tsxv_columns)
    
    print(f"\n🔍 COLUMN COMPARISON:")
    print(f"   Common columns: {len(common)}")
    print(f"   TSX-only columns: {len(tsx_only)}")
    if tsx_only:
        for col in tsx_only:
            print(f"      • {col}")
    print(f"   TSXV-only columns: {len(tsxv_only)}")
    if tsxv_only:
        for col in tsxv_only:
            print(f"      • {col}")
    
    return tsx_df, tsxv_df, common, tsx_only, tsxv_only

def analyze_commodity_columns(tsx_df, tsxv_df):
    """Analyze commodity-related columns"""
    print(f"\n💎 COMMODITY COLUMNS ANALYSIS:")
    print("=" * 50)
    
    # Identify commodity columns
    commodity_columns = [
        'Oil and Gas', 'Gold', 'Silver', 'Copper', 'Nickel', 'Diamond', 
        'Molybdenum', 'Platinum/PGM', 'Iron', 'Lead', 'Zinc', 'Rare Earths', 
        'Potash', 'Lithium', 'Uranium', 'Coal', 'Tungsten', 
        'Base & Precious Metals', 'Royalty Streaming', 'Other Properties'
    ]
    
    # Combined dataset for analysis
    combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
    
    print(f"📊 Commodity Exposure Analysis (999 companies):")
    
    commodity_stats = {}
    for commodity in commodity_columns:
        if commodity in combined_df.columns:
            # Count non-null, non-zero values (assuming these indicate exposure)
            exposure_count = len(combined_df[combined_df[commodity].notna() & (combined_df[commodity] != 0)])
            total_count = len(combined_df[combined_df[commodity].notna()])
            commodity_stats[commodity] = {
                'companies_with_exposure': exposure_count,
                'total_with_data': total_count,
                'exposure_rate': exposure_count / total_count if total_count > 0 else 0
            }
            
            print(f"   {commodity:20s}: {exposure_count:3d} companies ({exposure_count/len(combined_df)*100:4.1f}%)")
    
    # Find companies with multiple commodity exposures
    print(f"\n🔍 DIVERSIFICATION ANALYSIS:")
    companies_with_commodities = combined_df.copy()
    
    # Count commodities per company
    commodity_counts = []
    for idx, row in companies_with_commodities.iterrows():
        count = 0
        for commodity in commodity_columns:
            if commodity in row and pd.notna(row[commodity]) and row[commodity] != 0:
                count += 1
        commodity_counts.append(count)
    
    companies_with_commodities['Commodity_Count'] = commodity_counts
    
    print(f"   Companies with 1 commodity: {len(companies_with_commodities[companies_with_commodities['Commodity_Count'] == 1])}")
    print(f"   Companies with 2+ commodities: {len(companies_with_commodities[companies_with_commodities['Commodity_Count'] >= 2])}")
    print(f"   Companies with 5+ commodities: {len(companies_with_commodities[companies_with_commodities['Commodity_Count'] >= 5])}")
    print(f"   Max commodities per company: {companies_with_commodities['Commodity_Count'].max()}")
    
    return commodity_stats

def analyze_geographic_columns(tsx_df, tsxv_df):
    """Analyze geographic/location columns"""
    print(f"\n🌍 GEOGRAPHIC COLUMNS ANALYSIS:")
    print("=" * 50)
    
    combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
    
    # HQ Location analysis
    if 'HQ Location' in combined_df.columns:
        hq_locations = combined_df['HQ Location'].value_counts()
        print(f"📍 Headquarters Locations (Top 10):")
        for location, count in hq_locations.head(10).items():
            print(f"   {location:25s}: {count:3d} companies")
    
    # Regional analysis
    if 'HQ Region' in combined_df.columns:
        hq_regions = combined_df['HQ Region'].value_counts()
        print(f"\n🌎 Headquarters Regions:")
        for region, count in hq_regions.items():
            print(f"   {region:25s}: {count:3d} companies")
    
    # Operations geography
    geographic_ops_columns = ['AFRICA', 'ASIA', 'AUS/NZ/PNG', 'CANADA', 'LATIN AMERICA', 'OTHER', 'UK/EUROPE', 'USA']
    
    print(f"\n🏭 OPERATIONS GEOGRAPHY:")
    for geo_col in geographic_ops_columns:
        if geo_col in combined_df.columns:
            ops_count = len(combined_df[combined_df[geo_col].notna() & (combined_df[geo_col] != 0)])
            print(f"   {geo_col:15s}: {ops_count:3d} companies ({ops_count/len(combined_df)*100:4.1f}%)")
    
    # Canadian operations focus
    if 'CANADA' in combined_df.columns:
        canadian_ops = combined_df[combined_df['CANADA'].notna() & (combined_df['CANADA'] != 0)]
        print(f"\n🇨🇦 CANADIAN OPERATIONS FOCUS:")
        print(f"   Companies with Canadian operations: {len(canadian_ops)} ({len(canadian_ops)/len(combined_df)*100:.1f}%)")

def analyze_financial_columns(tsx_df, tsxv_df):
    """Analyze financial and market data columns"""
    print(f"\n💰 FINANCIAL COLUMNS ANALYSIS:")
    print("=" * 50)
    
    combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
    
    # Market cap analysis (already done but summary here)
    market_cap_col = 'Market Cap (C$) 30-June-2025'
    if market_cap_col in combined_df.columns:
        market_caps = pd.to_numeric(combined_df[market_cap_col], errors='coerce')
        valid_caps = market_caps.dropna()
        
        print(f"📊 Market Cap Data Availability:")
        print(f"   Companies with market cap data: {len(valid_caps)}/{len(combined_df)} ({len(valid_caps)/len(combined_df)*100:.1f}%)")
        print(f"   Median market cap: ${valid_caps.median():,.0f} CAD")
        print(f"   Range: ${valid_caps.min():,.0f} to ${valid_caps.max():,.0f} CAD")
    
    # Trading activity analysis
    volume_col = 'Volume YTD 30-June-2025'
    if volume_col in combined_df.columns:
        volumes = pd.to_numeric(combined_df[volume_col], errors='coerce')
        valid_volumes = volumes.dropna()
        
        print(f"\n📈 Trading Activity:")
        print(f"   Companies with volume data: {len(valid_volumes)}/{len(combined_df)}")
        print(f"   Median YTD volume: {valid_volumes.median():,.0f}")
        print(f"   Companies with zero volume: {len(valid_volumes[valid_volumes == 0])}")

def identify_missing_attributes():
    """Identify what key attributes we need to add"""
    print(f"\n❌ MISSING KEY ATTRIBUTES FOR ENHANCED CLASSIFICATION:")
    print("=" * 50)
    
    missing_attributes = [
        "Company Stage (Producer/Developer/Explorer)",
        "Operational Status (Operating/Construction/Permitting/Exploration)",
        "Primary Commodity (single main focus)",
        "Revenue Status (Revenue generating vs Pre-revenue)",
        "Canadian Province Details (BC, ON, QC, etc.)",
        "Project Status/Phase",
        "Intelligence Priority Tier",
        "Last Updated Timestamp",
        "News Relevance Score",
        "Canadian Operations Percentage"
    ]
    
    print("🎯 Attributes to Add/Derive:")
    for i, attr in enumerate(missing_attributes, 1):
        print(f"   {i:2d}. {attr}")

def propose_enhanced_schema():
    """Propose the enhanced dataset schema"""
    print(f"\n🎯 PROPOSED ENHANCED SCHEMA:")
    print("=" * 50)
    
    schema = {
        "Core_Identity": [
            "Company_ID",
            "Company_Name", 
            "Ticker_Symbol",
            "Exchange",
            "Sector",
            "Sub_Sector"
        ],
        "Financial_Metrics": [
            "Market_Cap_CAD",
            "Market_Cap_USD", 
            "Market_Cap_Tier",
            "Outstanding_Shares",
            "YTD_Volume",
            "YTD_Value",
            "Revenue_TTM",
            "Revenue_Status"
        ],
        "Geographic_Details": [
            "HQ_Country",
            "HQ_Province_State",
            "HQ_City",
            "Canadian_Operations_Pct",
            "Primary_Operations_Country",
            "Operations_Provinces"
        ],
        "Commodity_Classification": [
            "Primary_Commodity",
            "Secondary_Commodities",
            "Commodity_Category",
            "Diversified_Portfolio",
            "Royalty_Streaming"
        ],
        "Stage_And_Status": [
            "Company_Stage",
            "Operational_Status", 
            "Production_Phase",
            "Development_Stage",
            "Project_Count"
        ],
        "Intelligence_Scoring": [
            "Intelligence_Tier",
            "Priority_Score",
            "Canadian_Relevance_Score",
            "News_Relevance_Score",
            "Last_Updated"
        ]
    }
    
    for category, fields in schema.items():
        print(f"\n📊 {category.replace('_', ' ')}:")
        for field in fields:
            print(f"   • {field}")
    
    return schema

def main():
    """Main analysis function"""
    print("🔍 COMPREHENSIVE DATASET STRUCTURE ANALYSIS")
    print("=" * 80)
    
    # Analyze current structure
    tsx_df, tsxv_df, common, tsx_only, tsxv_only = analyze_current_structure()
    
    # Analyze specific column types
    commodity_stats = analyze_commodity_columns(tsx_df, tsxv_df)
    analyze_geographic_columns(tsx_df, tsxv_df)
    analyze_financial_columns(tsx_df, tsxv_df)
    
    # Identify gaps and propose enhancements
    identify_missing_attributes()
    enhanced_schema = propose_enhanced_schema()
    
    print(f"\n" + "="*80)
    print("💡 SUMMARY:")
    print("   Current dataset has strong foundation with commodity and geographic data")
    print("   Missing key classification attributes for stage/status")
    print("   Need to derive Primary Commodity from boolean columns")
    print("   Can enhance with intelligence scoring and tier system")
    print("   Keep exploration companies but classify and prioritize appropriately")
    
    # Save analysis results
    analysis_results = {
        'analysis_date': datetime.now().isoformat(),
        'total_companies': len(tsx_df) + len(tsxv_df),
        'tsx_companies': len(tsx_df),
        'tsxv_companies': len(tsxv_df),
        'common_columns': len(common),
        'commodity_stats': commodity_stats,
        'proposed_schema': enhanced_schema
    }
    
    with open('data/processed/dataset_structure_analysis.json', 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\n📊 Analysis saved to: data/processed/dataset_structure_analysis.json")

if __name__ == "__main__":
    main()