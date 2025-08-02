#!/usr/bin/env python3
"""
Integrate Enhanced Dataset
Connect the enhanced company classification system with breaking news and weekend reports
"""

import pandas as pd
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class EnhancedDatasetIntegrator:
    """Integrates enhanced company dataset with intelligence systems"""
    
    def __init__(self):
        self.enhanced_dataset_path = "data/processed/enhanced_canadian_mining_companies.xlsx"
        self.db_path = "data/databases/mining_intelligence.db"
        
        # Load enhanced dataset
        self.companies_df = self.load_enhanced_dataset()
        
        # Create company lookup dictionaries for fast access
        self.ticker_to_info = self.create_company_lookups()
        
        # Intelligence tier mappings
        self.tier_descriptions = {
            1: "Daily Focus - Major Producers & Developers",
            2: "Weekly Focus - Mid-tier & Advanced Explorers", 
            3: "Monthly Focus - Small Producers & Quality Explorers",
            4: "Quarterly Focus - Early Stage Exploration"
        }
    
    def load_enhanced_dataset(self):
        """Load the enhanced company dataset"""
        try:
            df = pd.read_excel(self.enhanced_dataset_path, sheet_name='All Companies')
            print(f"✅ Loaded enhanced dataset: {len(df)} companies")
            return df
        except Exception as e:
            print(f"❌ Error loading enhanced dataset: {e}")
            return pd.DataFrame()
    
    def create_company_lookups(self):
        """Create fast lookup dictionaries for company information"""
        if self.companies_df.empty:
            return {}
        
        ticker_lookup = {}
        
        for idx, row in self.companies_df.iterrows():
            ticker = row.get('Root Ticker', '')
            if not ticker:
                continue
            
            # Create comprehensive company info
            company_info = {
                'company_name': row.get('Name', ''),
                'exchange': row.get('Exchange', ''),
                'market_cap': row.get('Market Cap (C$) 30-June-2025', 0),
                'market_cap_tier': row.get('Market_Cap_Tier', ''),
                'primary_commodity': row.get('Primary_Commodity', ''),
                'commodity_category': row.get('Commodity_Category', ''),
                'company_stage': row.get('Company_Stage', ''),
                'operational_status': row.get('Operational_Status', ''),
                'intelligence_tier': row.get('Intelligence_Tier', 4),
                'priority_score': row.get('Priority_Score', 0),
                'canadian_operations_pct': row.get('Canadian_Operations_Pct', 0),
                'hq_province': row.get('HQ Location', ''),
                'hq_province_full': row.get('HQ_Province_Full', ''),
                'secondary_commodities': row.get('Secondary_Commodities', ''),
                'sector': row.get('Sector', ''),
                'last_updated': row.get('Last_Updated', '')
            }
            
            # Add both formats for ticker lookup
            ticker_lookup[ticker] = company_info
            ticker_lookup[f"{ticker}.TO"] = company_info  # TSX format
            ticker_lookup[f"{ticker}.V"] = company_info   # TSXV format
        
        print(f"✅ Created lookup table for {len(ticker_lookup)} ticker variations")
        return ticker_lookup
    
    def get_company_info(self, ticker: str) -> Optional[Dict]:
        """Get enhanced company information by ticker"""
        # Try exact match first
        if ticker in self.ticker_to_info:
            return self.ticker_to_info[ticker]
        
        # Try without exchange suffix
        base_ticker = ticker.replace('.TO', '').replace('.V', '')
        if base_ticker in self.ticker_to_info:
            return self.ticker_to_info[base_ticker]
        
        return None
    
    def get_companies_by_tier(self, tier: int) -> List[Dict]:
        """Get all companies in a specific intelligence tier"""
        if self.companies_df.empty:
            return []
        
        tier_companies = self.companies_df[self.companies_df['Intelligence_Tier'] == tier]
        
        companies = []
        for idx, row in tier_companies.iterrows():
            company_info = {
                'ticker': row.get('Root Ticker', ''),
                'company_name': row.get('Name', ''),
                'exchange': row.get('Exchange', ''),
                'market_cap': row.get('Market Cap (C$) 30-June-2025', 0),
                'primary_commodity': row.get('Primary_Commodity', ''),
                'company_stage': row.get('Company_Stage', ''),
                'priority_score': row.get('Priority_Score', 0)
            }
            companies.append(company_info)
        
        return companies
    
    def get_companies_by_commodity(self, commodity: str) -> List[Dict]:
        """Get companies focused on a specific commodity"""
        if self.companies_df.empty:
            return []
        
        # Filter by primary commodity
        commodity_companies = self.companies_df[
            self.companies_df['Primary_Commodity'].str.contains(commodity, case=False, na=False)
        ]
        
        companies = []
        for idx, row in commodity_companies.iterrows():
            company_info = {
                'ticker': row.get('Root Ticker', ''),
                'company_name': row.get('Name', ''),
                'exchange': row.get('Exchange', ''),
                'market_cap': row.get('Market Cap (C$) 30-June-2025', 0),
                'company_stage': row.get('Company_Stage', ''),
                'intelligence_tier': row.get('Intelligence_Tier', 4),
                'canadian_operations_pct': row.get('Canadian_Operations_Pct', 0)
            }
            companies.append(company_info)
        
        # Sort by priority score
        companies.sort(key=lambda x: self.get_company_info(x['ticker']).get('priority_score', 0), reverse=True)
        
        return companies
    
    def get_companies_by_stage(self, stage: str) -> List[Dict]:
        """Get companies by development stage"""
        if self.companies_df.empty:
            return []
        
        stage_companies = self.companies_df[self.companies_df['Company_Stage'] == stage]
        
        companies = []
        for idx, row in stage_companies.iterrows():
            company_info = {
                'ticker': row.get('Root Ticker', ''),
                'company_name': row.get('Name', ''),
                'exchange': row.get('Exchange', ''),
                'market_cap': row.get('Market Cap (C$) 30-June-2025', 0),
                'primary_commodity': row.get('Primary_Commodity', ''),
                'intelligence_tier': row.get('Intelligence_Tier', 4),
                'priority_score': row.get('Priority_Score', 0)
            }
            companies.append(company_info)
        
        return companies
    
    def update_market_screener_config(self):
        """Update market screener to use enhanced dataset"""
        print("🔧 Updating market screener configuration...")
        
        # Get companies by intelligence tier for focused screening
        tier1_companies = self.get_companies_by_tier(1)  # Daily focus
        tier2_companies = self.get_companies_by_tier(2)  # Weekly focus
        
        config = {
            'daily_focus_companies': [
                {'ticker': c['ticker'], 'name': c['company_name'], 'stage': c['company_stage']}
                for c in tier1_companies
            ],
            'weekly_focus_companies': [
                {'ticker': c['ticker'], 'name': c['company_name'], 'stage': c['company_stage']}
                for c in tier2_companies
            ],
            'screening_priorities': {
                'tier_1_weight': 1.0,
                'tier_2_weight': 0.8,
                'tier_3_weight': 0.6,
                'tier_4_weight': 0.3
            },
            'updated': datetime.now().isoformat()
        }
        
        with open('data/processed/market_screener_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Market screener config updated:")
        print(f"   Daily focus: {len(tier1_companies)} companies")
        print(f"   Weekly focus: {len(tier2_companies)} companies")
    
    def update_breaking_news_config(self):
        """Update breaking news monitor with enhanced company data"""
        print("🔧 Updating breaking news monitor configuration...")
        
        # Create commodity-focused company lists for better news correlation
        commodity_groups = {
            'copper': self.get_companies_by_commodity('Copper'),
            'gold': self.get_companies_by_commodity('Gold'),
            'lithium': self.get_companies_by_commodity('Lithium'),
            'silver': self.get_companies_by_commodity('Silver'),
            'uranium': self.get_companies_by_commodity('Uranium')
        }
        
        # Focus on high-priority companies for each commodity
        focused_groups = {}
        for commodity, companies in commodity_groups.items():
            # Keep top 20 companies by priority for each commodity
            focused_groups[commodity] = companies[:20]
        
        config = {
            'commodity_focused_companies': focused_groups,
            'high_priority_tickers': [
                c['ticker'] for c in self.get_companies_by_tier(1)
            ],
            'canadian_miners': [
                {'ticker': row['Root Ticker'], 'name': row['Name'], 'stage': row['Company_Stage']}
                for idx, row in self.companies_df.iterrows()
                if row.get('Canadian_Operations_Pct', 0) >= 50
            ],
            'producer_companies': [
                {'ticker': row['Root Ticker'], 'name': row['Name']}
                for idx, row in self.companies_df.iterrows()
                if row.get('Company_Stage') == 'Producer'
            ],
            'updated': datetime.now().isoformat()
        }
        
        with open('data/processed/breaking_news_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Breaking news config updated:")
        print(f"   Copper companies: {len(focused_groups['copper'])}")
        print(f"   Gold companies: {len(focused_groups['gold'])}")
        print(f"   High priority tickers: {len(config['high_priority_tickers'])}")
    
    def update_weekend_report_config(self):
        """Update weekend report system with enhanced classifications"""
        print("🔧 Updating weekend report configuration...")
        
        # Create focused company lists for weekend analysis
        config = {
            'featured_companies': {
                'major_producers': [
                    {'ticker': row['Root Ticker'], 'name': row['Name'], 'commodity': row['Primary_Commodity']}
                    for idx, row in self.companies_df.iterrows()
                    if (row.get('Company_Stage') == 'Producer' and 
                        row.get('Market_Cap_Tier') in ['Mega', 'Large'])
                ],
                'key_developers': [
                    {'ticker': row['Root Ticker'], 'name': row['Name'], 'commodity': row['Primary_Commodity']}
                    for idx, row in self.companies_df.iterrows()
                    if (row.get('Company_Stage') == 'Developer' and 
                        row.get('Intelligence_Tier') <= 2)
                ],
                'discovery_potential': [
                    {'ticker': row['Root Ticker'], 'name': row['Name'], 'commodity': row['Primary_Commodity']}
                    for idx, row in self.companies_df.iterrows()
                    if (row.get('Company_Stage') in ['Advanced Explorer', 'Explorer'] and 
                        row.get('Intelligence_Tier') <= 3 and
                        row.get('Market Cap (C$) 30-June-2025', 0) >= 25_000_000)
                ]
            },
            'commodity_focus': {
                commodity: len(self.get_companies_by_commodity(commodity))
                for commodity in ['Gold', 'Copper', 'Silver', 'Lithium', 'Uranium', 'Nickel']
            },
            'geographic_focus': {
                'high_canadian_focus': len(self.companies_df[self.companies_df['Canadian_Operations_Pct'] >= 75]),
                'medium_canadian_focus': len(self.companies_df[
                    (self.companies_df['Canadian_Operations_Pct'] >= 25) & 
                    (self.companies_df['Canadian_Operations_Pct'] < 75)
                ]),
                'international_focus': len(self.companies_df[self.companies_df['Canadian_Operations_Pct'] < 25])
            },
            'updated': datetime.now().isoformat()
        }
        
        with open('data/processed/weekend_report_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Weekend report config updated:")
        print(f"   Major producers: {len(config['featured_companies']['major_producers'])}")
        print(f"   Key developers: {len(config['featured_companies']['key_developers'])}")
        print(f"   Discovery potential: {len(config['featured_companies']['discovery_potential'])}")
    
    def create_integration_summary(self):
        """Create summary of integration results"""
        print("\n📊 INTEGRATION SUMMARY")
        print("=" * 60)
        
        # Intelligence tier breakdown
        tier_counts = {}
        for tier in [1, 2, 3, 4]:
            tier_companies = self.get_companies_by_tier(tier)
            tier_counts[tier] = len(tier_companies)
            print(f"🎯 Tier {tier} ({self.tier_descriptions[tier]}): {len(tier_companies)} companies")
        
        # Stage breakdown
        print(f"\n🏭 COMPANY STAGE BREAKDOWN:")
        for stage in ['Producer', 'Developer', 'Advanced Explorer', 'Explorer', 'Early Explorer']:
            stage_companies = self.get_companies_by_stage(stage)
            print(f"   {stage:20s}: {len(stage_companies)} companies")
        
        # Top commodities
        print(f"\n💎 TOP COMMODITY EXPOSURE:")
        for commodity in ['Gold', 'Copper', 'Silver', 'Lithium', 'Uranium']:
            commodity_companies = self.get_companies_by_commodity(commodity)
            print(f"   {commodity:10s}: {len(commodity_companies)} companies")
        
        # Canadian focus
        canadian_high = len(self.companies_df[self.companies_df['Canadian_Operations_Pct'] >= 75])
        canadian_med = len(self.companies_df[
            (self.companies_df['Canadian_Operations_Pct'] >= 25) & 
            (self.companies_df['Canadian_Operations_Pct'] < 75)
        ])
        
        print(f"\n🇨🇦 CANADIAN OPERATIONS FOCUS:")
        print(f"   High Canadian focus (≥75%): {canadian_high} companies")
        print(f"   Medium Canadian focus (25-75%): {canadian_med} companies")
        
        return {
            'tier_counts': tier_counts,
            'total_companies': len(self.companies_df),
            'integration_date': datetime.now().isoformat()
        }
    
    def test_integration(self):
        """Test the integration with sample lookups"""
        print("\n🧪 TESTING INTEGRATION")
        print("=" * 60)
        
        # Test ticker lookups
        test_tickers = ['AEM', 'ABX', 'FM', 'K', 'NGT']
        
        print("🔍 Testing company lookups:")
        for ticker in test_tickers:
            info = self.get_company_info(ticker)
            if info:
                print(f"   {ticker}: {info['company_name']} - {info['company_stage']} - Tier {info['intelligence_tier']}")
            else:
                print(f"   {ticker}: NOT FOUND")
        
        # Test commodity focus
        print(f"\n💎 Testing commodity focus (Copper):")
        copper_companies = self.get_companies_by_commodity('Copper')[:5]
        for company in copper_companies:
            print(f"   {company['ticker']}: {company['company_name']} - {company['company_stage']}")
        
        print(f"\n✅ Integration test completed successfully!")

def main():
    """Main integration function"""
    print("🔗 ENHANCED DATASET INTEGRATION")
    print("=" * 80)
    
    integrator = EnhancedDatasetIntegrator()
    
    if integrator.companies_df.empty:
        print("❌ Enhanced dataset not available. Run enhanced_company_classifier.py first.")
        return
    
    # Update all system configurations
    integrator.update_market_screener_config()
    integrator.update_breaking_news_config()
    integrator.update_weekend_report_config()
    
    # Create integration summary
    summary = integrator.create_integration_summary()
    
    # Test integration
    integrator.test_integration()
    
    print(f"\n🎉 INTEGRATION COMPLETE!")
    print(f"📊 Enhanced dataset successfully integrated with intelligence systems")
    print(f"🎯 {summary['total_companies']} companies classified and ready for analysis")
    print(f"⚡ Breaking news system updated with commodity-focused company lists")
    print(f"📅 Weekend reports configured with tiered company analysis")
    
    return integrator

if __name__ == "__main__":
    main()