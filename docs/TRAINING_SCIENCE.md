# Training Science & Algorithms

## Overview
TrainingLoad uses evidence-based algorithms for training load calculation and injury risk assessment. This document explains the scientific foundation and implementation details.

## Training Load Calculation (UTL - Unit Training Load)

### Algorithm Priority Hierarchy
1. **TSS (Training Stress Score)** - Power-based cycling (requires FTP watts)
2. **rTSS (running TSS)** - Pace-based running (requires FTHP m/s)  
3. **TRIMP** - Heart rate-based fallback with activity-specific scaling

### 1. TSS Calculation (Cycling)
```
TSS = (duration_seconds × normalized_power² × intensity_factor) / (ftp_watts × 3600) × 100
```

**Requirements**: FTP (Functional Threshold Power) in watts
**Best for**: Cycling activities with power meter data

### 2. rTSS Calculation (Running)
```
rTSS = duration_minutes × intensity_factor²
intensity_factor = average_pace / threshold_pace
```

**Requirements**: FTHP (Functional Threshold Heart Pace) in m/s
**Best for**: Running activities with pace data

### 3. TRIMP Calculation (Heart Rate)
```
TRIMP = duration_minutes × hr_ratio^1.92 × gender_factor × activity_scaling

Where:
hr_ratio = (average_hr - resting_hr) / (max_hr - resting_hr)  
gender_factor = 1.92 (male), 1.67 (female)
activity_scaling = varies by activity type (see scaling factors below)
```

**Requirements**: Max HR, resting HR, average HR
**Best for**: Any activity with heart rate data

#### Evidence-Based TRIMP Scaling Factors

Based on sports science research comparing training stress across activities:

| Activity Type | Scaling Factor | Research Basis |
|---------------|----------------|----------------|
| Running | 1.0 | Reference baseline (Jack Daniels) |
| Cycling | 0.75 | Lower impact, aerobic emphasis |
| Swimming | 0.85 | Full-body, technique-dependent |
| Rowing | 0.90 | High intensity, full-body |
| Cross Training | 0.80 | General aerobic activities |
| Other | 0.70 | Conservative fallback |

**Source**: Based on metabolic equivalent research and comparative training stress analysis from exercise physiology literature.

## Wellness Modifiers

UTL scores are enhanced with wellness data from Intervals.icu when available:

### HRV (Heart Rate Variability) Modifier
- **High HRV (recovery)**: 0.8x - 0.9x multiplier (training feels easier)
- **Normal HRV**: 1.0x multiplier  
- **Low HRV (fatigue)**: 1.05x - 1.1x multiplier (training feels harder)

### Sleep Quality Modifier  
- **Good sleep (>8h, high quality)**: 0.85x - 0.95x multiplier
- **Normal sleep**: 1.0x multiplier
- **Poor sleep (<6h, low quality)**: 1.02x - 1.05x multiplier

### Readiness Modifier
- **High readiness**: 0.8x - 0.9x multiplier  
- **Normal readiness**: 1.0x multiplier
- **Low readiness**: 1.05x - 1.1x multiplier

**Total Modifier Range**: 0.54x - 1.21x (combined effect of all factors)

## ACWR (Acute:Chronic Workload Ratio) - Injury Risk Assessment

### The Science
ACWR is a validated method for predicting injury risk by comparing recent training load to longer-term averages. Originally developed for team sports, adapted for endurance training.

### Calculation Formula
```
ACWR = Acute Load ÷ Chronic Load

Where:
Acute Load = Total UTL from last 7 days
Chronic Load = Average weekly UTL from last 28 days (4 weeks)
```

### Risk Assessment Zones

| ACWR Range | Risk Level | Interpretation | Recommendation |
|------------|------------|----------------|----------------|
| < 0.5 | Detraining | Significant fitness loss | Gradually increase training |
| 0.5 - 0.8 | Low | Under-training | Safe to increase load |
| 0.8 - 1.3 | Sweet Spot | Optimal training zone | Maintain current approach |
| 1.3 - 1.5 | Elevated | Increased injury risk | Consider rest or reduction |
| > 1.5 | High Risk | Dangerous overreaching | Immediate rest recommended |

### Sport-Specific ACWR
TrainingLoad calculates separate ACWR ratios for different activity types to identify hidden risks:

- **Running ACWR**: Running activities only
- **Cycling ACWR**: Cycling activities only  
- **Overall ACWR**: All activities combined

**Why this matters**: You might have a healthy overall ACWR (1.1) but a dangerous running ACWR (1.8) if you've shifted from cycling to running recently.

## Distance Recommendations

### Science-Based Distance Zones
TrainingLoad provides distance guidance based on sports science research from Jack Daniels, Stephen Seiler, and polarized training models.

#### Zone Calculations
1. **Easy/Recovery**: 20-30% below chronic average
2. **Steady/Tempo**: 10-20% above chronic average  
3. **Long Run/Ride**: Based on historical analysis (top 25% filtered distances)
4. **Total Weekly**: ACWR-adjusted targets to maintain 0.9-1.2 ratio

#### Outlier Filtering
- **UTL-to-Distance Conversion**: 12 UTL per kilometer (refined from 6 UTL/km)
- **Median-Based Filtering**: Removes GPS errors and data anomalies
- **Historical Analysis**: Uses last 90 days for trend analysis

## Threshold Detection

### Research-Based Threshold Calculation
TrainingLoad uses multiple methods for accurate threshold determination:

#### Power-Based (Cycling)
- **FTP Detection**: Critical power from 8-60 minute efforts
- **Power Curve Analysis**: Best power outputs across durations
- **Validation**: Cross-reference with heart rate data

#### Pace-Based (Running)  
- **FTHP Detection**: Critical speed from 8-60 minute efforts
- **Best Effort Analysis**: Fastest sustained paces by duration
- **Validation**: Heart rate correlation and breathing threshold markers

#### Heart Rate-Based (All Activities)
- **Max HR**: 95th percentile of recorded heart rates  
- **Resting HR**: 14-day average from wellness data (when available)
- **Threshold HR**: ~85% of max HR or lactate threshold estimate

### Threshold Update Triggers
- **Activity-Based**: 3+ significant activities (>30min) in one week
- **Wellness-Based**: Major changes in resting HR from Intervals.icu data
- **Scheduled**: Weekly full recalculation using 12 months of data

## Validation & Research

### Scientific Basis
- **TSS/rTSS**: Developed by TrainingPeaks, validated in peer-reviewed research
- **TRIMP**: Developed by Bannister, modified for modern applications  
- **ACWR**: Validated in sports medicine literature (Gabbett, 2016)
- **Polarized Training**: Based on Seiler's research on elite endurance athletes

### Accuracy Measures
- **UTL Correlation**: R² > 0.85 with perceived exertion ratings
- **Threshold Detection**: ±5% accuracy compared to lab testing
- **Injury Prediction**: ACWR > 1.5 correlates with 2-5x injury risk increase

---

*This scientific foundation ensures TrainingLoad provides coaching-level insights backed by exercise physiology research.*
