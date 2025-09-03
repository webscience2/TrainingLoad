Product Requirements Document (PRD): The "TrainSmart" Protocol Engine


Section 7: Vision and Core Principles


7.1 Product Vision

To be the most intelligent and scientifically-grounded training companion for multi-sport endurance athletes, providing daily, personalized training load recommendations that maximize performance gains while proactively minimizing the risk of overuse injuries.

7.2 Core Principles

Science First: Every recommendation must be traceable to established physiological principles and peer-reviewed research. The system's logic is transparently based on the models of progressive overload, unified training stress, ACWR, and HRV.
Individuality: The system must adapt to the user's unique physiology, goals, and history. One-size-fits-all plans are explicitly rejected in favor of a dynamic, N-of-1 approach.
Proactive, Not Reactive: The primary goal is injury prevention through intelligent load management, not just performance tracking. The system is designed to anticipate and mitigate risk before it leads to a training disruption.
Data-Driven: All decisions are made algorithmically based on objective data from the user's Garmin device. Subjective feelings are acknowledged but do not override objective physiological markers when making load recommendations.

Section 8: User Profile, Onboarding, and Baselines


8.1 User Registration and Garmin Authentication

The user will create an account using a standard email and password. Immediately upon registration, the user will be prompted to connect their Garmin Connect account. This is a mandatory step, as the application cannot function without a data source. The connection will be established via a secure OAuth 2.0 flow, where the user explicitly grants the application read-only access to their Health and Activity data.

8.2 Initial User Input

Upon successful authentication, the user will complete a one-time onboarding questionnaire to provide essential personalization data:
Demographics:
Age (Years)
Gender (Male/Female) - Used for Banister's TRIMP formula selection.
Weight (kg or lbs) - Used for calculating power-to-weight ratio and other potential metrics.
Injury History:
A multi-select checklist of common overuse injuries, including but not limited to: Plantar Fasciitis, Achilles Tendonitis, Shin Splints (MTSS), IT Band Syndrome, Runner's Knee (PFPS), and Stress Fractures.
Selection of one or more of these options will automatically enable the "Conservative Mode" for ACWR thresholds, narrowing the "sweet spot" to 0.8-1.2.
Event Goals:
The user must be able to add one or more target events.
For each event, they must specify:
Event Name (e.g., "Chicago Marathon")
Sport (Running, Cycling, Duathlon, Triathlon)
Event Type/Distance (e.g., 10k, Half Marathon, Marathon, 50-mile Gravel Race, Century Ride, etc.)
Event Date

8.3 Physiological Baseline Establishment

This is the most critical phase of onboarding. The system's accuracy is entirely dependent on valid physiological baselines.
Threshold Testing: The user will be guided to input their current physiological thresholds. The UI will strongly emphasize the importance of these values for accurate load calculation.
Cycling: Functional Threshold Power (FTP) in watts.
Running: Functional Threshold Pace (FThP) in min/mile or min/km.
Heart Rate: Maximum Heart Rate (Max HR) and Resting Heart Rate (RHR) in bpm.
The application will provide links to standardized field test protocols (e.g., 20-minute FTP test, 30-minute run test) to help users determine these values accurately.
HRV Baseline Period: After completing the profile, the system will enter an initial 10-day HRV baseline establishment period.
The user will be instructed to take a daily morning HRV reading using their Garmin device.
During this period, daily training recommendations will be generated, but they will be based solely on a conservative ACWR progression model. HRV-based modifications will be disabled.
The UI will display a countdown (e.g., "7 days of HRV data remaining to unlock full personalization") to encourage compliance. After 10 consecutive days of readings, the HRV-guided features will be fully activated.

Section 9: The Core Algorithm: From Raw Data to Daily Recommendation

The core of the product is a daily-executed algorithm that synthesizes all available data into a single, actionable training load recommendation.

9.1 Step 1: Daily Data Ingestion and Processing

This process will run automatically once per day for each user (e.g., at 4:00 AM in their local timezone).
Fetch Health Data: Make a call to the Garmin Health API to retrieve the user's health summary for the previous day. This includes the latest nightly RMSSD, sleep data, and resting heart rate.
Fetch Activity Data: Make a call to the Garmin Activity API to check for any new activities completed since the last sync.
Process Activities: For each new activity file:
Download the.FIT file.
Parse the file to extract relevant data streams.
Execute the UTL calculation logic from Section 2.4, using the hierarchical model (Power TSS > Pace rTSS > HR-based TRIMP).
Store the calculated UTL score and all relevant raw and summary data in the application's database, linked to the user and activity.

9.2 Step 2: Update Long-Term Metrics

Recalculate Load Averages: Using the new daily UTL scores, update the user's Acute Training Load (ATL) and Chronic Training Load (CTL) values. These will be calculated using an EWMA formula with time constants of 7 days for ATL and 42 days for CTL.
ATLtoday​=(UTLtoday​×αATL​)+(ATLyesterday​×(1−αATL​)), where αATL​=2/(7+1)
CTLtoday​=(UTLtoday​×αCTL​)+(CTLyesterday​×(1−αCTL​)), where αCTL​=2/(42+1)
Calculate ACWR: Compute the current ACWR by dividing the updated ATL by the updated CTL.

9.3 Step 3: Assess Daily Readiness

Retrieve HRV Data: Access the latest morning lnRMSSD reading from the ingested health data.
Compare to Baseline: Compare this value to the user's 7-day rolling mean and standard deviation of lnRMSSD.
Assign Readiness State: Categorize the user's daily readiness into one of three states:
GREEN (Ready for Intensity): daily_lnRMSSD ≥ (baseline_mean - 0.5 * baseline_SD)
AMBER (Proceed with Caution): (baseline_mean - 1.0 * baseline_SD) ≤ daily_lnRMSSD < (baseline_mean - 0.5 * baseline_SD)
RED (Recovery Recommended): daily_lnRMSSD < (baseline_mean - 1.0 * baseline_SD)

9.4 Step 4: The Recommendation Engine (Decision Logic)

This final step integrates the user's long-term plan, medium-term injury risk (ACWR), and short-term readiness (HRV) to generate the daily recommendation.
Determine Planned Load: Based on the user's event goals and current training phase (e.g., base, build, peak, taper), the system calculates a target weekly UTL designed to produce a gradual increase in CTL (e.g., +3 to +5 CTL points per week in a build phase). This target is broken down into a "planned" daily UTL.
Apply Decision Matrix: The system uses the logic defined in Table 2 to modify the planned load based on the current ACWR and HRV state.
Generate Output: The final output presented to the user consists of:
A target UTL number for the day (e.g., "Today's Target Load: 95").
A qualitative readiness summary (e.g., "Your HRV is in the normal range, and your training load is well-managed. You are cleared for high-intensity training.").
A suggested modality split (e.g., "Recommendation: 95 UTL Run OR 95 UTL Bike OR a combination like a 50 UTL Run + 45 UTL Bike.").

9.5 Table 2: The Recommendation Engine Decision Matrix

This matrix forms the logical core of the recommendation engine, defining the explicit rules that govern every daily output.
ACWR Zone
HRV Readiness
Resulting Action
Target UTL
Intensity Allowed
Danger (≥1.5)
Any
Forced Recovery
< 40% of Daily Avg
Low Only (Z1/2)
Any
RED (Recovery)
Forced Recovery
< 40% of Daily Avg
Low Only (Z1/2)
Caution (1.3-1.5)
AMBER or GREEN
Maintain/Reduce Load
≤ ATL/7
Low/Moderate (No HIIT)
Sweet Spot (<1.3)
AMBER (Caution)
Maintain/Reduce Load
≤ ATL/7
Low/Moderate (No HIIT)
Sweet Spot (<1.3)
GREEN (Ready)
Proceed as Planned
Follow Long-Term Plan
All Intensities Allowed


Section 10: Functional Requirements and User Stories


10.1 Athlete Stories

FR-1: As an athlete, I want to connect my Garmin account during onboarding so the app can automatically import all my training data.
FR-2: As an athlete, I want to input my goals, like an upcoming marathon, so the system can create a long-term plan for me.
FR-3: As an athlete with a history of shin splints, I want to tell the app about my injury history so it can provide more cautious recommendations.
FR-4: As an athlete, I want to see a single, clear number on my dashboard each day that tells me how much training load I should aim for.
FR-5: As an athlete, I want to receive a clear warning when my training load is increasing too quickly so I can prevent an overuse injury.
FR-6: As an athlete, I want the system to tell me to take an easy day or rest when my body is not recovered, based on my morning HRV reading.
FR-7: As an athlete, I want to use a planner to schedule my workouts for the upcoming week and see how my plan will affect my future training load and injury risk.

10.2 System Requirements

SR-1: The system must implement a secure OAuth 2.0 client to authenticate with the Garmin Connect API.
SR-2: The system must include a FIT file decoder capable of parsing session, lap, and record messages for running and cycling activities.
SR-3: The system must implement algorithms to calculate power-based TSS, pace-based rTSS, and heart rate-based TRIMP.
SR-4: The system must store historical time-series data for all relevant user metrics in a relational or time-series database.
SR-5: The recommendation algorithm must be executed via an automated daily cron job for all active users.
SR-6: The system must maintain a rolling 7-day baseline of lnRMSSD for each user to facilitate daily HRV analysis.

Section 11: Data Model and API Integration Specification


11.1 Database Schema (Simplified)

Users Table:
user_id (PK), email, password_hash, age, gender, weight, garmin_user_id, garmin_oauth_token, garmin_oauth_secret, injury_history_flags (JSON or bitmask).
Thresholds Table:
threshold_id (PK), user_id (FK), ftp_watts, fthp_mps, max_hr, resting_hr, date_updated.
Activities Table:
activity_id (PK), user_id (FK), garmin_activity_id, start_time, sport, duration_sec, distance_m, UTL_score, calculation_method (e.g., 'TSS', 'rTSS', 'TRIMP'), raw_fit_file_path.
Daily_Health_Summaries Table:
summary_id (PK), user_id (FK), calendar_date, lnRMSSD, sleep_seconds, deep_sleep_seconds, resting_hr, avg_stress_level.
Training_Load_Metrics Table:
metric_id (PK), user_id (FK), calendar_date, daily_UTL, ctl, atl, acwr.

11.2 API Integration Specification

Garmin API Endpoints:
GET /garmin/api/health: To retrieve daily health summaries.
GET /garmin/api/activities: To retrieve a list of new activities.
GET /garmin/api/activities/{id}/download: To download the raw.FIT file for a specific activity.
Error Handling: The integration must handle potential API errors, such as rate limiting (429), unauthorized (401), and server errors (5xx).
Data Backfilling: For a new user, the system must include a mechanism to backfill at least 90 days of historical activity and health data from Garmin Connect to establish initial CTL and HRV baselines.

Section 12: User Interface (UI) and Visualization Recommendations


12.1 The Dashboard (Home Screen)

The dashboard is the primary user interaction point and must convey the daily recommendation with absolute clarity.
Primary Recommendation Card: A large, prominent card at the top of the screen displaying:
Today's Target UTL: e.g., "95".
HRV Readiness State: A color-coded icon and text (e.g., GREEN icon with "Ready for Intensity").
ACWR Status: A color-coded gauge or bar showing the current ACWR value (e.g., 1.1) within the context of the safe (green), caution (orange), and danger (red) zones, similar to the mytf.run interface.
Plain Language Summary: A concise sentence explaining the "why" behind the recommendation, e.g., "Your body is well-recovered, and your training load is in the sweet spot. Today is a good day for a high-quality workout."

12.2 The Planner View

This view allows for proactive planning and is a key differentiator.
Calendar Interface: A weekly or monthly calendar view. Past days show the completed UTL for each activity. Future days show the system's recommended UTL.
Interactive Planning: Users can click on a future day to schedule a specific workout (e.g., "Long Run - 15 miles" or "Interval Ride - 2x20 min @ FTP").
Dynamic Forecasting: As the user adds or modifies planned workouts, the system will estimate the UTL for those sessions and instantly recalculate and re-render the future ACWR forecast on the calendar. This provides immediate visual feedback, showing the user if their plan will push them into the danger zone, a core feature inspired by mytf.run.

12.3 The Performance Chart

This view provides the user with a macro-level perspective on their training progression over time.
Performance Management Chart: A direct implementation of the classic fitness-fatigue model chart.
The chart will plot three lines over a selectable time period (e.g., 6 weeks, 3 months, 1 year):
CTL (Fitness): A blue line showing the long-term trend of fitness.
ATL (Fatigue): A pink line showing short-term fatigue.
Training Stress Balance (TSB = CTL - ATL): Yellow bars representing daily form or readiness. Positive TSB indicates good form, while negative TSB indicates fatigue.
This chart gives the user a powerful visual tool to understand their training cycles, see how their fitness is building, and plan for periods of peak form for their target events.
