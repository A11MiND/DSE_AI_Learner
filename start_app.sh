#!/bin/bash

echo "Starting DSE AI Learner Platform (Streamlit)..."

# Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Application..."
echo "Access the app at http://localhost:8501"

streamlit run app.py
