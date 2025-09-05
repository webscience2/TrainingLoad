# ACWR (Acute:Chronic Workload Ratio) Calculation - Complete Explanation

## Overview

The **Acute:Chronic Workload Ratio (ACWR)** is a scientific method for monitoring training load and predicting injury risk. It compares your recent training load (acute) to your longer-term average (chronic) to determine if you're training within safe parameters.

## The Formula

```
ACWR = Acute Load ÷ Chronic Load
```

Where:
- **Acute Load** = Total UTL from last 7 days
- **Chronic Load** = Average weekly UTL from last 28 days (4 weeks)

## Step-by-Step Calculation

### Step 1: Calculate Acute Load (Last 7 Days)
Sum up all UTL scores from activities in the past 7 days.

**Example for User 1 (as of Sept 5, 2025):**
- Sept 4: Cycling (2.1 UTL)
- Sept 2: Running (219.0 UTL) 
- Sept 1: Hiking (26.7 UTL) + Hiking (18.7 UTL)
- Aug 31: Running (90.7 UTL) + Running (88.3 UTL)

**Acute Load = 445.6 UTL**

### Step 2: Calculate Chronic Load (4-Week Average)
1. Get total UTL from last 28 days
2. Divide by 4 to get weekly average

**Example for User 1:**
- Week 35 (Aug 29 - Sep 5): 445.6 UTL
- Week 34 (Aug 22 - Aug 28): 623.4 UTL  
- Week 33 (Aug 15 - Aug 21): 428.0 UTL
- Week 32 (Aug 8 - Aug 14): 53.9 UTL

**Total 28-day UTL = 1,550.9**
**Chronic Load = 1,550.9 ÷ 4 = 387.7 UTL/week**

### Step 3: Calculate ACWR
```
ACWR = 445.6 ÷ 387.7 = 1.15
```

## Risk Assessment Zones

The system uses evidence-based thresholds to assess injury risk:

| ACWR Range | Risk Level | Meaning | Action |
|------------|------------|---------|---------|
| **< 0.8** | 🟡 Detraining | Load too low, fitness may decline | Gradually increase training |
| **0.8 - 1.2** | 🟢 Low Risk | **SWEET SPOT** - Optimal training zone | Continue current approach |
| **1.2 - 1.3** | 🟠 Moderate Risk | Approaching upper safe limit | Be cautious, monitor closely |
| **> 1.3** | 🔴 High Risk | Significant injury risk | Reduce training immediately |
| **> 1.4** | 🚨 Critical | Extreme risk - immediate action needed | Take rest days |

## Real-World Example Analysis

**User 1's Current Status:**
- **ACWR**: 1.15
- **Risk Level**: 🟢 Low Risk  
- **Interpretation**: "Load within safe parameters"

**Why This is Safe:**
- Acute load (445.6) is only 15% higher than chronic average (387.7)
- Well within the 0.8-1.2 optimal range
- Indicates controlled progression, not a dangerous spike

**What If Scenarios:**

1. **ACWR = 0.7**: Too low - user is training less than their 4-week average, fitness may decline
2. **ACWR = 1.4**: Dangerous - acute load is 40% higher than recent average, high injury risk
3. **ACWR = 2.0**: Critical - acute load double the chronic average, likely overreaching

## Scientific Background

### Research Foundation
The ACWR concept is based on:
- **Tim Gabbett's research** (2016) on training load and injury prediction
- **Studies in elite athletes** showing ACWR > 1.5 increases injury risk by 2-7x
- **Meta-analyses** confirming optimal range of 0.8-1.3 for most sports

### Why These Timeframes?
- **7-day acute window**: Captures immediate training stress and fatigue
- **28-day chronic window**: Represents fitness adaptations and training capacity
- **Weekly averaging**: Smooths out day-to-day variations

## Technical Implementation Details

### Data Sources
- **UTL Scores**: Calculated from power (TSS), pace (rTSS), or heart rate (TRIMP)
- **Activity Types**: All activities included (cycling, running, hiking, etc.)
- **Time Zones**: Uses activity start time, handles day boundaries correctly

### Calculation Code
```python
def _calculate_workload_ratios(self, user_id: int, db: Session) -> Dict[str, Any]:
    # Get last 28 days for chronic load (4 weeks)  
    chronic_start = datetime.now() - timedelta(days=28)
    # Get last 7 days for acute load (1 week)
    acute_start = datetime.now() - timedelta(days=7)
    
    # Query activities and sum UTL scores
    chronic_activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.start_date >= chronic_start,
        Activity.utl_score.isnot(None)
    ).all()
    
    acute_activities = db.query(Activity).filter(
        Activity.user_id == user_id, 
        Activity.start_date >= acute_start,
        Activity.utl_score.isnot(None)
    ).all()
    
    # Calculate loads
    chronic_load = sum([a.utl_score for a in chronic_activities]) / 4.0  # Weekly average
    acute_load = sum([a.utl_score for a in acute_activities])
    
    # Calculate ratio
    acw_ratio = acute_load / chronic_load if chronic_load > 0 else 1.0
```

### Edge Cases
- **New Users**: If chronic_load = 0, ACWR defaults to 1.0 (neutral)
- **Missing Data**: Only includes activities with valid UTL scores
- **Time Zone**: Uses local activity time, not UTC

## Practical Application

### For Athletes
1. **Green Zone (0.8-1.2)**: Train as planned, body is adapting well
2. **Yellow Zone (1.2-1.3)**: Be more conservative, prioritize recovery
3. **Red Zone (>1.3)**: Take rest days, focus on easy activities only

### For Coaches
- **Monitor weekly trends**, not just single values
- **Consider wellness data** alongside ACWR (HRV, sleep, etc.)
- **Individual variation** - some athletes tolerate higher ratios

### Integration with Other Metrics
The TrainingLoad system combines ACWR with:
- **HRV Status**: Poor HRV + high ACWR = extra caution
- **Sleep Quality**: Bad sleep reduces tolerance to high ACWR  
- **Historical Patterns**: Individual baselines and injury history

## Limitations & Considerations

### What ACWR Does Well
✅ Predicts overuse injury risk  
✅ Guides training progression  
✅ Objective, data-driven metric  
✅ Validated across multiple sports  

### What ACWR Doesn't Capture
❌ Acute injuries (falls, collisions)  
❌ Individual resilience differences  
❌ External stress factors  
❌ Training quality vs. quantity  

### Best Practices
1. **Use as guidance**, not absolute rules
2. **Combine with subjective feel** and wellness markers
3. **Consider sport-specific factors** (running vs cycling tolerance)
4. **Account for training experience** (beginners vs veterans)

## Summary

ACWR is a powerful tool for **injury prevention through intelligent load management**. By comparing your recent training (acute) to your 4-week average (chronic), it provides an early warning system for overreaching and helps maintain the "sweet spot" of training progression.

The TrainingLoad system calculates this automatically from your activity data and provides clear, actionable guidance to keep you training safely and effectively.
