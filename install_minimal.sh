#!/bin/bash
# Quick install script for Bluehost - installs only essential packages
# Run this if the full requirements.txt fails due to memory issues

echo "🎰 Installing minimal dependencies for Flask web app..."

# Install core packages one by one to avoid memory issues
pip install --user flask>=2.3.0
pip install --user python-dotenv>=1.0.0
pip install --user mysql-connector-python>=8.0.0
pip install --user requests>=2.31.0
pip install --user cryptography>=41.0.0
pip install --user python-dateutil>=2.8.0

echo "✅ Minimal installation complete!"
echo "🚀 You can now run: python3 start_bluehost.py"
