# TrainingLoad Codebase Cleanup Summary

## Overview
Performed comprehensive cleanup of analysis, debug, and test scripts that were scattered throughout the root directory. The goal was to maintain only core application files in the root while properly organizing development/maintenance tools.

## Files Cleaned Up

### 🗑️ **Deleted (Empty/Obsolete Files)**
- `test_new_utl.py` - Empty file
- `validate_scientific_scaling.py` - Empty file  
- `recalculate_utl.py` - Empty file
- `update_scientific_utl.py` - Empty file
- `fix_localStorage.js` - Empty file
- `intervals_icu_integration.html` - Empty file
- `fix_strava_link.sql` - Empty file

### 🗂️ **Moved to tests/ Directory**
- `check_schema.py` → `tests/check_schema.py` (updated version)
- `debug_running_streams.py` → `tests/debug_running_streams.py` (updated version)
- `test_new_user_thresholds.py` → `tests/test_new_user_thresholds.py`

### 🗑️ **Removed (Duplicates Already in tests/)**
- `analyze_thresholds.py` (identical to tests/ version)
- `analyze_running_streams.py` (identical to tests/ version) 
- `analyze_power_streams.py` (identical to tests/ version)
- `analyze_ftp_12_months.py` (identical to tests/ version)
- `analyze_thresholds_simple.py` (identical to tests/ version)

### 📦 **Archived**
- `web/` directory → `archive/old_web_frontend/`
  - Old "AthletaSync" frontend (5 HTML/JS/CSS files)
  - No longer used since React frontend was implemented
  - Preserved in archive for reference

## Current Root Directory Structure

### ✅ **Core Application Files (Kept)**
```
./backend/              # Main application backend
./frontend/             # React frontend application  
./background_processor.py  # Background processing system
./service_manager.py    # Service management utility
./setup_cron.py         # Deployment/setup script
```

### ✅ **Development/Operations Files (Kept)**
```
./tests/                # All test and analysis scripts
./maintenance/          # Maintenance scripts
./docs/                 # Documentation
./analysis/             # Research documentation
./archive/              # Archived old code
./logs/                 # Application logs
./tl                    # Management script
./start.sh, stop.sh     # Service control scripts  
./logs.sh               # Log viewing script
./maintenance.sh        # Maintenance operations
```

### ✅ **Configuration Files (Kept)**
```
./.env                  # Environment variables
./package.json          # Node.js dependencies
./pyproject.toml        # Python project config
./db_schema.sql         # Database schema
./README.md             # Project documentation
```

## Benefits of Cleanup

1. **🎯 Clarity**: Root directory now contains only core application files
2. **📁 Organization**: Development tools properly organized in subdirectories
3. **🚀 Deployment**: Easier to identify what needs to be deployed vs development tools
4. **🧹 Maintenance**: No more confusion about duplicate/obsolete scripts
5. **📚 Documentation**: Clear separation between app code and analysis tools

## File Count Summary

| Directory | Python Files | Purpose |
|-----------|-------------|----------|
| **Root** | 3 | Core application services |
| **backend/** | ~15 | Main application backend |
| **frontend/src/** | ~10 | React frontend components |
| **tests/** | ~15 | Analysis, debug, and test scripts |
| **maintenance/** | ~5 | Database maintenance scripts |

## Recommendation for Future

- **New analysis scripts** → Add to `tests/` directory
- **New maintenance scripts** → Add to `maintenance/` directory  
- **New deployment scripts** → Keep in root only if essential for operations
- **Experimental features** → Use `archive/experiments/` for temporary work

This cleanup significantly improves the project's maintainability and makes it easier for new developers to understand the codebase structure.
