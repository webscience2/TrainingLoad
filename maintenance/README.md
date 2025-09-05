# Maintenance Scripts

This directory contains one-time setup, migration, and maintenance scripts that were used during development and system updates.

## Scripts

### `recalculate_utl_with_new_thresholds.py`
**Purpose**: One-time recalculation of historical UTL scores with stream-based thresholds
- Used after implementing the research-based threshold calculation system
- Recalculated all 87 activities with corrected FTP/FTHP values
- Resulted in +222% total UTL increase due to more accurate thresholds

**Historical Context**: This was run after discovering that original thresholds were significantly underestimated (FTP was 42W too low, running threshold 0.55 m/s too slow).

### `update_stream_based_thresholds.py`
**Purpose**: One-time update of user thresholds based on stream analysis findings
- Applied discovered stream analysis results to update database thresholds
- Updated FTP from 155W to 197W (+42W, 27.1% increase)
- Updated FTHP from 2.81 to 3.36 m/s (pace improvement from 5.9 to 5.0 min/km)

**Historical Context**: This was the initial threshold correction based on "Road to Sky in Watopia" 207W best 20-min power analysis.

### `recalculate_utl.py`
**Purpose**: Earlier version of UTL recalculation with corrected FTP
- Legacy script for FTP-based UTL recalculation
- Superseded by the more comprehensive `recalculate_utl_with_new_thresholds.py`

## Usage

⚠️ **Warning**: These are one-time migration scripts that have already been executed. Running them again may cause data inconsistencies.

```bash
# Historical usage (DO NOT re-run):
python maintenance/update_stream_based_thresholds.py
python maintenance/recalculate_utl_with_new_thresholds.py
```

## Status

✅ **COMPLETED** - All scripts have been successfully executed and their changes are now integrated into the main system.

The functionality from these maintenance scripts is now part of the core application:
- **Stream-based threshold calculation**: Integrated into `backend/research_threshold_calculator.py`
- **Automatic threshold updates**: Part of Strava sync process in `backend/activities.py`
- **New user onboarding**: Uses research-based methods in `backend/onboarding.py`

## Historical Significance

These scripts represent key milestones in the system development:

1. **Discovery Phase**: Initial analysis revealed massive threshold underestimation
2. **Correction Phase**: Stream-based analysis provided accurate threshold values  
3. **Integration Phase**: Research-based methods integrated into core application
4. **Migration Phase**: Historical data updated with corrected calculations

The results of these scripts led to a 222% increase in total UTL scores, reflecting more accurate training load assessment.
