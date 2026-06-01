#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setting up database..."
python -c "from database import create_tables; create_tables()"

echo "Starting PM Pilot..."
streamlit run app.py
