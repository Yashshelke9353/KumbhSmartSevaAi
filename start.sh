#!/bin/bash

# Kumbh Smart Seva - Startup Script
# Initializes database and starts the Flask application

echo ""
echo "🏛️  Kumbh Smart Seva Platform - Startup"
echo "=============================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✓ pip found"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# Install/upgrade dependencies
echo "📚 Installing/upgrading dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✓ Dependencies installed"
echo ""

# Initialize database
echo "🗄️  Checking database..."
python3 << EOF
from database.db_manager import DatabaseManager
db = DatabaseManager()
db.init_db()
print("✓ Database ready")
EOF

# Optionally load sample data
echo ""
read -p "Load sample test data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 Loading sample data..."
    python3 init_sample_data.py
    echo ""
fi

# Start the application
echo "🚀 Starting Kumbh Smart Seva..."
echo "=============================================="
echo ""
echo "📍 Access the application at:"
echo "   🌐 Homepage:  http://localhost:5000"
echo "   🔐 Admin:     http://localhost:5000/admin/login"
echo "   📝 Login:     http://localhost:5000/login"
echo ""
echo "Test Credentials:"
echo "   Visitor - rajesh@example.com / password123"
echo "   Admin   - admin@kumbh.com / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

python3 app.py
