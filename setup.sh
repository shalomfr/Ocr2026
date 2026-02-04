#!/bin/bash

echo "=========================================="
echo "Hebrew OCR Training System - Setup"
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
echo "✓ Node.js found"

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL not found. Please install it manually."
else
    echo "✓ PostgreSQL found"
fi

echo ""
echo "Installing Backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created backend/.env - Please edit with your settings"
fi

cd ..

echo ""
echo "Installing Frontend..."
cd frontend

# Install dependencies
npm install

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created frontend/.env"
fi

cd ..

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your database and Cloudinary settings"
echo "2. Create PostgreSQL database: createdb hebrew_ocr"
echo "3. Start backend: cd backend && python app.py"
echo "4. Start frontend: cd frontend && npm run dev"
echo ""
echo "Backend will run on: http://localhost:5000"
echo "Frontend will run on: http://localhost:3000"
echo ""
