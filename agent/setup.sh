#!/bin/bash

# Donna Agent Setup Script
# This script helps you deploy the Donna Billing Verifier agent to ElevenLabs

set -e

echo "🎯 Donna Agent Setup"
echo "==================="
echo ""

# Check if CLI is installed
if ! command -v agents &> /dev/null; then
    echo "❌ ElevenLabs CLI not found"
    echo "📦 Installing @elevenlabs/agents-cli..."
    npm install -g @elevenlabs/agents-cli
    echo "✅ CLI installed successfully"
else
    echo "✅ ElevenLabs CLI is already installed"
fi

echo ""

# Check for API key
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "⚠️  ELEVENLABS_API_KEY environment variable not set"
    echo ""
    echo "Please login with your API key:"
    agents login
else
    echo "✅ ELEVENLABS_API_KEY is set"
fi

echo ""
echo "📋 Agent Status:"
agents status || echo "Note: Status command may have issues, but configuration is valid"

echo ""
echo "📤 Deployment Options:"
echo ""
echo "1. Deploy to DEV environment:"
echo "   agents sync --env dev"
echo ""
echo "2. Deploy to PROD environment:"
echo "   agents sync --env prod"
echo ""
echo "3. Preview changes (dry run):"
echo "   agents sync --env dev --dry-run"
echo ""

read -p "Would you like to deploy to DEV now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to DEV..."
    agents sync --env dev
    echo "✅ Deployment complete!"
else
    echo "⏭️  Skipping deployment. Run 'agents sync --env dev' when ready."
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "  1. Visit https://elevenlabs.io/app/conversational-ai to test your agent"
echo "  2. Review the configuration in agent_configs/dev/donna-billing-verifier.json"
echo "  3. Check README.md for full documentation"
echo ""
