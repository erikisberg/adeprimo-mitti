#!/bin/bash
# Setup script for Content Monitor

echo "Setting up Content Monitor..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/history
mkdir -p data/analysis

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    cat > .env << EOF
# API Keys
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ASSISTANT_ID=your_assistant_id_here

# Configuration
SIMILARITY_THRESHOLD=0.9
EOF
    echo ".env file created. Please edit it with your API keys."
fi

# Make run script executable
chmod +x run.sh

# Run setup test
echo "Running setup test..."
python setup_test.py

echo ""
echo "Setup completed!"
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run the monitor with: ./run.sh"

# Deactivate virtual environment
deactivate