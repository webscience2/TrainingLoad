#!/bin/bash
# TrainingLoad Production Deployment Script

set -e  # Exit on any error

echo "🚀 TrainingLoad Production Deployment"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "app.yaml" ]; then
    echo "❌ Error: app.yaml not found. Please run from backend/ directory"
    exit 1
fi

# Check if gcloud is installed and configured
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK"
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No Google Cloud project configured"
    echo "   Run: gcloud auth login && gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_ID"
echo "   Runtime: Python 3.11"
echo "   Service: App Engine Standard"
echo ""

# Check if required APIs are enabled
echo "🔍 Checking required Google Cloud APIs..."
REQUIRED_APIS=(
    "appengine.googleapis.com"
    "sqladmin.googleapis.com"
    "cloudbuild.googleapis.com"
    "secretmanager.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "   ✅ $api"
    else
        echo "   ❌ $api (not enabled)"
        echo "      Enable with: gcloud services enable $api"
        exit 1
    fi
done

# Validate app.yaml configuration
echo ""
echo "🔧 Validating deployment configuration..."
if grep -q "PROJECT_ID:REGION:INSTANCE_NAME" app.yaml; then
    echo "   ⚠️  Warning: Update Cloud SQL connection string in app.yaml"
    echo "      Replace: PROJECT_ID:REGION:INSTANCE_NAME"
    echo "      With: your-project:region:instance-name"
fi

# Check for environment variables
echo ""
echo "🔐 Environment Variables Check:"
echo "   Please ensure these are configured in Google Cloud Console:"
echo "   - DATABASE_URL (Cloud SQL connection string)"
echo "   - STRAVA_CLIENT_ID (Strava OAuth)"
echo "   - STRAVA_CLIENT_SECRET (Strava OAuth)"
echo "   - INTERVALS_ICU_BASE_URL (optional)"
echo ""

# Pre-deployment tests
echo "🧪 Running pre-deployment checks..."
if [ -f "main.py" ]; then
    echo "   ✅ main.py found"
else
    echo "   ❌ main.py not found"
    exit 1
fi

if [ -f "requirements.txt" ] && [ -s "requirements.txt" ]; then
    echo "   ✅ requirements.txt found and not empty"
else
    echo "   ❌ requirements.txt missing or empty"
    exit 1
fi

# Deployment confirmation
echo ""
echo "🚨 Ready to deploy to production!"
echo "   Target: $PROJECT_ID (App Engine)"
echo "   This will:"
echo "   - Deploy the backend API to App Engine"
echo "   - Configure automatic scaling (1-10 instances)"
echo "   - Set up health checks"
echo "   - Enable Cloud SQL connections"
echo ""

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Deploy to App Engine
echo ""
echo "🚀 Deploying to App Engine..."
gcloud app deploy app.yaml --quiet

# Get the deployed URL
URL=$(gcloud app browse --no-launch-browser 2>&1 | grep -o 'https://[^[:space:]]*')
if [ -n "$URL" ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo "   URL: $URL"
    echo "   API Docs: $URL/docs"
    echo "   Health Check: $URL/health"
else
    echo "✅ Deployment completed (URL not captured)"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Configure environment variables in Google Cloud Console"
echo "2. Set up Cloud Scheduler for background jobs"
echo "3. Configure custom domain (optional)"
echo "4. Set up monitoring and alerting"
echo ""
echo "📚 Documentation: docs/ARCHITECTURE.md"
