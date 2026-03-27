#!/bin/bash
# PhysiqAI Day 1 Setup Script
# Automates all setup steps for Reddit scraper

echo "🚀 PhysiqAI Day 1 Setup"
echo "======================="
echo ""

# Check if we're in the right directory
if [ ! -f "EXECUTION_PLAN.md" ]; then
    echo "❌ Error: Please run this from ~/Documents/physiqai/"
    exit 1
fi

echo "📁 Creating folder structure..."
mkdir -p data/reddit_scrapes/images
mkdir -p data/reddit_scrapes/metadata
mkdir -p scripts
mkdir -p logs

echo "✅ Folders created"
echo ""

echo "📦 Installing Python dependencies..."
pip3 install praw pillow requests --quiet

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "⚠️  Some dependencies failed to install. Please run manually:"
    echo "   pip3 install praw pillow requests"
fi

echo ""
echo "🔑 Checking .env file..."

if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << 'EOF'
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=PhysiqAI:v1.0 (by /u/your_reddit_username)

# Google AI (already configured)
GOOGLE_AI_KEY=AIzaSyDqrsDqtITlURVHhVFbwBan2gESidwvFEY

# Replicate (already configured)
REPLICATE_API_TOKEN=r8_...
EOF
    echo ""
    echo "📝 .env template created!"
    echo ""
    echo "⚠️  ACTION REQUIRED:"
    echo "1. Go to https://www.reddit.com/prefs/apps"
    echo "2. Click 'Create App'"
    echo "3. Choose 'script' type"
    echo "4. Copy your client_id and client_secret"
    echo "5. Edit .env file with your credentials:"
    echo "   nano .env"
    echo ""
    exit 1
else
    echo "✅ .env file exists"
fi

echo ""
echo "🔍 Verifying Reddit API credentials..."

# Check if credentials are filled in
if grep -q "your_client_id_here" .env; then
    echo "⚠️  Reddit credentials not configured yet!"
    echo ""
    echo "Please edit .env file:"
    echo "   nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Credentials configured"
echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next step: Run the scraper"
echo "   python3 scripts/scrape_progresspics.py"
echo ""
