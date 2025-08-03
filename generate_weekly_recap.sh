#!/bin/bash

# Resource Capital Mining Intelligence - Weekly Recap Generator
# Quick execution script for generating weekly reports

echo "📊 Resource Capital Mining Intelligence - Weekly Recap Generator"
echo "=============================================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ Virtual environment not found. Please ensure 'venv' directory exists."
    exit 1
fi

# Check if required files exist
if [ ! -f "scripts/generate_weekly_recap.py" ]; then
    echo "❌ Error: generate_weekly_recap.py not found in scripts directory"
    exit 1
fi

if [ ! -f "templates/weekly_recap_template.md" ]; then
    echo "❌ Error: weekly_recap_template.md not found in templates directory"
    exit 1
fi

# Parse command line arguments
DAYS=7
OUTPUT=""
START_DATE=""
END_DATE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --days)
            DAYS="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --start-date)
            START_DATE="$2"
            shift 2
            ;;
        --end-date)
            END_DATE="$2"
            shift 2
            ;;
        --help)
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --days NUMBER       Number of days to include (default: 7)"
            echo "  --output PATH       Output file path (auto-generated if not specified)"
            echo "  --start-date DATE   Start date (YYYY-MM-DD)"
            echo "  --end-date DATE     End date (YYYY-MM-DD)"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Generate weekly recap for last 7 days"
            echo "  $0 --days 14                         # Generate recap for last 14 days"
            echo "  $0 --start-date 2025-08-01 --end-date 2025-08-03  # Custom date range"
            echo "  $0 --output my_report.md             # Custom output file"
            echo ""
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python scripts/generate_weekly_recap.py"

if [ ! -z "$DAYS" ] && [ -z "$START_DATE" ] && [ -z "$END_DATE" ]; then
    CMD="$CMD --days $DAYS"
fi

if [ ! -z "$START_DATE" ]; then
    CMD="$CMD --start-date $START_DATE"
fi

if [ ! -z "$END_DATE" ]; then
    CMD="$CMD --end-date $END_DATE"
fi

if [ ! -z "$OUTPUT" ]; then
    CMD="$CMD --output $OUTPUT"
fi

echo "🚀 Generating weekly recap..."
echo "Command: $CMD"
echo ""

# Execute the command
eval $CMD

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Weekly recap generation completed successfully!"
    echo ""
    echo "📁 Output location: Check the weekly_reports/ directory"
    echo "📋 For more options, run: $0 --help"
    echo "📚 Full documentation: scripts/README_Weekly_Recap_System.md"
else
    echo ""
    echo "❌ Error: Weekly recap generation failed"
    echo "💡 Try running with --help for usage information"
    exit 1
fi