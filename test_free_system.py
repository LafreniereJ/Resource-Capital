#!/usr/bin/env python3
"""
Test script to verify the mining intelligence system works with FREE tools only
"""

import sys
import os
import asyncio
from datetime import datetime

def test_free_dependencies():
    """Test that all required free dependencies are available"""
    
    print("🔍 Testing FREE Dependencies...")
    
    # Test core dependencies
    try:
        import yfinance
        print("✅ yfinance - Available")
    except ImportError:
        print("❌ yfinance - Missing")
        return False
    
    try:
        import pandas
        print("✅ pandas - Available")
    except ImportError:
        print("❌ pandas - Missing")
        return False
    
    try:
        import requests
        print("✅ requests - Available")
    except ImportError:
        print("❌ requests - Missing")
        return False
    
    try:
        import feedparser
        print("✅ feedparser - Available")
    except ImportError:
        print("❌ feedparser - Missing")
        return False
    
    # Test web scraping dependencies
    try:
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4 - Available")
    except ImportError:
        print("❌ beautifulsoup4 - Missing")
        return False
    
    try:
        from playwright.async_api import async_playwright
        print("✅ playwright - Available")
    except ImportError:
        print("❌ playwright - Missing")
        return False
    
    try:
        from selenium import webdriver
        print("✅ selenium - Available")
    except ImportError:
        print("❌ selenium - Missing")
        return False
    
    # Test that crawl4ai is NOT available (should fail)
    try:
        import crawl4ai
        print("❌ crawl4ai - Should NOT be available (paid API)")
        return False
    except ImportError:
        print("✅ crawl4ai - Correctly NOT available (free system)")
    
    return True

def test_config_import():
    """Test that the configuration system works"""
    
    print("\n🔧 Testing Configuration...")
    
    try:
        sys.path.append('src')
        from core.config import Config
        print("✅ Config import - Successful")
        
        # Test configuration validation
        if Config.validate_config():
            print("✅ Config validation - Passed")
        else:
            print("❌ Config validation - Failed")
            return False
            
    except Exception as e:
        print(f"❌ Config import - Failed: {str(e)}")
        return False
    
    return True

async def test_basic_functionality():
    """Test basic system functionality"""
    
    print("\n🚀 Testing Basic Functionality...")
    
    try:
        # Test yfinance
        import yfinance as yf
        ticker = yf.Ticker("AEM.TO")
        info = ticker.info
        if info:
            print("✅ yfinance data fetch - Successful")
        else:
            print("❌ yfinance data fetch - Failed")
            return False
            
    except Exception as e:
        print(f"❌ yfinance test - Failed: {str(e)}")
        return False
    
    try:
        # Test requests
        import requests
        response = requests.get("https://www.google.com", timeout=10)
        if response.status_code == 200:
            print("✅ requests test - Successful")
        else:
            print("❌ requests test - Failed")
            return False
            
    except Exception as e:
        print(f"❌ requests test - Failed: {str(e)}")
        return False
    
    return True

def test_data_extraction():
    """Test the updated data extraction without crawl4ai"""
    
    print("\n📊 Testing Data Extraction...")
    
    try:
        sys.path.append('src')
        from processors.enhanced_data_extractor import EnhancedDataExtractor
        
        extractor = EnhancedDataExtractor()
        print("✅ EnhancedDataExtractor - Created successfully")
        
        # Test pattern setup
        patterns = extractor._setup_extraction_patterns()
        if patterns and "financial_metrics" in patterns:
            print("✅ Pattern extraction - Setup successful")
        else:
            print("❌ Pattern extraction - Setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Data extraction test - Failed: {str(e)}")
        return False
    
    return True

async def main():
    """Run all tests"""
    
    print("🧪 FREE Mining Intelligence System Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_free_dependencies),
        ("Configuration", test_config_import),
        ("Basic Functionality", test_basic_functionality),
        ("Data Extraction", test_data_extraction)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for FREE operation.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 