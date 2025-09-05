"""
Research-Based Threshold Calculation Methods

Based on scientific literature and best practices for FTP and running threshold estimation.

Key Research Findings:

CYCLING FTP (Functional Threshold Power):
1. Gold Standard: 60-minute all-out effort = actual FTP
2. 20-minute test: Best 20-min power × 0.95 (most common, validated method)
3. 40-minute test: Best 40-min power × 0.97 (more accurate than 20-min)
4. Critical Power Model: Mathematical approach using power-duration curve
5. Normalized Power considerations: For variable efforts, NP better represents threshold stress

RUNNING THRESHOLD:
1. Lactate Threshold Pace: Sustainable pace for 60+ minutes
2. 20-minute test pace: Best 20-min pace × 1.02-1.05 (slightly faster than LT)
3. Critical Speed/Velocity: Similar to cycling CP, using pace-duration modeling
4. Heart Rate Threshold: ~85-90% of max HR sustained for 60 minutes
5. Velocity at VO2max (vVO2max): Different from threshold - typically 6-8min pace

SLIDING WINDOW ANALYSIS:
- Essential for finding true best sustained efforts within activities
- Removes influence of warm-up, cool-down, and recovery periods
- 1Hz sampling recommended for accuracy
- Multiple duration analysis (5, 10, 15, 20, 30, 40, 60 minutes)

THRESHOLD ESTIMATION HIERARCHY (Best to Worst):
Cycling:
1. 60-minute power (gold standard)
2. 40-minute power × 0.97
3. 20-minute power × 0.95
4. Critical Power modeling
5. Percentile-based estimates (90th-95th percentile × 0.95)

Running:
1. 60-minute best pace (lactate threshold)
2. 30-minute best pace × 1.02
3. 20-minute best pace × 1.05
4. Critical speed modeling
5. Tempo/threshold efforts from structured workouts
