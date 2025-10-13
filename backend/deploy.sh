#!/bin/bash

# CV Reader Backend Deployment Script
# Supports Railway, Heroku, and Render

echo "🚀 CV Reader Backend Deployment Script"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run from backend directory."
    exit 1
fi

echo "📋 Available deployment options:"
echo "1. Railway (Recommended - Free tier)"  
echo "2. Heroku (Requires credit card)"
echo "3. Render (Free tier with limitations)"
echo "4. Local development server"

read -p "Choose deployment option (1-4): " choice

case $choice in
    1)
        echo "🚂 Deploying to Railway..."
        
        # Check if railway CLI is installed
        if ! command -v railway &> /dev/null; then
            echo "Installing Railway CLI..."
            npm install -g @railway/cli
        fi
        
        echo "Please follow these steps:"
        echo "1. Go to https://railway.app"
        echo "2. Sign up with GitHub"
        echo "3. Run: railway login"
        echo "4. Run: railway link (select your project)"
        echo "5. Run: railway up"
        echo ""
        echo "Your API will be available at: https://your-project.railway.app"
        ;;
        
    2)
        echo "🟣 Deploying to Heroku..."
        
        # Check if heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not found. Please install:"
            echo "https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        read -p "Enter your Heroku app name: " app_name
        
        echo "Creating Heroku app..."
        heroku create $app_name
        
        echo "Deploying..."
        git add .
        git commit -m "Deploy backend to Heroku"
        git subtree push --prefix backend heroku main
        
        echo "✅ Deployed to: https://$app_name.herokuapp.com"
        ;;
        
    3)
        echo "🎨 Deploying to Render..."
        echo "Please follow these steps:"
        echo "1. Go to https://render.com"
        echo "2. Connect your GitHub repository"  
        echo "3. Create a new Web Service"
        echo "4. Select your repository and backend folder"
        echo "5. Set these settings:"
        echo "   - Build Command: pip install -r requirements.txt"
        echo "   - Start Command: gunicorn app:app"
        echo "   - Environment: Python 3"
        echo ""
        echo "Your API will be available at: https://your-service.onrender.com"
        ;;
        
    4)
        echo "💻 Starting local development server..."
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate || source venv/Scripts/activate
        
        # Install requirements
        echo "Installing requirements..."
        pip install -r requirements.txt
        
        # Start server
        echo "🚀 Starting server on http://localhost:5000"
        python app.py
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process completed!"
echo ""
echo "📝 Next steps:"
echo "1. Copy your API URL"
echo "2. Update frontend API_BASE_URL in python_version.html"
echo "3. Test the connection"
echo ""
echo "🔗 Frontend files to update:"
echo "- python_version.html"
echo "- hybrid_version.html" 
echo ""
echo "💡 Update this line:"
echo "const API_BASE_URL = 'https://your-deployed-api-url';"