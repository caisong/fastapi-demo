#!/bin/bash
echo "Installing FastAPI dependencies..."
pip install -r requirements.txt

echo ""
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "Starting development server..."
echo "The server will be available at: http://127.0.0.1:8000"
echo "API documentation at: http://127.0.0.1:8000/docs"
echo ""
python scripts/dev.py