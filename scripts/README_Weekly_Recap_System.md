# 📊 Weekly Recap System - User Guide

## 🎯 Overview

The Weekly Recap System automatically generates comprehensive reports about your mining intelligence system's performance, development progress, and business metrics. This system provides standardized, data-driven weekly summaries that track all aspects of your operation.

## 🏗️ System Components

### 📋 Template System
- **Location**: `templates/weekly_recap_template.md`
- **Purpose**: Standardized format for all weekly reports
- **Features**: 15+ sections covering technical, business, and operational metrics

### ⚙️ Configuration
- **Location**: `config/weekly_recap_config.json`
- **Purpose**: Customizable reporting parameters and data sources
- **Features**: Database paths, metrics thresholds, formatting options

### 📊 Data Collector
- **Location**: `scripts/recap_data_collector.py`
- **Purpose**: Collects metrics from git, databases, files, and system logs
- **Features**: Automated data gathering and analysis

### 🤖 Report Generator
- **Location**: `scripts/generate_weekly_recap.py`
- **Purpose**: Main automation script that generates complete reports
- **Features**: Template population, data analysis, and report output

## 🚀 Quick Start Guide

### 1. Generate This Week's Recap

```bash
# Basic usage - generates recap for last 7 days
cd "/Projects/Resource Capital"
source venv/bin/activate
python scripts/generate_weekly_recap.py

# Custom date range
python scripts/generate_weekly_recap.py --start-date 2025-08-01 --end-date 2025-08-03

# Custom output location
python scripts/generate_weekly_recap.py --output "custom_reports/my_report.md"
```

### 2. Collect Raw Data Only

```bash
# Just collect data without generating report
python scripts/recap_data_collector.py --output weekly_data.json --days 7
```

### 3. Use Custom Configuration

```bash
# Use custom config file
python scripts/generate_weekly_recap.py --config my_custom_config.json
```

## 📋 Command Line Options

### Weekly Recap Generator

```bash
python scripts/generate_weekly_recap.py [OPTIONS]

Options:
  --config PATH           Path to configuration file (default: config/weekly_recap_config.json)
  --template PATH         Path to template file (default: templates/weekly_recap_template.md)
  --output PATH           Output file path (auto-generated if not specified)
  --days INTEGER          Number of days to include (default: 7)
  --start-date YYYY-MM-DD Start date for report period
  --end-date YYYY-MM-DD   End date for report period
  --help                  Show help message
```

### Data Collector

```bash
python scripts/recap_data_collector.py [OPTIONS]

Options:
  --config PATH           Path to configuration file
  --output PATH           Output JSON file path (default: weekly_data.json)
  --days INTEGER          Number of days to look back (default: 7)
  --help                  Show help message
```

## 📊 Report Sections Explained

### 🚀 Executive Summary
- High-level overview of the week's activities
- Key performance indicators and metrics
- Major accomplishments and developments

### 💻 Technical Progress
- **Development Achievements**: Git commits and feature implementations
- **Infrastructure Updates**: System improvements and optimizations
- **Testing & QA**: Test coverage and quality assurance activities

### 📈 Business Intelligence
- **Market Intelligence**: Key market events and analysis
- **Company Events**: Notable corporate developments
- **Commodity Performance**: Price movements and trends
- **Trending Topics**: Most important themes of the week

### 🛠️ System Health
- **Database Metrics**: Record counts, growth, and storage
- **Web Scraping Performance**: Success rates and response times
- **API Integration Status**: External service connectivity

### 📂 Data Processing
- **Data Ingestion**: Volume of data processed
- **Quality Metrics**: Accuracy and validation statistics
- **Pipeline Status**: ETL operations and efficiency

### 🎯 Key Accomplishments
- **Major Milestones**: Significant achievements
- **Performance Improvements**: Optimization results
- **Notable Events**: Important developments

### ⚠️ Issues & Challenges
- **Technical Issues**: Problems encountered and solutions
- **Data Quality Concerns**: Accuracy and completeness issues
- **External Dependencies**: Third-party service impacts

### 🔮 Next Week's Priorities
- **Development Focus**: Planned feature development
- **System Improvements**: Infrastructure enhancements
- **Monitoring & Analysis**: Surveillance priorities

## ⚙️ Customization Guide

### 📝 Modify the Template

Edit `templates/weekly_recap_template.md` to customize:
- Section order and content
- Formatting and styling
- Additional metrics or KPIs
- Company-specific information

### 🔧 Configure Data Sources

Edit `config/weekly_recap_config.json` to customize:
- Database paths and connection strings
- Metrics thresholds and targets
- Report formatting preferences
- Automation schedules

### 📊 Add Custom Metrics

To add new metrics to reports:

1. **Add data collection** in `recap_data_collector.py`:
```python
def _collect_custom_metrics(self):
    # Your custom data collection logic
    custom_data = {"metric_name": "metric_value"}
    self.data["custom"] = custom_data
```

2. **Add template placeholders** in `weekly_recap_template.md`:
```markdown
### Custom Section
{custom_metric_value}
```

3. **Add template population** in `generate_weekly_recap.py`:
```python
replacements["custom_metric_value"] = self._generate_custom_metric(data)
```

## 🔄 Automation Setup

### Scheduled Generation

Add to crontab for automatic weekly reports:

```bash
# Generate report every Saturday at 9 AM
0 9 * * 6 cd /Projects/Resource\ Capital && source venv/bin/activate && python scripts/generate_weekly_recap.py
```

### Integration with CI/CD

Add to your deployment pipeline:

```yaml
# .github/workflows/weekly-report.yml
name: Weekly Report
on:
  schedule:
    - cron: '0 9 * * 6'  # Every Saturday at 9 AM
jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate Weekly Report
        run: |
          python scripts/generate_weekly_recap.py
          git add weekly_reports/
          git commit -m "Add weekly report for $(date +%Y-%m-%d)"
          git push
```

## 📋 Examples

### Example 1: Monthly Summary
```bash
# Generate report for entire month
python scripts/generate_weekly_recap.py \
  --start-date 2025-08-01 \
  --end-date 2025-08-31 \
  --output "monthly_reports/august_2025.md"
```

### Example 2: Custom Project Report
```bash
# Create report for specific project milestone
python scripts/generate_weekly_recap.py \
  --start-date 2025-08-01 \
  --end-date 2025-08-03 \
  --config "config/project_milestone_config.json" \
  --template "templates/milestone_template.md" \
  --output "project_reports/testing_infrastructure_complete.md"
```

### Example 3: Data Collection Only
```bash
# Collect data for external analysis
python scripts/recap_data_collector.py \
  --days 30 \
  --output "analytics/monthly_data_$(date +%Y%m).json"
```

## 🎯 Best Practices

### 📅 Regular Schedule
- **Weekly Generation**: Every Saturday morning for previous week
- **Monthly Summaries**: First Saturday of each month for previous month
- **Milestone Reports**: After major feature completions or releases

### 📊 Data Quality
- **Verify Git Activity**: Ensure all commits are properly categorized
- **Database Cleanup**: Remove test data before generating reports
- **Performance Monitoring**: Include actual metrics from monitoring systems

### 📝 Report Review
- **Executive Summary**: Keep concise and action-oriented
- **Technical Details**: Include enough detail for team understanding
- **Action Items**: Clearly identify next week's priorities

### 🔄 Continuous Improvement
- **Template Evolution**: Regularly update template based on stakeholder feedback
- **Metric Enhancement**: Add new KPIs as business needs evolve
- **Automation Refinement**: Improve data collection accuracy over time

## ❓ Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'recap_data_collector'"
**Solution**: Ensure you're running from the project root directory

**Issue**: "Error: Could not load template"
**Solution**: Verify template file exists at `templates/weekly_recap_template.md`

**Issue**: "Warning: Could not collect git data"
**Solution**: Ensure you're in a git repository with commit history

**Issue**: Database connection errors
**Solution**: Verify database paths in config file are correct

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Add debug information
python scripts/generate_weekly_recap.py --verbose
```

## 🎉 Success Metrics

The weekly recap system is working well when you see:

- ✅ **Consistent Reports**: Generated automatically each week
- ✅ **Accurate Data**: Metrics reflect actual system performance
- ✅ **Actionable Insights**: Reports drive decision-making
- ✅ **Time Savings**: Manual reporting effort reduced by 90%+
- ✅ **Stakeholder Satisfaction**: Team finds reports valuable

---

**💡 Pro Tip**: Start with the default configuration and gradually customize based on your specific needs. The system is designed to be immediately useful out-of-the-box while being highly customizable for advanced use cases.

**📞 Support**: For questions or feature requests, review the generated reports and modify the templates/configuration files as needed.