#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Auto-Certification Setup ==="

# Install dependencies
pip install -r requirements.txt -q

# Create sample data and copy fonts
python create_sample.py

echo ""
echo "=== Starting Server ==="
echo "Open http://localhost:5000 in your browser"
echo ""
python app.py
