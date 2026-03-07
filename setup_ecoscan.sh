#!/bin/bash

# --- EcoScan Initialize Script ---

echo "🌿 EcoScan Project Setup"
echo "========================="

# 1. Setup Backend
echo ">>> Setting up Python Backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✅ Created backend/.env (Update with your Gemini API Key!)"
fi
cd ..

# 2. Setup Extension
echo ">>> Setting up Chrome Extension..."
cd extension
if command -v npm &> /dev/null
then
    npm install
    npm run build
    echo "  ✅ Extension built successfully. Load the 'extension/dist' folder in Chrome."
else
    echo "  ⚠️  Node.js/npm not detected. Please install Node.js to build the extension."
fi
cd ..

echo "========================="
echo "🚀 Setup complete! Refer to README.md for more details."
