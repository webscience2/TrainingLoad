# TrainingLoad Production Deployment Guide

## Prerequisites

### 1. Google Cloud Setup
- **Google Cloud Project**: Create or select a project
- **Billing**: Enable billing on your project
- **Google Cloud SDK**: Install and configure locally

```bash
# Install Google Cloud SDK (macOS)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Required APIs
Enable these APIs in your Google Cloud project:

```bash
gcloud services enable appengine.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

## Database Setup

### 1. Create Cloud SQL Instance
```bash
# Create PostgreSQL instance
gcloud sql instances create trainload-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=03:00

# Create database
gcloud sql databases create trainload --instance=trainload-db

# Create user
gcloud sql users create trainload \
    --instance=trainload-db \
    --password=YOUR_SECURE_PASSWORD
```

### 2. Configure Database Schema
```bash
# Connect to your database and run schema creation
gcloud sql connect trainload-db --user=trainload

# In psql, run your schema creation scripts
# (Copy SQL from your models.py or existing database)
```

## Environment Configuration

### 1. Update app.yaml
Edit `backend/app.yaml` and replace:
```yaml
beta_settings:
  cloud_sql_instances: YOUR_PROJECT:us-central1:trainload-db
```

### 2. Set Environment Variables
Configure these in Google Cloud Console → App Engine → Settings:

```bash
DATABASE_URL=postgresql://trainload:YOUR_PASSWORD@/trainload?host=/cloudsql/YOUR_PROJECT:us-central1:trainload-db
STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
ENVIRONMENT=production
```

## Strava API Configuration

### 1. Create Strava Application
1. Go to https://www.strava.com/settings/api
2. Create new application
3. Set Authorization Callback Domain to: `your-project.appspot.com`
4. Note the Client ID and Client Secret

### 2. Update Redirect URI
Your Strava app should have redirect URI:
```
https://YOUR_PROJECT.appspot.com/auth/strava/callback
```

## Frontend Deployment Preparation

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
```

### 2. Configure API Endpoint
Update frontend configuration to point to your production API:
```javascript
const API_BASE_URL = 'https://YOUR_PROJECT.appspot.com';
```

## Backend Deployment

### 1. Run Deployment Script
```bash
cd backend
./deploy.sh
```

### 2. Manual Deployment (Alternative)
```bash
cd backend
gcloud app deploy app.yaml
```

## Cloud Scheduler Setup

### 1. Run Scheduler Setup
```bash
cd backend
./setup-scheduler.sh
```

### 2. Verify Jobs
```bash
gcloud scheduler jobs list
```

## Post-Deployment Configuration

### 1. Test Health Check
```bash
curl https://YOUR_PROJECT.appspot.com/health
```

### 2. Test API Endpoints
```bash
# View API documentation
open https://YOUR_PROJECT.appspot.com/docs

# Test scheduler jobs
curl -X POST https://YOUR_PROJECT.appspot.com/scheduler/jobs
```

### 3. Run Initial Data Sync
```bash
# Trigger manual sync for testing
curl -X POST https://YOUR_PROJECT.appspot.com/scheduler/run/quick_sync
```

## Monitoring & Maintenance

### 1. View Logs
```bash
gcloud app logs tail -s default
```

### 2. Monitor Performance
- Google Cloud Console → App Engine → Services
- Monitor instance scaling and performance metrics

### 3. Database Monitoring
- Google Cloud Console → SQL → trainload-db
- Monitor connections, CPU, and storage usage

## Scaling Configuration

### Current Configuration
- **Min Instances**: 1 (always warm)
- **Max Instances**: 10 (auto-scaling)
- **Instance Class**: F2 (balanced CPU/memory)

### Adjust Scaling (Optional)
Edit `app.yaml` to modify:
```yaml
automatic_scaling:
  min_instances: 2  # More responsive
  max_instances: 20  # Handle higher load
  target_cpu_utilization: 0.5  # Scale earlier
```

## Security Considerations

### 1. Environment Variables
- Never commit secrets to git
- Use Google Cloud Secret Manager for sensitive data
- Rotate API keys regularly

### 2. Database Security
- Use strong passwords
- Enable SSL connections
- Regular security updates

### 3. Application Security
- HTTPS only (enforced by App Engine)
- CORS properly configured
- Input validation on all endpoints

## Troubleshooting

### Common Issues

#### Deployment Fails
```bash
# Check deployment logs
gcloud app logs tail -s default

# Verify requirements.txt
cat requirements.txt
```

#### Database Connection Issues
```bash
# Test Cloud SQL connection
gcloud sql connect trainload-db --user=trainload

# Verify instance name in app.yaml
# Format: project:region:instance
```

#### Scheduler Jobs Failing
```bash
# Check job status
gcloud scheduler jobs list

# View job logs
gcloud logging read "resource.type=cloud_scheduler_job" --limit=50
```

### Performance Issues
- Monitor App Engine quotas and limits
- Check database connection pooling
- Review CPU/memory usage in Cloud Console

## Cost Optimization

### Expected Costs (Approximate)
- **App Engine**: ~$20-50/month (F2 instances, moderate usage)
- **Cloud SQL**: ~$15-25/month (db-f1-micro)
- **Cloud Scheduler**: ~$1/month (5 jobs)
- **Total**: ~$35-75/month

### Cost Reduction Tips
- Use F1 instances for lower traffic
- Reduce min_instances to 0 (cold starts acceptable)
- Use smaller Cloud SQL tier (db-e2-micro)

## Backup & Recovery

### Database Backups
- Automated daily backups enabled
- Point-in-time recovery available
- Test restore procedures monthly

### Application Recovery
- Source code in Git repository
- Quick redeployment capability
- Environment variables documented

---

**Ready to Deploy?**

1. Complete prerequisites
2. Set up database and environment variables
3. Run `./deploy.sh` from backend directory
4. Run `./setup-scheduler.sh` for background jobs
5. Test all endpoints and functionality

For issues or questions, see the troubleshooting section or check application logs.
