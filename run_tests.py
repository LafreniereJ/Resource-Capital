#!/usr/bin/env python3
"""
Comprehensive Test Runner for Mining Intelligence System
Executes all test suites with proper reporting and analysis
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
import sqlite3


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n✅ Success: {success}")
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 5 minutes")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False, "", str(e)


def check_dependencies():
    """Check that all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest', 'pytest-cov', 'pytest-asyncio', 'pytest-mock',
        'yfinance', 'feedparser', 'requests', 'pandas', 
        'beautifulsoup4', 'selenium', 'playwright'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements-dev.txt")
        return False
    
    print("✅ All dependencies satisfied")
    return True


def run_test_suite(test_type, test_path=None, extra_args=None):
    """Run a specific test suite"""
    base_command = "python -m pytest"
    
    # Build command based on test type
    if test_type == "unit":
        command = f"{base_command} tests/unit/ -m unit"
    elif test_type == "integration":
        command = f"{base_command} tests/integration/ -m integration"
    elif test_type == "data_quality":
        command = f"{base_command} tests/data_quality/ -m data_quality"
    elif test_type == "scrapers":
        command = f"{base_command} tests/scrapers/ -m scraper"
    elif test_type == "api":
        command = f"{base_command} tests/integration/test_api_integrations.py -m api"
    elif test_type == "performance":
        command = f"{base_command} tests/performance/ -m performance"
    elif test_type == "all":
        command = f"{base_command} tests/"
    elif test_type == "fast":
        command = f"{base_command} tests/ -m 'not slow and not requires_network'"
    elif test_type == "network":
        command = f"{base_command} tests/ -m requires_network"
    elif test_path:
        command = f"{base_command} {test_path}"
    else:
        command = f"{base_command} tests/"
    
    # Add coverage reporting
    command += " --cov=src --cov-report=term-missing --cov-report=html"
    
    # Add extra arguments
    if extra_args:
        command += f" {extra_args}"
    
    return run_command(command, f"Running {test_type} tests")


def run_code_quality_checks():
    """Run code quality and linting checks"""
    checks = [
        ("python -m black --check src/ tests/", "Code formatting check (black)"),
        ("python -m isort --check-only src/ tests/", "Import sorting check (isort)"),
        ("python -m flake8 src/ tests/", "Code linting (flake8)"),
        ("python -m mypy src/", "Type checking (mypy)")
    ]
    
    results = {}
    
    for command, description in checks:
        success, stdout, stderr = run_command(command, description)
        results[description] = success
    
    return results


def generate_test_report(test_results, coverage_data=None):
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"test_report_{timestamp}.json"
    
    report = {
        'timestamp': timestamp,
        'test_results': test_results,
        'coverage': coverage_data,
        'summary': {
            'total_test_suites': len(test_results),
            'passed_suites': sum(1 for result in test_results.values() if result['success']),
            'failed_suites': sum(1 for result in test_results.values() if not result['success'])
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report_path


def create_test_database():
    """Create test database with sample data"""
    db_path = "test_mining_intelligence.db"
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY,
            symbol TEXT UNIQUE,
            name TEXT,
            market_cap REAL,
            exchange TEXT,
            sector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE intelligence_data (
            id INTEGER PRIMARY KEY,
            headline TEXT,
            summary TEXT,
            url TEXT,
            source TEXT,
            published TIMESTAMP,
            priority_score REAL,
            event_type TEXT,
            impact_level TEXT,
            canadian_relevance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data
    sample_companies = [
        ('AEM.TO', 'Agnico Eagle Mines Limited', 25000000000, 'TSX', 'Gold'),
        ('FM.TO', 'First Quantum Minerals Ltd.', 8500000000, 'TSX', 'Copper'),
        ('HBM.TO', 'Hudbay Minerals Inc.', 2100000000, 'TSX', 'Copper'),
        ('LUN.TO', 'Lundin Mining Corporation', 7800000000, 'TSX', 'Copper'),
        ('GOLD.TO', 'Barrick Gold Corporation', 35000000000, 'TSX', 'Gold')
    ]
    
    cursor.executemany(
        'INSERT INTO companies (symbol, name, market_cap, exchange, sector) VALUES (?, ?, ?, ?, ?)',
        sample_companies
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created test database: {db_path}")
    return db_path


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Mining Intelligence System Test Runner")
    parser.add_argument('--type', choices=['unit', 'integration', 'data_quality', 'scrapers', 'api', 'performance', 'all', 'fast', 'network'], 
                       default='fast', help='Type of tests to run')
    parser.add_argument('--path', help='Specific test file or directory to run')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency check')
    parser.add_argument('--skip-quality', action='store_true', help='Skip code quality checks')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage-threshold', type=int, default=80, help='Coverage threshold percentage')
    parser.add_argument('--extra-args', help='Extra arguments to pass to pytest')
    
    args = parser.parse_args()
    
    print("🧪 Mining Intelligence System - Comprehensive Testing")
    print("=" * 80)
    print(f"Test Type: {args.type}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check dependencies
    if not args.skip_deps:
        if not check_dependencies():
            sys.exit(1)
    
    # Create test database
    test_db = create_test_database()
    
    # Set environment variables for testing
    os.environ['TESTING'] = '1'
    os.environ['TEST_DATABASE_PATH'] = test_db
    
    test_results = {}
    
    try:
        # Run tests
        if args.type == "all":
            # Run all test suites
            test_suites = ['unit', 'integration', 'data_quality', 'scrapers', 'api']
            for suite in test_suites:
                success, stdout, stderr = run_test_suite(suite, extra_args=args.extra_args)
                test_results[suite] = {
                    'success': success,
                    'stdout': stdout,
                    'stderr': stderr
                }
        else:
            # Run specific test suite
            success, stdout, stderr = run_test_suite(args.type, args.path, args.extra_args)
            test_results[args.type] = {
                'success': success,
                'stdout': stdout,
                'stderr': stderr
            }
        
        # Run code quality checks
        if not args.skip_quality:
            quality_results = run_code_quality_checks()
            test_results['code_quality'] = quality_results
        
        # Generate report
        report_path = generate_test_report(test_results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_suites = len(test_results)
        passed_suites = sum(1 for result in test_results.values() 
                           if (isinstance(result, dict) and result.get('success')) or 
                              (isinstance(result, bool) and result))
        
        print(f"Total Test Suites: {total_suites}")
        print(f"Passed: {passed_suites}")
        print(f"Failed: {total_suites - passed_suites}")
        print(f"Success Rate: {passed_suites/total_suites*100:.1f}%")
        
        for suite_name, result in test_results.items():
            if isinstance(result, dict):
                status = "✅ PASS" if result.get('success') else "❌ FAIL"
            else:
                status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {suite_name:20s}: {status}")
        
        print(f"\nTest report saved to: {report_path}")
        
        # Check coverage
        if os.path.exists('htmlcov/index.html'):
            print("Coverage report available at: htmlcov/index.html")
        
        # Exit with appropriate code
        if passed_suites == total_suites:
            print("\n🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print(f"\n⚠️ {total_suites - passed_suites} TEST SUITE(S) FAILED")
            sys.exit(1)
    
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)
        
        # Remove environment variables
        os.environ.pop('TESTING', None)
        os.environ.pop('TEST_DATABASE_PATH', None)


if __name__ == "__main__":
    main()