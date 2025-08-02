#!/usr/bin/env python3
"""
Magna Mining Data Extractor
Extracts key business information from scraped JSON data
"""

import json
import re
from datetime import datetime
from pathlib import Path

class MagnaDataExtractor:
    def __init__(self, json_file):
        self.json_file = json_file
        self.data = self.load_data()
        self.extracted_info = {
            'project_updates': [],
            'news_items': [],
            'financial_info': [],
            'operational_updates': [],
            'corporate_announcements': [],
            'key_metrics': {},
            'management_info': [],
            'contact_info': {}
        }
    
    def load_data(self):
        """Load the scraped JSON data"""
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_financial_keywords(self, text):
        """Extract financial-related information"""
        financial_keywords = [
            r'revenue', r'earnings', r'profit', r'loss', r'ebitda', r'cash flow',
            r'quarterly', r'annual', r'financial results', r'financial performance',
            r'guidance', r'forecast', r'outlook', r'budget', r'capital',
            r'investment', r'funding', r'financing', r'debt', r'equity',
            r'dividend', r'share price', r'market cap', r'valuation',
            r'\$[\d,]+', r'million', r'billion', r'CAD', r'USD'
        ]
        
        matches = []
        for keyword in financial_keywords:
            pattern = re.compile(keyword, re.IGNORECASE)
            found = pattern.findall(text)
            if found:
                matches.extend(found)
        
        return matches
    
    def extract_project_keywords(self, text):
        """Extract project and operational information"""
        project_keywords = [
            r'project', r'mine', r'mining', r'operation', r'production',
            r'exploration', r'development', r'construction', r'expansion',
            r'resource', r'reserve', r'ore', r'mineral', r'deposit',
            r'drilling', r'assay', r'grade', r'tonnage', r'processing',
            r'mill', r'plant', r'facility', r'infrastructure', r'equipment',
            r'nickel', r'copper', r'platinum', r'palladium', r'gold'
        ]
        
        matches = []
        for keyword in project_keywords:
            pattern = re.compile(keyword, re.IGNORECASE)
            found = pattern.findall(text)
            if found:
                matches.extend(found)
        
        return matches
    
    def extract_dates(self, text):
        """Extract dates from text"""
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            r'\bQ[1-4]\s+\d{4}\b',  # Q1 2024
            r'\b\d{4}\s+Q[1-4]\b'   # 2024 Q1
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates
    
    def extract_news_and_updates(self):
        """Extract news items and project updates"""
        news_content = ""
        
        # Look for news page content
        if 'news' in self.data:
            news_content = self.data['news'].get('content', '')
        
        # Look for investor page content
        if 'investors' in self.data:
            news_content += "\n" + self.data['investors'].get('content', '')
        
        # Look for home page content
        if 'home' in self.data:
            news_content += "\n" + self.data['home'].get('content', '')
        
        # Split content into sections and analyze
        paragraphs = news_content.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if len(para) < 50:  # Skip very short paragraphs
                continue
                
            # Check if paragraph contains financial info
            financial_matches = self.extract_financial_keywords(para)
            if financial_matches:
                dates = self.extract_dates(para)
                self.extracted_info['financial_info'].append({
                    'content': para,
                    'keywords': financial_matches,
                    'dates': dates
                })
            
            # Check if paragraph contains project info
            project_matches = self.extract_project_keywords(para)
            if project_matches:
                dates = self.extract_dates(para)
                self.extracted_info['project_updates'].append({
                    'content': para,
                    'keywords': project_matches,
                    'dates': dates
                })
            
            # Check for news-specific indicators
            news_indicators = ['announced', 'reports', 'today', 'press release', 'update']
            if any(indicator in para.lower() for indicator in news_indicators):
                dates = self.extract_dates(para)
                self.extracted_info['news_items'].append({
                    'content': para,
                    'dates': dates
                })
    
    def extract_management_info(self):
        """Extract management and leadership information"""
        leadership_pages = ['leadership', 'team', 'management']
        
        for page in leadership_pages:
            if page in self.data:
                content = self.data[page].get('content', '')
                
                # Look for executive names and titles
                executive_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+).*?(?:CEO|CFO|COO|President|Director|Manager|Vice President|VP)'
                executives = re.findall(executive_pattern, content, re.IGNORECASE)
                
                for exec_name in executives:
                    self.extracted_info['management_info'].append({
                        'name': exec_name,
                        'source_page': page
                    })
    
    def extract_contact_info(self):
        """Extract contact information"""
        if 'contact' in self.data:
            content = self.data['contact'].get('content', '')
            
            # Extract email addresses
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            
            # Extract phone numbers
            phones = re.findall(r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', content)
            
            # Extract addresses (simple pattern)
            address_pattern = r'\d+[^,\n]*(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd)[^,\n]*'
            addresses = re.findall(address_pattern, content, re.IGNORECASE)
            
            self.extracted_info['contact_info'] = {
                'emails': emails,
                'phones': phones,
                'addresses': addresses
            }
    
    def extract_key_metrics(self):
        """Extract key business metrics and numbers"""
        all_content = ""
        for page_data in self.data.values():
            if isinstance(page_data, dict):
                all_content += page_data.get('content', '') + "\n"
        
        # Look for financial metrics
        metrics = {}
        
        # Revenue patterns
        revenue_matches = re.findall(r'revenue[^$]*\$([0-9,]+(?:\.[0-9]+)?)\s*(?:million|billion)?', all_content, re.IGNORECASE)
        if revenue_matches:
            metrics['revenue'] = revenue_matches
        
        # Production numbers
        production_matches = re.findall(r'production[^0-9]*([0-9,]+(?:\.[0-9]+)?)\s*(?:tonnes|tons|ounces|pounds)', all_content, re.IGNORECASE)
        if production_matches:
            metrics['production'] = production_matches
        
        # Share price
        share_matches = re.findall(r'share price[^$]*\$([0-9]+(?:\.[0-9]+)?)', all_content, re.IGNORECASE)
        if share_matches:
            metrics['share_price'] = share_matches
        
        self.extracted_info['key_metrics'] = metrics
    
    def process_all(self):
        """Process all extraction methods"""
        print("Extracting news and project updates...")
        self.extract_news_and_updates()
        
        print("Extracting management information...")
        self.extract_management_info()
        
        print("Extracting contact information...")
        self.extract_contact_info()
        
        print("Extracting key metrics...")
        self.extract_key_metrics()
        
        return self.extracted_info
    
    def generate_report(self):
        """Generate a formatted report"""
        report = []
        report.append("MAGNA MINING - KEY INFORMATION EXTRACT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Financial Information
        if self.extracted_info['financial_info']:
            report.append("FINANCIAL INFORMATION:")
            report.append("-" * 25)
            for item in self.extracted_info['financial_info'][:5]:  # Top 5
                report.append(f"• {item['content'][:200]}...")
                if item['dates']:
                    report.append(f"  Dates: {', '.join(item['dates'])}")
                report.append("")
        
        # Project Updates
        if self.extracted_info['project_updates']:
            report.append("PROJECT UPDATES:")
            report.append("-" * 17)
            for item in self.extracted_info['project_updates'][:5]:  # Top 5
                report.append(f"• {item['content'][:200]}...")
                if item['dates']:
                    report.append(f"  Dates: {', '.join(item['dates'])}")
                report.append("")
        
        # News Items
        if self.extracted_info['news_items']:
            report.append("NEWS & ANNOUNCEMENTS:")
            report.append("-" * 22)
            for item in self.extracted_info['news_items'][:5]:  # Top 5
                report.append(f"• {item['content'][:200]}...")
                if item['dates']:
                    report.append(f"  Dates: {', '.join(item['dates'])}")
                report.append("")
        
        # Key Metrics
        if self.extracted_info['key_metrics']:
            report.append("KEY METRICS:")
            report.append("-" * 13)
            for metric, values in self.extracted_info['key_metrics'].items():
                report.append(f"• {metric.title()}: {', '.join(values)}")
            report.append("")
        
        # Management
        if self.extracted_info['management_info']:
            report.append("MANAGEMENT TEAM:")
            report.append("-" * 17)
            for person in self.extracted_info['management_info'][:10]:
                report.append(f"• {person['name']}")
            report.append("")
        
        # Contact Info
        if self.extracted_info['contact_info']:
            report.append("CONTACT INFORMATION:")
            report.append("-" * 20)
            contact = self.extracted_info['contact_info']
            if contact.get('emails'):
                report.append(f"Emails: {', '.join(contact['emails'])}")
            if contact.get('phones'):
                report.append(f"Phones: {', '.join(contact['phones'])}")
            if contact.get('addresses'):
                report.append(f"Address: {contact['addresses'][0] if contact['addresses'] else 'N/A'}")
        
        return "\n".join(report)
    
    def save_results(self, output_file=None):
        """Save extracted information to JSON and text report"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_output = f"magna_extracted_data_{timestamp}.json"
            report_output = f"magna_key_info_report_{timestamp}.txt"
        else:
            json_output = f"{output_file}.json"
            report_output = f"{output_file}_report.txt"
        
        # Save JSON data
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_info, f, indent=2, ensure_ascii=False)
        
        # Save text report
        report = self.generate_report()
        with open(report_output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return json_output, report_output

def main():
    # Find the most recent JSON file
    json_files = list(Path('.').glob('magna_mining_data_*.json'))
    if not json_files:
        print("No Magna Mining JSON files found!")
        return
    
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"Processing: {latest_file}")
    
    # Extract information
    extractor = MagnaDataExtractor(latest_file)
    extracted_data = extractor.process_all()
    
    # Save results
    json_file, report_file = extractor.save_results()
    
    print(f"\nExtraction completed!")
    print(f"JSON data saved to: {json_file}")
    print(f"Report saved to: {report_file}")
    
    # Display summary
    print(f"\nSUMMARY:")
    print(f"Financial items: {len(extracted_data['financial_info'])}")
    print(f"Project updates: {len(extracted_data['project_updates'])}")
    print(f"News items: {len(extracted_data['news_items'])}")
    print(f"Management entries: {len(extracted_data['management_info'])}")
    print(f"Key metrics found: {len(extracted_data['key_metrics'])}")
    
    # Show quick preview
    print(f"\nQUICK PREVIEW:")
    print("-" * 30)
    report = extractor.generate_report()
    preview_lines = report.split('\n')[:20]  # First 20 lines
    print('\n'.join(preview_lines))
    if len(report.split('\n')) > 20:
        print("... (see full report in output file)")

if __name__ == "__main__":
    main()