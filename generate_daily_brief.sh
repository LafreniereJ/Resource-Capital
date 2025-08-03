#!/bin/bash

# Quick Daily Mining Brief Generator
# Simple script to generate today's mining sector brief for social media

echo "🏭 Canadian Mining Daily Brief Generator"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "scripts/generate_daily_brief.py" ]; then
    echo "❌ Error: Please run this script from the Resource Capital project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ Virtual environment not found. Using system Python."
fi

# Check if required files exist
if [ ! -f "scripts/generate_daily_brief.py" ]; then
    echo "❌ Error: generate_daily_brief.py not found in scripts directory"
    exit 1
fi

if [ ! -f "templates/daily_market_brief_template.md" ]; then
    echo "❌ Error: daily_market_brief_template.md not found in templates directory"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p reports/social

# Parse command line arguments
SHOW_PREVIEW=false
CUSTOM_OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --preview)
            SHOW_PREVIEW=true
            shift
            ;;
        --output)
            CUSTOM_OUTPUT="$2"
            shift 2
            ;;
        --help)
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --preview      Show brief preview after generation"
            echo "  --output PATH  Custom output file path"
            echo "  --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Generate today's brief"
            echo "  $0 --preview                 # Generate and show preview"
            echo "  $0 --output my_brief.md      # Custom output file"
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

# Generate the brief
echo "🚀 Generating daily mining brief..."
echo ""

# Build command
CMD="python scripts/generate_daily_brief.py"

if [ ! -z "$CUSTOM_OUTPUT" ]; then
    CMD="$CMD --output $CUSTOM_OUTPUT"
fi

if [ "$SHOW_PREVIEW" = true ]; then
    CMD="$CMD --test"
fi

# Execute the command
eval $CMD

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Daily brief generation completed successfully!"
    echo ""
    
    # Show additional info
    echo "📁 Output location: reports/social/"
    echo "📋 Latest briefs:"
    ls -la reports/social/ | tail -3
    
    # Show file content if preview requested and no custom output
    if [ "$SHOW_PREVIEW" = true ] && [ -z "$CUSTOM_OUTPUT" ]; then
        TODAY=$(date +%Y%m%d)
        BRIEF_FILE="reports/social/daily_brief_${TODAY}.md"
        
        if [ -f "$BRIEF_FILE" ]; then
            echo ""
            echo "📱 Brief ready for social media:"
            echo "================================"
            cat "$BRIEF_FILE"
            echo ""
            echo "================================"
            echo "📊 Character count: $(wc -c < "$BRIEF_FILE") characters"
            echo "📝 Word count: $(wc -w < "$BRIEF_FILE") words"
        fi
    fi
    
    echo ""
    echo "💡 Tips:"
    echo "   • Copy content to your social media platforms"
    echo "   • Customize hashtags if needed"
    echo "   • Schedule for 9 AM EST posting"
    echo "   • Set up automation: scripts/setup_daily_automation.sh"
    
else
    echo ""
    echo "❌ Error: Daily brief generation failed"
    echo "💡 Try running with --help for usage information"
    echo "🔍 Check that all dependencies are installed:"
    echo "   pip install -r requirements.txt"
    exit 1
fi