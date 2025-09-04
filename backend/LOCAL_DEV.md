# Local Development Workflow for TrainSmart Backend

## 1. Activate your virtual environment
```
source .venv/bin/activate
```

## 2. Start the Cloud SQL Proxy (in a separate terminal)
```
./cloud-sql-proxy --credentials-file=../trainload-app-4da9cdff6ac6.json trainload-app:us-central1:trainload
```

## 3. Run the FastAPI app locally with hot reload
```
uvicorn main:app --reload
```
- The app will be available at http://127.0.0.1:8000

## 4. Test endpoints locally
- Use curl, Postman, or your browser to hit endpoints like:
```
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "yourpassword", "age": 30, "gender": "male", "weight": "70"}'
```

## 5. Make code changes and see instant results
- Uvicorn with `--reload` will auto-restart the server on code changes.

## 6. Deploy to App Engine only when ready
```
gcloud app deploy
```
- Deploy only when you want to update the production/staging environment.

---
**Tip:**
- You can use environment variables in `.env` for local DB credentials.
- Keep the Cloud SQL Proxy running for database access.
