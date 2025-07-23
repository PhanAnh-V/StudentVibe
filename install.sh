#!/bin/bash
# Install Python dependencies for VibeCheck Flask app

echo "🚀 Installing Python dependencies for VibeCheck..."

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "✅ Python dependencies installed successfully!"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ All dependencies installed!"
echo "🎯 Ready to deploy VibeCheck Flask application!"
