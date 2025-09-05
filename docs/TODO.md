# TODO.md: TrainSmart Protocol Engine Development Tracker

[x] Initialize repository structure (backend, frontend, docs)
[x] Set up GCP project
[x] Enable required APIs
[x] Set up billing
[x] Create Cloud SQL (Postgres) instance
[x] Create service account
[x] Deploy backend to App Engine (URL: https://trainload-app.uw.r.appspot.com)

## 2. Authentication & Onboarding
~ Implement user registration (email/password)  
[x] Integrate Strava OAuth 2.0 authentication (mandatory)
- [ ] Onboarding questionnaire (demographics, injury history, event goals)
- [ ] Physiological baseline input UI (FTP, FThP, Max HR, RHR)
- [ ] HRV baseline period logic (10-day countdown, compliance UI)

## 3. Data Ingestion & Processing

~ Integrate Strava Activity API endpoints  
[x] Implement daily cron job for data ingestion (4:00 AM local time)
- [ ] Download and parse .FIT/.TCX/.GPX files (use pre-built library)
- [ ] Calculate UTL scores (Power TSS, Pace rTSS, HR-based TRIMP)
- [ ] Store raw and processed data in database
- [ ] Backfill 90 days of historical activity data for new users

## 4. Core Algorithm & Metrics
- [ ] Implement ATL/CTL/ACWR calculations (EWMA formulas)
- [ ] Recommendation engine (ACWR-based decision matrix, daily output)

## 5. User Interface
- [ ] Responsive web dashboard (primary recommendation card, ACWR gauge, HRV state)
- [ ] Planner view (calendar, interactive planning, dynamic ACWR forecast)
- [ ] Performance chart (CTL, ATL, TSB visualization)

## 6. Notifications
- [ ] Configurable email notifications (daily recommendations, warnings)

## 7. System & API Integration
- [ ] Error handling for Strava API (rate limits, auth, server errors)
[x] Secure storage of OAuth tokens
[x] Relational/time-series database schema implementation

## 8. Testing & QA
- [ ] Unit and integration tests for backend logic
- [ ] UI/UX testing for web frontend
- [ ] End-to-end tests for onboarding and data flow

## 9. Documentation
- [ ] Update PRD as needed
- [ ] Developer setup guide
- [ ] API documentation

---
**Legend:**
- [ ] Not started
- [x] Complete
- [~] In progress

Add comments or links to issues as needed for each item.
