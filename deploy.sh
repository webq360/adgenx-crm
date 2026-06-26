#!/bin/bash
# Production Deployment Script for PythonAnywhere

echo "🚀 Starting deployment..."

# Step 1: Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Step 2: Copy production environment
echo "⚙️  Setting up environment..."
cp .env.pythonanywhere .env

# Step 3: Install dependencies
echo "📦 Installing dependencies..."
pip install --user -r requirements.txt

# Step 4: Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Step 5: Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Step 6: Activate pending users (optional)
echo "👥 Checking for pending users..."
python manage.py activate_pending_users

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to PythonAnywhere Web tab"
echo "2. Click 'Reload' button"
echo "3. Test the website: https://webq.pythonanywhere.com"
echo ""
echo "🧪 Test checklist:"
echo "- [ ] Website loads"
echo "- [ ] Registration works (no CAPTCHA error)"
echo "- [ ] Login works"
echo "- [ ] Ad Accounts table shows new columns"
echo "- [ ] CORS test: https://webq.pythonanywhere.com/api/cors-test/"
