# Mining Intelligence System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive mining industry intelligence and data collection system for Canadian mining companies listed on TSX and TSXV exchanges.

## 🎯 Features

### Core Intelligence Capabilities
- **Real-time Market Data**: Integration with yfinance for stock performance tracking
- **News Aggregation**: RSS feed monitoring and financial news collection
- **Web Scraping**: Multi-source data extraction using Playwright and Selenium
- **AI-Powered Analysis**: LLM integration for content analysis and insights
- **Database Management**: SQLite-based data storage and retrieval

### Data Sources
- TSX and TSXV listed companies
- Financial market data
- News feeds and press releases
- Company investor relations pages
- Regulatory filings

### Analysis Modules
- **Business Intelligence**: Comprehensive company analysis
- **M&A Activity Scanning**: Merger and acquisition monitoring
- **Operational Updates**: Mining operations and production data
- **Market Analysis**: Stock performance and trading patterns

## 🏗️ Architecture

```
src/
├── core/                   # Core system components
│   ├── config.py          # Configuration management
│   ├── complete_mining_intelligence_system.py
│   └── comprehensive_mining_intelligence.py
├── scrapers/               # Web scraping modules
│   ├── playwright_scrapers.py
│   ├── selenium_scrapers.py
│   └── enhanced_mining_scraper.py
├── processors/             # Data processing and extraction
│   ├── enhanced_data_extractor.py
│   ├── pattern_based_extractor.py
│   └── comprehensive_data_aggregator.py
├── intelligence/           # Business intelligence modules
│   ├── comprehensive_business_intel.py
│   ├── mining_ma_scanner.py
│   └── real_numerical_intel.py
├── reports/               # Report generation
│   ├── daily_tsx_mining_report.py
│   └── quick_daily_report.py
└── tests/                 # Test suite
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- API keys for OpenAI or Anthropic (optional, for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/mining-intelligence-system.git
   cd mining-intelligence-system
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv mining_env
   source mining_env/bin/activate  # On Windows: mining_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

### Basic Usage

1. **Run configuration test**
   ```bash
   python src/core/config.py
   ```

2. **Generate a daily report**
   ```bash
   python src/reports/daily_tsx_mining_report.py
   ```

3. **Start complete intelligence system**
   ```bash
   python src/core/complete_mining_intelligence_system.py
   ```

## 📊 Data Management

### Database Structure
The system uses SQLite databases to store:
- Company information and metadata
- Market data and financial metrics
- News articles and analysis
- Scraping results and processed data

### Data Flow
1. **Collection**: Web scrapers gather data from multiple sources
2. **Processing**: Data processors clean and structure information
3. **Analysis**: Intelligence modules generate insights
4. **Storage**: Results stored in databases and exported as reports
5. **Reporting**: Automated report generation with customizable formats

## 🔧 Configuration

### Core Settings (`src/core/config.py`)
- **API Keys**: Configure OpenAI/Anthropic for AI features
- **Crawling**: Delay, timeout, and retry settings
- **Content**: Word count and size limits
- **Scoring**: Relevance thresholds and content weights

### Customization
- Add new data sources in `scrapers/`
- Create custom analysis in `intelligence/`
- Modify report formats in `reports/`

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest tests/`
5. Submit a pull request

### Coding Standards
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include type hints where appropriate
- Write tests for new functionality

## 📈 Usage Examples

### Basic Company Analysis
```python
from src.core.complete_mining_intelligence_system import CompleteMiningIntelligence

# Initialize for a specific company
intel = CompleteMiningIntelligence(symbol="AEM.TO", company_name="Agnico Eagle Mines")

# Run comprehensive analysis
results = await intel.run_complete_analysis()
print(results)
```

### Custom Data Extraction
```python
from src.processors.enhanced_data_extractor import EnhancedDataExtractor

extractor = EnhancedDataExtractor()
data = await extractor.extract_company_data("https://company-website.com")
```

### Generate Reports
```python
from src.reports.daily_tsx_mining_report import DailyTSXMiningReport

report = DailyTSXMiningReport()
report.generate_report(output_format="pdf")
```

## 📁 Project Structure

### Data Organization
```
data/
├── raw/                   # Raw data files
├── processed/             # Cleaned and processed data
└── databases/             # SQLite database files
```

### Environment Management
```
environments/
├── crawl_env/            # Web crawling environment
└── mining_env/           # Main development environment
```

## 🔐 Security & Privacy

- **API Keys**: Never commit API keys to the repository
- **Data Privacy**: Comply with website terms of service and robots.txt
- **Rate Limiting**: Respectful crawling with appropriate delays
- **Data Retention**: Regular cleanup of temporary data

## 📋 Roadmap

### Current Features
- [x] Basic web scraping capabilities
- [x] Market data integration
- [x] Database storage system
- [x] Report generation
- [x] Canadian company filtering

### Planned Features
- [ ] Real-time data streaming
- [ ] Advanced ML-based analysis
- [ ] Interactive web dashboard
- [ ] API endpoint creation
- [ ] Docker containerization
- [ ] Cloud deployment options

## 🐛 Issues & Support

- **Bug Reports**: Use GitHub Issues with the "bug" label
- **Feature Requests**: Use GitHub Issues with the "enhancement" label
- **Questions**: Use GitHub Discussions for general questions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for market data
- [Playwright](https://playwright.dev/) for web automation
- [crawl4ai](https://github.com/unclecode/crawl4ai) for AI-powered crawling
- TSX Group for market data and company listings

## 📞 Contact

For questions or collaboration opportunities, please reach out through GitHub Issues or Discussions.

---

**Note**: This system is for educational and research purposes. Always comply with website terms of service and applicable regulations when collecting data.