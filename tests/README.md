# Tests Directory

This directory contains all testing, validation, and debugging scripts for the TrainingLoad system.

## Test Scripts

### `test_new_user_thresholds.py`
**Purpose**: Validates the research-based threshold calculation system for new users
- Tests the `calculate_initial_thresholds_for_new_user()` function
- Verifies stream-based FTP and FTHP estimation accuracy
- Confirms heart rate threshold calculation

**Usage**: 
```bash
python tests/test_new_user_thresholds.py
```

### `test_new_utl.py`
**Purpose**: Tests the wellness-enhanced UTL calculation system
- Validates UTL calculations with wellness data integration
- Tests improved TRIMP scoring for different activity types
- Verifies UTL calculation accuracy across various scenarios

**Usage**:
```bash
python tests/test_new_utl.py
```

## Validation Scripts

### `validate_scientific_scaling.py`
**Purpose**: Validates evidence-based TRIMP scaling factors against scientific literature
- Tests scaling factors against 2024 Compendium of Physical Activities
- Ensures TRIMP calculations reflect proper physiological demands
- Validates MET-based activity scaling

**Usage**:
```bash
python tests/validate_scientific_scaling.py
```

### `update_scientific_utl.py`
**Purpose**: Updates existing UTL calculations with evidence-based scaling factors
- Recalculates UTL scores for all activities using scientifically-validated scaling
- Updates database with improved TRIMP calculations
- Provides before/after comparison of UTL changes

**Usage**:
```bash
python tests/update_scientific_utl.py
```

## Debugging Scripts

### `debug_running_streams.py`
**Purpose**: Debug running threshold calculation issues
- Analyzes running activity stream data quality
- Identifies issues with velocity/pace data
- Helps troubleshoot threshold calculation problems

**Usage**:
```bash
python tests/debug_running_streams.py
```

### `check_schema.py`
**Purpose**: Database schema validation
- Checks database table structures
- Validates column types and constraints
- Ensures database integrity

**Usage**:
```bash
python tests/check_schema.py
```

## Analysis & Research Scripts

### `analyze_power_streams.py`
**Purpose**: Analyze detailed power streams from cycling activities
- Finds true 20-minute power efforts using sliding window analysis
- Research tool used to discover accurate FTP values
- Historical significance: Found 207W best power vs 155W estimated FTP

### `analyze_running_streams.py`
**Purpose**: Analyze detailed pace/speed streams from running activities
- Finds sustained pace efforts for threshold estimation
- Research tool for running threshold discovery
- Used sliding window analysis on velocity_smooth data

### `analyze_thresholds.py` & `analyze_thresholds_simple.py`
**Purpose**: Comprehensive threshold analysis and validation
- Compares current thresholds against recent activity performance
- Provides recommendations for threshold adjustments
- Shows activity distribution and performance trends

### `analyze_ftp_12_months.py`
**Purpose**: Long-term FTP analysis across 12 months of data
- Tracks FTP progression over extended periods
- Identifies performance trends and seasonal variations
- Historical analysis tool for threshold validation

## Running All Tests

To run the complete test suite:

```bash
# From the TrainingLoad root directory
python tests/test_new_user_thresholds.py
python tests/test_new_utl.py
python tests/validate_scientific_scaling.py
python tests/update_scientific_utl.py
```

## Test Categories

### 🔬 **Core System Tests**
- `test_new_user_thresholds.py` - New user onboarding threshold calculation
- `test_new_utl.py` - UTL calculation with wellness integration

### ✅ **Validation Tests** 
- `validate_scientific_scaling.py` - Scientific literature compliance
- `update_scientific_utl.py` - UTL calculation updates with evidence-based scaling

### 🐛 **Debug Tools**
- `debug_running_streams.py` - Stream data analysis
- `check_schema.py` - Database schema validation

### 🔬 **Research & Analysis Tools**
- `analyze_power_streams.py` - Cycling power stream analysis (FTP discovery)
- `analyze_running_streams.py` - Running pace stream analysis (threshold discovery)  
- `analyze_thresholds.py` - Comprehensive threshold validation
- `analyze_thresholds_simple.py` - Simplified threshold analysis
- `analyze_ftp_12_months.py` - Long-term FTP trend analysis

## Prerequisites

All test scripts require:
- Active Python virtual environment
- Database connection (PostgreSQL)
- Required dependencies installed (`pip install -r requirements.txt`)

## Notes

- Tests use the existing database and user data
- No destructive operations are performed
- All scripts include error handling and detailed logging
- Path imports are configured to work from the TrainingLoad root directory
