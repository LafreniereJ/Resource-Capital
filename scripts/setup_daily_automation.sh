#!/bin/bash

# Daily Mining Brief Automation Setup
# Sets up cron jobs for automated daily social media brief generation

echo "🏭 Resource Capital Mining Intelligence - Daily Brief Automation Setup"
echo "======================================================================"

# Check if we're in the right directory
if [ ! -f "scripts/generate_daily_brief.py" ]; then
    echo "❌ Error: Please run this script from the Resource Capital project root directory"
    exit 1
fi

# Get current directory
PROJECT_DIR=$(pwd)
VENV_PATH="$PROJECT_DIR/venv"
SCRIPT_PATH="$PROJECT_DIR/scripts/generate_daily_brief.py"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PATH"
    echo "Please create virtual environment first: python -m venv venv"
    exit 1
fi

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Daily brief script not found at $SCRIPT_PATH"
    exit 1
fi

echo "✅ Project directory: $PROJECT_DIR"
echo "✅ Virtual environment: $VENV_PATH"
echo "✅ Script path: $SCRIPT_PATH"

# Create wrapper script for cron execution
WRAPPER_SCRIPT="$PROJECT_DIR/scripts/daily_brief_cron.sh"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash

# Daily Brief Cron Wrapper Script
# This script is called by cron to generate daily mining briefs

# Set up environment
export PATH=/usr/bin:/bin:/usr/local/bin
cd "$PROJECT_DIR"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Generate timestamp for logging
TIMESTAMP=\$(date '+%Y-%m-%d %H:%M:%S')

# Generate daily brief with error handling
echo "[\$TIMESTAMP] Starting daily brief generation..." >> logs/daily_brief_cron.log

if python "$SCRIPT_PATH" >> logs/daily_brief_cron.log 2>&1; then
    echo "[\$TIMESTAMP] Daily brief generated successfully" >> logs/daily_brief_cron.log
else
    echo "[\$TIMESTAMP] ERROR: Daily brief generation failed" >> logs/daily_brief_cron.log
    exit 1
fi

# Optional: Post to social media APIs here
# Example: python scripts/post_to_social.py --file reports/social/daily_brief_\$(date +%Y%m%d).md

echo "[\$TIMESTAMP] Daily brief automation completed" >> logs/daily_brief_cron.log
EOF

# Make wrapper script executable
chmod +x "$WRAPPER_SCRIPT"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

echo "✅ Created cron wrapper script: $WRAPPER_SCRIPT"

# Generate cron entry
# 9 AM EST = 2 PM UTC (14:00 UTC) for Monday-Friday
CRON_ENTRY="0 14 * * 1-5 $WRAPPER_SCRIPT"

echo ""
echo "📅 CRON SETUP INSTRUCTIONS:"
echo "=============================="
echo ""
echo "To set up automated daily brief generation (Mon-Fri at 9 AM EST), run:"
echo ""
echo "1. Open your crontab:"
echo "   crontab -e"
echo ""
echo "2. Add this line:"
echo "   $CRON_ENTRY"
echo ""
echo "3. Save and exit"
echo ""
echo "Alternative: Run this command to add the cron job automatically:"
echo "   (crontab -l 2>/dev/null; echo \"$CRON_ENTRY\") | crontab -"
echo ""

# Offer to set up cron job automatically
read -p "Would you like to add the cron job automatically now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    if [ $? -eq 0 ]; then
        echo "✅ Cron job added successfully!"
        echo ""
        echo "📋 Current crontab entries:"
        crontab -l | grep -E "(daily_brief|$PROJECT_DIR)"
    else
        echo "❌ Failed to add cron job. Please add manually using the instructions above."
    fi
else
    echo "⏭️ Skipping automatic cron setup. Use the instructions above to set up manually."
fi

echo ""
echo "🔍 TESTING AND MONITORING:"
echo "=========================="
echo ""
echo "Test the automation manually:"
echo "  $WRAPPER_SCRIPT"
echo ""
echo "Monitor automation logs:"
echo "  tail -f logs/daily_brief_cron.log"
echo ""
echo "View generated briefs:"
echo "  ls -la reports/social/"
echo ""

# Test the wrapper script
echo "🧪 TESTING WRAPPER SCRIPT:"
echo "=========================="
echo ""
read -p "Would you like to test the wrapper script now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Running test..."
    
    if "$WRAPPER_SCRIPT"; then
        echo "✅ Test completed successfully!"
        echo ""
        echo "📄 Generated files:"
        ls -la reports/social/ | tail -5
        echo ""
        echo "📋 Log output:"
        tail -5 logs/daily_brief_cron.log
    else
        echo "❌ Test failed. Check logs for details:"
        echo "   tail logs/daily_brief_cron.log"
    fi
else
    echo "⏭️ Skipping test. You can run it manually later with: $WRAPPER_SCRIPT"
fi

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "Your daily mining brief automation is now configured to run:"
echo "• Monday-Friday at 9:00 AM EST (2:00 PM UTC)"
echo "• Reports saved to: reports/social/"
echo "• Logs saved to: logs/daily_brief_cron.log"
echo ""
echo "Next steps:"
echo "1. Monitor the first few automated runs"
echo "2. Customize the template if needed (templates/daily_market_brief_template.md)"
echo "3. Set up social media posting integration if desired"
echo "4. Configure Saturday weekly recap and Sunday outlook reports"
echo ""