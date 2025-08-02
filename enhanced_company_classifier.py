#!/usr/bin/env python3
"""
Enhanced Company Classifier
Creates comprehensive company classification system including exploration companies
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import yfinance as yf

class EnhancedCompanyClassifier:
    """Classifies mining companies by stage, commodity, geography, and intelligence priority"""
    
    def __init__(self):
        self.commodity_categories = {
            'Precious Metals': ['Gold', 'Silver', 'Platinum/PGM'],
            'Base Metals': ['Copper', 'Nickel', 'Lead', 'Zinc', 'Iron'],
            'Energy Metals': ['Uranium', 'Coal'],
            'Technology Metals': ['Lithium', 'Rare Earths', 'Molybdenum', 'Tungsten'],
            'Industrial Minerals': ['Potash', 'Diamond'],
            'Energy': ['Oil and Gas'],
            'Diversified': ['Base & Precious Metals'],
            'Royalties': ['Royalty Streaming'],
            'Other': ['Other Properties']
        }
        
        self.canadian_provinces = {
            'BC': 'British Columbia',
            'AB': 'Alberta', 
            'SK': 'Saskatchewan',
            'MB': 'Manitoba',
            'ON': 'Ontario',
            'QC': 'Quebec',
            'NB': 'New Brunswick',
            'NS': 'Nova Scotia',
            'PE': 'Prince Edward Island',
            'NL': 'Newfoundland and Labrador',
            'YT': 'Yukon',
            'NT': 'Northwest Territories',
            'NU': 'Nunavut'
        }
        
        self.stage_keywords = {
            'Producer': ['production', 'producing', 'mine', 'mining', 'operations'],
            'Developer': ['development', 'construction', 'feasibility', 'permitting'],
            'Explorer': ['exploration', 'prospect', 'discovery', 'drilling', 'claims']
        }
    
    def load_and_prepare_data(self):
        """Load and combine TSX/TSXV data"""
        print("📊 Loading and preparing company data...")
        
        tsx_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                              sheet_name='TSX Canadian Companies')
        tsxv_df = pd.read_excel("data/processed/canadian_mining_companies_filtered.xlsx", 
                               sheet_name='TSXV Canadian Companies')
        
        # Add exchange info
        tsx_df['Exchange'] = 'TSX'
        tsxv_df['Exchange'] = 'TSXV'
        
        # Standardize column names between sheets
        if 'Sub Sector' in tsx_df.columns and 'Sub-Sector' in tsxv_df.columns:
            tsx_df = tsx_df.rename(columns={'Sub Sector': 'Sub_Sector'})
            tsxv_df = tsxv_df.rename(columns={'Sub-Sector': 'Sub_Sector'})
        
        # Combine datasets
        combined_df = pd.concat([tsx_df, tsxv_df], ignore_index=True)
        
        print(f"✅ Loaded {len(combined_df)} companies ({len(tsx_df)} TSX + {len(tsxv_df)} TSXV)")
        
        return combined_df
    
    def classify_primary_commodity(self, row):
        """Determine primary commodity focus for a company"""
        commodity_columns = [
            'Oil and Gas', 'Gold', 'Silver', 'Copper', 'Nickel', 'Diamond', 
            'Molybdenum', 'Platinum/PGM', 'Iron', 'Lead', 'Zinc', 'Rare Earths', 
            'Potash', 'Lithium', 'Uranium', 'Coal', 'Tungsten', 
            'Base & Precious Metals', 'Royalty Streaming', 'Other Properties'
        ]
        
        # Find commodities with exposure
        exposed_commodities = []
        for commodity in commodity_columns:
            if commodity in row and pd.notna(row[commodity]) and row[commodity] != 0:
                exposed_commodities.append(commodity)
        
        # Determine primary commodity
        if len(exposed_commodities) == 0:
            return 'Unknown', 'Other'
        elif len(exposed_commodities) == 1:
            primary = exposed_commodities[0]
        else:
            # For multiple commodities, prioritize by importance/value
            priority_order = ['Gold', 'Copper', 'Silver', 'Lithium', 'Uranium', 'Nickel', 'Zinc']
            primary = None
            for priority_commodity in priority_order:
                if priority_commodity in exposed_commodities:
                    primary = priority_commodity
                    break
            if not primary:
                primary = exposed_commodities[0]  # Fallback to first one
        
        # Determine commodity category
        commodity_category = 'Other'
        for category, commodities in self.commodity_categories.items():
            if primary in commodities:
                commodity_category = category
                break
        
        return primary, commodity_category
    
    def classify_company_stage(self, row):
        """Classify company by development stage"""
        market_cap = pd.to_numeric(row.get('Market Cap (C$) 30-June-2025', 0), errors='coerce')
        if pd.isna(market_cap):
            market_cap = 0
        
        exchange = row.get('Exchange', '')
        company_name = str(row.get('Name', '')).lower()
        
        # Stage classification logic
        if market_cap >= 1_000_000_000:  # $1B+
            # Large companies are likely producers
            stage = 'Producer'
            operational_status = 'Operating'
            
        elif market_cap >= 500_000_000:  # $500M - $1B
            # Mid-large companies - likely producers or advanced developers
            if exchange == 'TSX':
                stage = 'Producer'
                operational_status = 'Operating'
            else:
                stage = 'Developer'
                operational_status = 'Construction'
                
        elif market_cap >= 100_000_000:  # $100M - $500M
            # Mid-cap companies - mix of producers and developers
            if exchange == 'TSX':
                stage = 'Producer'
                operational_status = 'Operating'
            else:
                stage = 'Developer'
                operational_status = 'Permitting'
                
        elif market_cap >= 25_000_000:  # $25M - $100M
            # Small companies - likely developers or advanced explorers
            if exchange == 'TSX':
                stage = 'Developer'
                operational_status = 'Construction'
            else:
                stage = 'Advanced Explorer'
                operational_status = 'Feasibility'
                
        elif market_cap >= 5_000_000:  # $5M - $25M
            # Small companies - likely explorers
            stage = 'Explorer'
            operational_status = 'Exploration'
            
        else:  # <$5M
            # Very small - early stage explorers
            stage = 'Early Explorer'
            operational_status = 'Early Exploration'
        
        # Adjust based on name keywords
        for stage_type, keywords in self.stage_keywords.items():
            if any(keyword in company_name for keyword in keywords):
                if stage_type == 'Producer' and stage in ['Developer', 'Explorer', 'Advanced Explorer']:
                    stage = 'Producer'
                    operational_status = 'Operating'
                elif stage_type == 'Explorer' and stage == 'Producer':
                    stage = 'Advanced Explorer'
                    operational_status = 'Exploration'
        
        return stage, operational_status
    
    def calculate_intelligence_tier(self, row, stage, primary_commodity, canadian_operations_pct):
        """Calculate intelligence monitoring tier"""
        market_cap = pd.to_numeric(row.get('Market Cap (C$) 30-June-2025', 0), errors='coerce')
        if pd.isna(market_cap):
            market_cap = 0
        
        exchange = row.get('Exchange', '')
        
        # Base scoring
        score = 0
        
        # Market cap scoring
        if market_cap >= 1_000_000_000:
            score += 40
        elif market_cap >= 250_000_000:
            score += 30
        elif market_cap >= 50_000_000:
            score += 20
        elif market_cap >= 10_000_000:
            score += 10
        
        # Exchange bonus
        if exchange == 'TSX':
            score += 20
        
        # Stage bonus
        stage_scores = {
            'Producer': 25,
            'Developer': 20,
            'Advanced Explorer': 15,
            'Explorer': 10,
            'Early Explorer': 5
        }
        score += stage_scores.get(stage, 0)
        
        # Canadian operations bonus
        if canadian_operations_pct >= 80:
            score += 15
        elif canadian_operations_pct >= 50:
            score += 10
        elif canadian_operations_pct >= 25:
            score += 5
        
        # Commodity priority bonus
        high_priority_commodities = ['Gold', 'Copper', 'Silver', 'Lithium', 'Uranium']
        if primary_commodity in high_priority_commodities:
            score += 10
        
        # Determine tier
        if score >= 80:
            tier = 1  # Daily monitoring
        elif score >= 60:
            tier = 2  # Weekly monitoring  
        elif score >= 40:
            tier = 3  # Monthly monitoring
        else:
            tier = 4  # Quarterly monitoring
        
        return tier, score
    
    def calculate_canadian_operations_percentage(self, row):
        """Estimate percentage of operations in Canada"""
        # Check operations geography columns
        canadian_ops = row.get('CANADA', 0)
        
        # Count total geographic exposures
        geo_columns = ['AFRICA', 'ASIA', 'AUS/NZ/PNG', 'CANADA', 'LATIN AMERICA', 'UK/EUROPE', 'USA']
        total_exposures = 0
        for geo in geo_columns:
            if geo in row and pd.notna(row[geo]) and row[geo] != 0:
                total_exposures += 1
        
        # Estimate Canadian percentage
        if total_exposures == 0:
            return 50  # Default assumption for Canadian companies
        elif canadian_ops and pd.notna(canadian_ops) and canadian_ops != 0:
            return max(100 / total_exposures, 25)  # At least 25% if they have Canadian ops
        else:
            return 0  # No Canadian operations indicated
    
    def enhance_dataset(self, df):
        """Add all enhanced classification attributes"""
        print("🔧 Enhancing dataset with classifications...")
        
        enhanced_df = df.copy()
        
        # Initialize new columns
        enhanced_columns = {
            'Primary_Commodity': [],
            'Commodity_Category': [],
            'Secondary_Commodities': [],
            'Company_Stage': [],
            'Operational_Status': [],
            'Canadian_Operations_Pct': [],
            'Intelligence_Tier': [],
            'Priority_Score': [],
            'Market_Cap_Tier': [],
            'HQ_Province_Full': [],
            'Last_Updated': []
        }
        
        for idx, row in df.iterrows():
            # Commodity classification
            primary_commodity, commodity_category = self.classify_primary_commodity(row)
            enhanced_columns['Primary_Commodity'].append(primary_commodity)
            enhanced_columns['Commodity_Category'].append(commodity_category)
            
            # Secondary commodities (all others)
            commodity_columns = [
                'Oil and Gas', 'Gold', 'Silver', 'Copper', 'Nickel', 'Diamond', 
                'Molybdenum', 'Platinum/PGM', 'Iron', 'Lead', 'Zinc', 'Rare Earths', 
                'Potash', 'Lithium', 'Uranium', 'Coal', 'Tungsten', 
                'Base & Precious Metals', 'Royalty Streaming', 'Other Properties'
            ]
            secondary = []
            for commodity in commodity_columns:
                if (commodity in row and pd.notna(row[commodity]) and 
                    row[commodity] != 0 and commodity != primary_commodity):
                    secondary.append(commodity)
            enhanced_columns['Secondary_Commodities'].append(', '.join(secondary) if secondary else '')
            
            # Stage classification
            stage, operational_status = self.classify_company_stage(row)
            enhanced_columns['Company_Stage'].append(stage)
            enhanced_columns['Operational_Status'].append(operational_status)
            
            # Canadian operations
            canadian_pct = self.calculate_canadian_operations_percentage(row)
            enhanced_columns['Canadian_Operations_Pct'].append(canadian_pct)
            
            # Intelligence tier
            tier, priority_score = self.calculate_intelligence_tier(row, stage, primary_commodity, canadian_pct)
            enhanced_columns['Intelligence_Tier'].append(tier)
            enhanced_columns['Priority_Score'].append(priority_score)
            
            # Market cap tier
            market_cap = pd.to_numeric(row.get('Market Cap (C$) 30-June-2025', 0), errors='coerce')
            if pd.isna(market_cap):
                market_cap = 0
                
            if market_cap >= 5_000_000_000:
                cap_tier = 'Mega'
            elif market_cap >= 1_000_000_000:
                cap_tier = 'Large'
            elif market_cap >= 250_000_000:
                cap_tier = 'Mid'
            elif market_cap >= 50_000_000:
                cap_tier = 'Small'
            elif market_cap >= 10_000_000:
                cap_tier = 'Micro'
            else:
                cap_tier = 'Nano'
            enhanced_columns['Market_Cap_Tier'].append(cap_tier)
            
            # HQ Province full name
            hq_location = row.get('HQ Location', '')
            province_full = self.canadian_provinces.get(hq_location, hq_location)
            enhanced_columns['HQ_Province_Full'].append(province_full)
            
            # Last updated
            enhanced_columns['Last_Updated'].append(datetime.now().isoformat())
        
        # Add all new columns to dataframe
        for col_name, col_data in enhanced_columns.items():
            enhanced_df[col_name] = col_data
        
        print(f"✅ Enhanced dataset with {len(enhanced_columns)} new classification attributes")
        
        return enhanced_df
    
    def generate_classification_summary(self, enhanced_df):
        """Generate summary of the enhanced classification"""
        print("\n📊 ENHANCED CLASSIFICATION SUMMARY")
        print("=" * 60)
        
        # Stage distribution
        print("🏭 COMPANY STAGE DISTRIBUTION:")
        stage_counts = enhanced_df['Company_Stage'].value_counts()
        for stage, count in stage_counts.items():
            percentage = (count / len(enhanced_df)) * 100
            print(f"   {stage:20s}: {count:3d} companies ({percentage:4.1f}%)")
        
        # Commodity distribution
        print("\n💎 PRIMARY COMMODITY DISTRIBUTION:")
        commodity_counts = enhanced_df['Primary_Commodity'].value_counts()
        for commodity, count in commodity_counts.head(10).items():
            percentage = (count / len(enhanced_df)) * 100
            print(f"   {commodity:20s}: {count:3d} companies ({percentage:4.1f}%)")
        
        # Intelligence tier distribution
        print("\n🎯 INTELLIGENCE TIER DISTRIBUTION:")
        tier_counts = enhanced_df['Intelligence_Tier'].value_counts().sort_index()
        tier_names = {1: 'Daily', 2: 'Weekly', 3: 'Monthly', 4: 'Quarterly'}
        for tier, count in tier_counts.items():
            percentage = (count / len(enhanced_df)) * 100
            tier_name = tier_names.get(tier, f'Tier {tier}')
            print(f"   Tier {tier} ({tier_name:9s}): {count:3d} companies ({percentage:4.1f}%)")
        
        # Market cap tier distribution
        print("\n💰 MARKET CAP TIER DISTRIBUTION:")
        cap_tier_counts = enhanced_df['Market_Cap_Tier'].value_counts()
        tier_order = ['Mega', 'Large', 'Mid', 'Small', 'Micro', 'Nano']
        for tier in tier_order:
            if tier in cap_tier_counts:
                count = cap_tier_counts[tier]
                percentage = (count / len(enhanced_df)) * 100
                print(f"   {tier:20s}: {count:3d} companies ({percentage:4.1f}%)")
        
        # Canadian operations
        print("\n🇨🇦 CANADIAN OPERATIONS ANALYSIS:")
        high_canadian = len(enhanced_df[enhanced_df['Canadian_Operations_Pct'] >= 75])
        medium_canadian = len(enhanced_df[(enhanced_df['Canadian_Operations_Pct'] >= 25) & 
                                         (enhanced_df['Canadian_Operations_Pct'] < 75)])
        low_canadian = len(enhanced_df[enhanced_df['Canadian_Operations_Pct'] < 25])
        
        print(f"   High Canadian focus (≥75%): {high_canadian} companies")
        print(f"   Medium Canadian focus (25-75%): {medium_canadian} companies") 
        print(f"   Low Canadian focus (<25%): {low_canadian} companies")
        
        return {
            'stage_distribution': stage_counts.to_dict(),
            'commodity_distribution': commodity_counts.to_dict(),
            'tier_distribution': tier_counts.to_dict(),
            'market_cap_distribution': cap_tier_counts.to_dict()
        }
    
    def save_enhanced_dataset(self, enhanced_df):
        """Save the enhanced dataset"""
        output_file = "data/processed/enhanced_canadian_mining_companies.xlsx"
        
        # Create separate sheets for different tiers
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # All companies
            enhanced_df.to_excel(writer, sheet_name='All Companies', index=False)
            
            # By intelligence tier
            for tier in [1, 2, 3, 4]:
                tier_df = enhanced_df[enhanced_df['Intelligence_Tier'] == tier]
                tier_names = {1: 'Tier 1 - Daily', 2: 'Tier 2 - Weekly', 
                             3: 'Tier 3 - Monthly', 4: 'Tier 4 - Quarterly'}
                sheet_name = tier_names[tier]
                tier_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # By stage
            for stage in ['Producer', 'Developer', 'Advanced Explorer', 'Explorer', 'Early Explorer']:
                stage_df = enhanced_df[enhanced_df['Company_Stage'] == stage]
                if not stage_df.empty:
                    stage_df.to_excel(writer, sheet_name=stage, index=False)
        
        print(f"✅ Enhanced dataset saved to: {output_file}")
        
        # Also save summary JSON
        summary_file = "data/processed/enhanced_classification_summary.json"
        summary = self.generate_classification_summary(enhanced_df)
        summary['total_companies'] = len(enhanced_df)
        summary['enhancement_date'] = datetime.now().isoformat()
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"✅ Classification summary saved to: {summary_file}")
        
        return output_file

def main():
    """Main function to run enhanced classification"""
    print("🚀 ENHANCED COMPANY CLASSIFICATION SYSTEM")
    print("=" * 80)
    
    classifier = EnhancedCompanyClassifier()
    
    # Load data
    df = classifier.load_and_prepare_data()
    
    # Enhance with classifications
    enhanced_df = classifier.enhance_dataset(df)
    
    # Generate summary
    summary = classifier.generate_classification_summary(enhanced_df)
    
    # Save enhanced dataset
    output_file = classifier.save_enhanced_dataset(enhanced_df)
    
    print(f"\n🎉 ENHANCEMENT COMPLETE!")
    print(f"📊 Processed {len(enhanced_df)} companies with comprehensive classification")
    print(f"💾 Enhanced dataset: {output_file}")
    print(f"🎯 Intelligence tiers: {len(enhanced_df[enhanced_df['Intelligence_Tier']==1])} daily, "
          f"{len(enhanced_df[enhanced_df['Intelligence_Tier']==2])} weekly, "
          f"{len(enhanced_df[enhanced_df['Intelligence_Tier']==3])} monthly")
    
    return enhanced_df

if __name__ == "__main__":
    main()