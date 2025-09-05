# Training Load Calculation and Threshold Estimation Utilities
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import logging
from datetime import datetime
from streams_analysis import (
    analyze_activity_streams, 
    estimate_ftp_from_streams, 
    estimate_functional_threshold_pace_from_streams,
    estimate_running_critical_power,
    analyze_running_intensity_distribution
)

def calculate_utl(activity_summary: Dict[str, Any], threshold: Any, activity_streams: Optional[Dict] = None, wellness_data: Optional[Dict] = None) -> Tuple[float, str]:
    """
    Calculate Unit Training Load (UTL) for an activity with wellness data integration.
    
    Args:
        activity_summary: Strava activity summary data
        threshold: Threshold object with user's performance thresholds
        activity_streams: Optional detailed stream data (power, heart rate, etc.)
        wellness_data: Optional wellness data (HRV, sleep quality, readiness) for modifiers
    
    Returns:
        Tuple of (utl_score, calculation_method)
    """
    try:
        activity_type = activity_summary.get("type", "").lower()
        moving_time_seconds = activity_summary.get("moving_time", 0)
        moving_time_hours = moving_time_seconds / 3600.0
        
        if moving_time_hours == 0:
            return 0.0, "no_time"
        
        # 1. TSS (Training Stress Score) for cycling with power data
        if activity_type in ["ride", "cycling"] and activity_streams and "watts" in activity_streams:
            if threshold.ftp_watts and threshold.ftp_watts > 0:
                power_data = activity_streams["watts"]["data"]
                if power_data:
                    normalized_power = calculate_normalized_power(power_data)
                    intensity_factor = normalized_power / threshold.ftp_watts
                    tss = (moving_time_seconds * normalized_power * intensity_factor) / (threshold.ftp_watts * 36)
                    return tss, "TSS"
        
        # 2. rTSS (running Training Stress Score) for running with pace
        if activity_type in ["run", "running"]:
            if threshold.fthp_mps and threshold.fthp_mps > 0:
                distance_m = activity_summary.get("distance", 0)
                if distance_m > 0:
                    avg_pace_mps = distance_m / moving_time_seconds
                    intensity_factor = threshold.fthp_mps / avg_pace_mps  # Higher pace = higher IF
                    rtss = moving_time_hours * intensity_factor * intensity_factor * 100
                    return rtss, "rTSS"
        
        # 3. Enhanced TRIMP using heart rate zones and activity intensity
        if activity_streams and "heartrate" in activity_streams:
            if threshold.max_hr and threshold.resting_hr:
                hr_data = activity_streams["heartrate"]["data"]
                if hr_data:
                    # Use improved TRIMP calculation with activity-specific scaling
                    trimp = calculate_improved_trimp(hr_data, threshold.max_hr, threshold.resting_hr, 
                                                   moving_time_seconds, activity_type)
                    return trimp, "TRIMP"
        
        # 4. Intensity-based scoring using scientific principles
        # Avoid simple time-based scoring for activities like hiking
        
        # For running activities, use pace-based intensity if available
        if activity_type in ["run", "running"]:
            if activity_streams and "distance" in activity_streams:
                try:
                    # Analyze running intensity distribution
                    distance_data = activity_streams["distance"]["data"]
                    time_data = activity_streams.get("time", {}).get("data", list(range(len(distance_data))))
                    hr_data = activity_streams.get("heartrate", {}).get("data", None)
                    
                    intensity_analysis = analyze_running_intensity_distribution(distance_data, time_data, hr_data)
                    
                    if "intensity_classification" in intensity_analysis:
                        # Calculate UTL based on intensity distribution
                        intensity_type = intensity_analysis["intensity_classification"]
                        
                        # Science-based intensity factors
                        intensity_multipliers = {
                            "recovery": 0.5,
                            "aerobic_base": 0.8, 
                            "tempo": 1.2,
                            "high_intensity": 1.8
                        }
                        
                        multiplier = intensity_multipliers.get(intensity_type, 1.0)
                        intensity_utl = moving_time_hours * multiplier * 100
                        
                        return intensity_utl, f"running_intensity_{intensity_type}"
                except Exception as e:
                    logging.warning(f"Could not analyze running intensity: {str(e)}")
        
        # For cycling, use power zones if available
        if activity_type in ["ride", "cycling"]:
            if activity_streams and "watts" in activity_streams:
                try:
                    power_data = activity_streams["watts"]["data"]
                    if power_data and threshold.ftp_watts:
                        # Calculate normalized power and intensity factor
                        avg_power = sum(power_data) / len(power_data)
                        intensity_factor = avg_power / threshold.ftp_watts
                        
                        # TSS-like calculation: IF² × duration × 100
                        power_utl = (intensity_factor ** 2) * moving_time_hours * 100
                        
                        return power_utl, "power_intensity"
                except Exception as e:
                    logging.warning(f"Could not analyze cycling power: {str(e)}")
        
        # 5. Heart rate-based intensity for activities without specific metrics
        if activity_streams and "heartrate" in activity_streams:
            if threshold.max_hr and threshold.resting_hr:
                try:
                    hr_data = activity_streams["heartrate"]["data"]
                    if hr_data:
                        # Calculate average heart rate intensity
                        avg_hr = sum(hr_data) / len(hr_data)
                        hr_reserve = threshold.max_hr - threshold.resting_hr
                        avg_intensity = (avg_hr - threshold.resting_hr) / hr_reserve
                        
                        # Avoid high scores for low-intensity long activities
                        if avg_intensity < 0.6:  # Below 60% HRR
                            intensity_multiplier = 0.5
                        elif avg_intensity < 0.7:  # 60-70% HRR
                            intensity_multiplier = 0.8
                        elif avg_intensity < 0.8:  # 70-80% HRR
                            intensity_multiplier = 1.2
                        else:  # Above 80% HRR
                            intensity_multiplier = 1.8
                        
                        hr_utl = moving_time_hours * intensity_multiplier * 100
                        
                        return hr_utl, f"hr_intensity_{avg_intensity:.1f}"
                except Exception as e:
                    logging.warning(f"Could not analyze heart rate intensity: {str(e)}")
        
        # 6. Conservative fallback - avoid inflated scores for long, easy activities
        # Use activity type but cap the duration impact
        intensity_factors = {
            "run": 1.0,
            "running": 1.0,
            "ride": 0.9,
            "cycling": 0.9,
            "swim": 1.1,
            "swimming": 1.1,
            "hike": 0.4,  # Much lower for hiking
            "walk": 0.3,  # Much lower for walking
            "default": 0.8
        }
        
        intensity = intensity_factors.get(activity_type, intensity_factors["default"])
        
        # Cap the time factor to prevent inflated scores for very long activities
        # Use logarithmic scaling for activities over 2 hours
        if moving_time_hours > 2:
            time_factor = 2 + (moving_time_hours - 2) * 0.5  # Diminishing returns
        else:
            time_factor = moving_time_hours
            
        conservative_utl = time_factor * intensity * 100
        
        # Apply wellness modifiers if available
        if wellness_data:
            modified_utl, wellness_modifier = apply_wellness_modifiers(conservative_utl, wellness_data)
            return modified_utl, f"conservative_time_based{wellness_modifier}"
        
        return conservative_utl, "conservative_time_based"
        
    except Exception as e:
        logging.error(f"Error calculating UTL: {str(e)}")
        return 0.0, "error"


def calculate_normalized_power(power_data: List[int]) -> float:
    """Calculate Normalized Power from power data."""
    try:
        if not power_data or len(power_data) < 30:
            return np.mean(power_data) if power_data else 0
        
        # Rolling 30-second average
        rolling_avg = []
        for i in range(len(power_data) - 29):
            avg = np.mean(power_data[i:i+30])
            rolling_avg.append(avg)
        
        # Fourth power of rolling averages
        fourth_powers = [avg**4 for avg in rolling_avg]
        
        # Normalized power is the fourth root of the mean of fourth powers
        normalized_power = np.power(np.mean(fourth_powers), 0.25)
        
        return normalized_power
        
    except Exception as e:
        logging.error(f"Error calculating normalized power: {str(e)}")
        return np.mean(power_data) if power_data else 0


def calculate_trimp(hr_data: List[int], max_hr: int, resting_hr: int, duration_seconds: int) -> float:
    """Calculate TRIMP (Training Impulse) from heart rate data - Legacy method."""
    try:
        if not hr_data or max_hr <= resting_hr:
            return 0
        
        hr_reserve = max_hr - resting_hr
        avg_hr = np.mean(hr_data)
        hr_fraction = (avg_hr - resting_hr) / hr_reserve
        
        # Ensure fraction is between 0 and 1
        hr_fraction = max(0, min(1, hr_fraction))
        
        # TRIMP calculation (simplified)
        # Duration in minutes * HR fraction * exponential factor
        duration_minutes = duration_seconds / 60.0
        trimp = duration_minutes * hr_fraction * (0.64 * np.exp(1.92 * hr_fraction))
        
        return trimp
        
    except Exception as e:
        logging.error(f"Error calculating TRIMP: {str(e)}")
        return 0


def calculate_improved_trimp(hr_data: List[int], max_hr: int, resting_hr: int, duration_seconds: int, activity_type: str) -> float:
    """
    Calculate improved TRIMP with activity-specific scaling.
    
    This addresses the issue where hiking/walking activities get inflated TRIMP scores
    compared to running/cycling. Different activities have different physiological demands
    even at the same heart rate.
    """
    try:
        if not hr_data or max_hr <= resting_hr:
            return 0
        
        hr_reserve = max_hr - resting_hr
        avg_hr = np.mean(hr_data)
        hr_fraction = (avg_hr - resting_hr) / hr_reserve
        
        # Ensure fraction is between 0 and 1
        hr_fraction = max(0, min(1, hr_fraction))
        
        # Base TRIMP calculation using a more conservative exponential
        duration_minutes = duration_seconds / 60.0
        base_trimp = duration_minutes * hr_fraction * (0.5 * np.exp(1.5 * hr_fraction))
        
        # Activity-specific scaling factors based on MET values from 
        # 2024 Compendium of Physical Activities (evidence-based ratios)
        # 
        # Scientific basis:
        # - Running (6-8 mph): 9-12 METs (baseline = 10.5 average)
        # - Cycling (12-16 mph): 8-12 METs (average = 10) → 10/10.5 = 0.95
        # - Hiking general: 6 METs → 6/10.5 = 0.57 ≈ 0.55
        # - Walking brisk (3.5-4.5 mph): 5-7 METs (average = 6) → 6/10.5 = 0.57 ≈ 0.45
        # - Swimming (moderate): 8-12 METs (average = 10) → 10/10.5 = 0.95
        activity_scaling = {
            "run": 1.0,           # 9-12 METs - baseline reference
            "running": 1.0,
            "ride": 0.95,         # 8-12 METs - mechanical efficiency advantage
            "cycling": 0.95,
            "hike": 0.55,         # 6 METs general hiking (evidence-based)
            "hiking": 0.55,
            "walk": 0.45,         # 5-7 METs brisk walking (evidence-based)
            "walking": 0.45,
            "swim": 0.95,         # 8-12 METs moderate swimming
            "swimming": 0.95,
            "workout": 0.80,      # Generic strength/cross-training
            "crosstraining": 0.80,
            "elliptical": 0.70,   # Lower impact, mechanical assistance
            "alpineski": 0.90,    # Similar to cycling, equipment assistance
            "nordicski": 0.95,    # High full-body engagement
            "default": 0.75       # Conservative evidence-based default
        }
        
        scaling_factor = activity_scaling.get(activity_type, activity_scaling["default"])
        
        # Apply activity scaling
        adjusted_trimp = base_trimp * scaling_factor
        
        # Cap extremely high values (sanity check)
        # A 3-hour moderate activity should rarely exceed 200 TRIMP
        max_reasonable_trimp = duration_minutes * 1.2  # ~72 for 1 hour moderate
        adjusted_trimp = min(adjusted_trimp, max_reasonable_trimp)
        
        return adjusted_trimp
        
    except Exception as e:
        logging.error(f"Error calculating improved TRIMP: {str(e)}")
        return 0


def apply_wellness_modifiers(base_utl: float, wellness_data: Optional[Dict]) -> Tuple[float, str]:
    """
    Apply wellness data modifiers to base UTL score.
    
    Wellness factors like HRV, sleep quality, and readiness can indicate
    how much training stress the body can handle on a given day.
    """
    if not wellness_data:
        return base_utl, ""
    
    modifiers = []
    total_modifier = 1.0
    
    # HRV modifier (Heart Rate Variability)
    hrv = wellness_data.get('hrv')
    if hrv is not None:
        # HRV baseline comparison would be ideal, but for now use general ranges
        if hrv < 20:  # Low HRV suggests high stress/fatigue
            hrv_modifier = 0.8  # Reduce perceived training stress
            modifiers.append("low_hrv")
        elif hrv > 50:  # High HRV suggests good recovery
            hrv_modifier = 1.1  # Can handle slightly more stress
            modifiers.append("high_hrv")
        else:
            hrv_modifier = 1.0
        total_modifier *= hrv_modifier
    
    # Sleep quality modifier
    sleep_score = wellness_data.get('sleepScore')
    if sleep_score is not None:
        if sleep_score < 60:  # Poor sleep
            sleep_modifier = 0.85
            modifiers.append("poor_sleep")
        elif sleep_score > 85:  # Excellent sleep
            sleep_modifier = 1.05
            modifiers.append("great_sleep")
        else:
            sleep_modifier = 1.0
        total_modifier *= sleep_modifier
    
    # Readiness modifier (if available from intervals.icu)
    readiness = wellness_data.get('readiness')
    if readiness is not None:
        if readiness < 50:  # Low readiness
            readiness_modifier = 0.8
            modifiers.append("low_readiness")
        elif readiness > 80:  # High readiness
            readiness_modifier = 1.1
            modifiers.append("high_readiness")
        else:
            readiness_modifier = 1.0
        total_modifier *= readiness_modifier
    
    modified_utl = base_utl * total_modifier
    modifier_string = f"_wellness_{'_'.join(modifiers)}" if modifiers else ""
    
    return modified_utl, modifier_string


def estimate_thresholds_from_activities(activity_data: List[Dict], gender: str, activities_with_streams: Optional[List[Tuple[Dict, Dict]]] = None) -> Dict[str, Optional[float]]:
    """
    Estimate performance thresholds from recent activity data.
    Enhanced version that can use detailed streams data for more accurate estimates.
    
    Args:
        activity_data: List of activity dictionaries with performance data
        gender: User's gender for HR estimation
        activities_with_streams: Optional list of (activity_summary, streams_data) tuples
    
    Returns:
        Dictionary with estimated thresholds
    """
    try:
        # Check if activities have embedded streams data
        activities_with_embedded_streams = []
        for activity in activity_data:
            if 'streams' in activity and activity['streams']:
                activities_with_embedded_streams.append((activity, activity['streams']))
        
        # If we have streams data (either passed or embedded), use enhanced analysis
        if activities_with_streams:
            logging.info("Using enhanced threshold estimation with provided streams data")
            return enhanced_threshold_estimation(activities_with_streams, gender)
        elif activities_with_embedded_streams:
            logging.info("Using enhanced threshold estimation with embedded streams data")
            return enhanced_threshold_estimation(activities_with_embedded_streams, gender)
        
        # Fallback to original method using activity summaries only
        logging.info("Using basic threshold estimation from activity summaries")
        estimates = {
            'ftp_watts': None,
            'fthp_mps': None,
            'max_hr': None,
            'resting_hr': None
        }
        
        if not activity_data:
            return estimates
        
        # Separate activities by type
        cycling_activities = [a for a in activity_data if a.get('type', '').lower() in ['ride', 'cycling']]
        running_activities = [a for a in activity_data if a.get('type', '').lower() in ['run', 'running']]
        
        # Estimate FTP from cycling activities using proper methodology
        if cycling_activities:
            # Method 1: Find best 20+ minute average power, apply 95% factor
            best_20min_power = 0
            best_40min_power = 0
            best_60min_power = 0
            
            for activity in cycling_activities:
                avg_watts = activity.get('average_watts')
                moving_time = activity.get('moving_time', 0)
                
                if avg_watts and moving_time >= 1200:  # 20+ minutes
                    if avg_watts > best_20min_power:
                        best_20min_power = avg_watts
                        
                if avg_watts and moving_time >= 2400:  # 40+ minutes  
                    if avg_watts > best_40min_power:
                        best_40min_power = avg_watts
                        
                if avg_watts and moving_time >= 3600:  # 60+ minutes
                    if avg_watts > best_60min_power:
                        best_60min_power = avg_watts
            
            # Use best available method for FTP estimation
            if best_60min_power > 0:
                # Gold standard: 1-hour power is approximately FTP
                estimates['ftp_watts'] = best_60min_power
            elif best_40min_power > 0:
                # 40+ minute power, apply 97% factor
                estimates['ftp_watts'] = best_40min_power * 0.97
            elif best_20min_power > 0:
                # 20-minute test: apply 95% factor (most common method)
                estimates['ftp_watts'] = best_20min_power * 0.95
        
        # Estimate Functional Threshold Pace from running activities
        if running_activities:
            paces = []
            for activity in running_activities:
                distance = activity.get('distance', 0)
                moving_time = activity.get('moving_time', 0)
                if distance > 0 and moving_time > 1200:  # At least 20 mins
                    pace_mps = distance / moving_time
                    paces.append(pace_mps)
            
            if paces:
                # Estimate threshold pace as fastest sustainable pace
                estimates['fthp_mps'] = max(paces) * 0.9  # ~90% of best pace
        
        # Estimate heart rate thresholds
        all_hr_data = []
        for activity in activity_data:
            if activity.get('max_heartrate'):
                all_hr_data.append(activity['max_heartrate'])
        
        if all_hr_data:
            estimates['max_hr'] = max(all_hr_data)
            
            # Estimate resting HR (very rough approximation)
            # In practice, this should come from resting measurements
            age_estimate = 35  # Default assumption
            if gender.lower() == 'female':
                estimates['resting_hr'] = 75
            else:
                estimates['resting_hr'] = 70
        
        return estimates
        
    except Exception as e:
        logging.error(f"Error estimating thresholds: {str(e)}")
        return {
            'ftp_watts': None,
            'fthp_mps': None,
            'max_hr': None,
            'resting_hr': None
        }


def enhanced_threshold_estimation(activities_with_streams: List[Tuple[Dict, Dict]], gender: str) -> Dict[str, Optional[float]]:
    """
    Enhanced threshold estimation using detailed streams data for more accurate analysis.
    
    Args:
        activities_with_streams: List of (activity_summary, streams_data) tuples
        gender: User's gender for HR estimation
    
    Returns:
        Dictionary with estimated thresholds
    """
    estimates = {
        'ftp_watts': None,
        'fthp_mps': None,
        'max_hr': None,
        'resting_hr': None
    }
    
    try:
        best_ftp = 0
        best_fthp = 0
        max_heartrate = 0
        
        for activity_summary, streams_data in activities_with_streams:
            activity_type = activity_summary.get('type', '').lower()
            
            # Power analysis for cycling activities
            if activity_type in ['ride', 'cycling'] and 'watts' in streams_data:
                power_data = streams_data['watts']
                time_data = streams_data.get('time', list(range(len(power_data))))
                
                # Estimate FTP from this activity's streams
                ftp, method = estimate_ftp_from_streams(power_data, time_data)
                if ftp and ftp > best_ftp:
                    best_ftp = ftp
                    logging.info(f"Found better FTP estimate: {ftp:.1f}W using {method}")
            
            # Pace analysis for running activities  
            elif activity_type in ['run', 'running'] and 'distance' in streams_data:
                distance_data = streams_data['distance']
                time_data = streams_data.get('time', list(range(len(distance_data))))
                
                # Estimate functional threshold pace from this activity's streams
                fthp, method = estimate_functional_threshold_pace_from_streams(distance_data, time_data)
                if fthp and fthp > best_fthp:
                    best_fthp = fthp
                    logging.info(f"Found better FThP estimate: {fthp:.2f}m/s using {method}")
            
            # Heart rate analysis for all activities
            if 'heartrate' in streams_data:
                hr_data = streams_data['heartrate']
                if hr_data:
                    activity_max_hr = max(hr_data)
                    if activity_max_hr > max_heartrate:
                        max_heartrate = activity_max_hr
        
        # Set estimates
        if best_ftp > 0:
            estimates['ftp_watts'] = float(best_ftp)
        if best_fthp > 0:
            estimates['fthp_mps'] = float(best_fthp)
        if max_heartrate > 0:
            estimates['max_hr'] = int(max_heartrate)
            # Estimate resting HR based on max HR and gender
            if gender.upper() == 'F':
                estimates['resting_hr'] = max(50, max_heartrate - 160)
            else:
                estimates['resting_hr'] = max(45, max_heartrate - 170)
        else:
            estimates['resting_hr'] = 70
        
        return estimates
        
    except Exception as e:
        logging.error(f"Error in enhanced threshold estimation: {str(e)}")
        return estimates


def estimate_thresholds_from_activities(
    activities: List[Dict],
    gender: str,
    activities_with_streams: List[Tuple[Dict, Dict]] = None
) -> Optional[Dict]:
    """
    Estimate thresholds from activity data using stream analysis when available.
    
    Args:
        activities: List of activity summaries
        gender: User gender for HR estimation  
        activities_with_streams: List of (activity, streams) tuples for detailed analysis
    
    Returns:
        Dict with estimated thresholds or None if insufficient data
    """
    logging.info(f"Estimating thresholds from {len(activities)} activities")
    
    if not activities:
        return None
    
    # Separate by activity type
    cycling_activities = [a for a in activities if a['type'] in ['Ride', 'VirtualRide']]
    running_activities = [a for a in activities if a['type'] in ['Run', 'VirtualRun']]
    
    thresholds = {}
    
    # Estimate FTP from cycling activities
    if cycling_activities:
        ftp = estimate_ftp_from_activities(cycling_activities, activities_with_streams)
        if ftp:
            thresholds['ftp_watts'] = ftp
            logging.info(f"Estimated FTP: {ftp}W")
    
    # Estimate FTHP from running activities  
    if running_activities:
        fthp = estimate_fthp_from_activities(running_activities, activities_with_streams)
        if fthp:
            thresholds['fthp_mps'] = fthp
            logging.info(f"Estimated FTHP: {fthp:.2f} m/s")
    
    # Estimate heart rate zones from all activities
    hr_zones = estimate_hr_zones_from_activities(activities, gender, activities_with_streams)
    thresholds.update(hr_zones)
    
    return thresholds if thresholds else None


def estimate_ftp_from_activities(
    cycling_activities: List[Dict],
    activities_with_streams: List[Tuple[Dict, Dict]] = None
) -> Optional[float]:
    """
    Estimate FTP using multiple methods:
    1. Stream-based power curve analysis (best)
    2. 20-minute test detection and estimation (0.95x factor)
    3. Best 1-hour average power
    4. Statistical analysis of workout efforts
    """
    
    # Method 1: Stream-based power curve analysis
    if activities_with_streams:
        ftp_from_streams = estimate_ftp_from_power_streams(activities_with_streams)
        if ftp_from_streams:
            return ftp_from_streams
    
    # Method 2: Find structured tests or time trials
    ftp_from_tests = find_ftp_from_test_activities(cycling_activities)
    if ftp_from_tests:
        return ftp_from_tests
    
    # Method 3: Best average power analysis
    ftp_from_averages = estimate_ftp_from_average_power(cycling_activities)
    if ftp_from_averages:
        return ftp_from_averages
        
    logging.warning("Could not estimate FTP from available cycling data")
    return None


def estimate_ftp_from_power_streams(activities_with_streams: List[Tuple[Dict, Dict]]) -> Optional[float]:
    """
    Analyze power streams to build power curve and estimate FTP.
    """
    all_power_efforts = []
    
    for activity, streams in activities_with_streams:
        if activity['type'] not in ['Ride', 'VirtualRide']:
            continue
            
        watts_stream = streams.get('watts', {}).get('data', [])
        if not watts_stream or len(watts_stream) < 300:  # Need at least 5 minutes
            continue
        
        # Extract efforts of different durations
        power_efforts = extract_power_efforts(watts_stream)
        all_power_efforts.extend(power_efforts)
    
    if not all_power_efforts:
        return None
    
    # Build power curve
    power_curve = build_power_curve(all_power_efforts)
    
    # Estimate FTP as best 1-hour effort, or extrapolate from shorter efforts
    if 3600 in power_curve:  # 1-hour effort available
        return power_curve[3600]
    elif 2700 in power_curve and power_curve[2700] > 100:  # 45-min effort
        return power_curve[2700] * 0.95
    elif 1200 in power_curve and power_curve[1200] > 150:  # 20-min effort  
        return power_curve[1200] * 0.95
    elif 300 in power_curve and power_curve[300] > 200:  # 5-min effort
        return power_curve[300] * 0.85
    
    return None


def extract_power_efforts(watts_stream: List[float]) -> List[Dict]:
    """
    Extract best efforts of various durations from a power stream.
    """
    if not watts_stream:
        return []
    
    watts_array = np.array(watts_stream)
    efforts = []
    
    # Standard durations for power curve (seconds)
    durations = [30, 60, 120, 300, 480, 600, 900, 1200, 1800, 2700, 3600]
    
    for duration in durations:
        if len(watts_array) < duration:
            continue
            
        # Calculate rolling average for this duration using numpy for efficiency
        if len(watts_array) >= duration:
            # Use convolution for fast rolling average
            kernel = np.ones(duration) / duration
            rolling_avg = np.convolve(watts_array, kernel, mode='valid')
            
            # Find best effort
            best_power = np.max(rolling_avg)
            if best_power > 50:  # Reasonable minimum power
                efforts.append({
                    'duration': duration,
                    'power': best_power,
                    'timestamp': datetime.now() if 'datetime' in globals() else None
                })
    
    return efforts


def build_power_curve(efforts: List[Dict]) -> Dict[int, float]:
    """
    Build power curve from best efforts, taking the best power for each duration.
    """
    power_curve = {}
    
    # Group efforts by duration and take the maximum
    for effort in efforts:
        duration = effort['duration']
        power = effort['power']
        
        if duration not in power_curve or power > power_curve[duration]:
            power_curve[duration] = power
    
    return power_curve


def find_ftp_from_test_activities(cycling_activities: List[Dict]) -> Optional[float]:
    """
    Look for FTP test activities based on name patterns and duration.
    """
    test_keywords = ['ftp', 'test', '20 min', '20min', 'threshold', 'tt', 'time trial']
    
    for activity in cycling_activities:
        activity_name = activity.get('name', '').lower()
        moving_time = activity.get('moving_time', 0)
        avg_watts = activity.get('average_watts')
        
        # Check if this looks like an FTP test
        is_test_by_name = any(keyword in activity_name for keyword in test_keywords)
        is_20_min_effort = 1100 <= moving_time <= 1400  # 18-23 minutes
        
        if (is_test_by_name or is_20_min_effort) and avg_watts and avg_watts > 100:
            # Apply appropriate factor
            if is_20_min_effort or '20' in activity_name:
                estimated_ftp = avg_watts * 0.95
            else:
                estimated_ftp = avg_watts  # Assume it's already threshold power
            
            logging.info(f"Found FTP test activity: {activity_name}, {avg_watts}W avg -> {estimated_ftp}W FTP")
            return estimated_ftp
    
    return None


def estimate_ftp_from_average_power(cycling_activities: List[Dict]) -> Optional[float]:
    """
    Estimate FTP from best average power efforts of different durations.
    """
    long_efforts = []
    
    for activity in cycling_activities:
        moving_time = activity.get('moving_time', 0)
        avg_watts = activity.get('average_watts')
        
        # Look for efforts 30+ minutes with reasonable power
        if moving_time >= 1800 and avg_watts and avg_watts > 100:
            # Estimate FTP based on effort duration
            if moving_time >= 3600:  # 1+ hour
                ftp_factor = 1.0
            elif moving_time >= 2700:  # 45+ minutes
                ftp_factor = 0.97
            elif moving_time >= 1800:  # 30+ minutes  
                ftp_factor = 0.93
            else:
                continue
            
            estimated_ftp = avg_watts * ftp_factor
            long_efforts.append(estimated_ftp)
    
    if long_efforts:
        # Take the best effort as FTP estimate
        return max(long_efforts)
    
    return None


def estimate_fthp_from_activities(
    running_activities: List[Dict],
    activities_with_streams: List[Tuple[Dict, Dict]] = None
) -> Optional[float]:
    """
    Estimate Functional Threshold Heart Rate Pace (FTHP) for running.
    """
    
    # Method 1: Stream-based critical speed analysis
    if activities_with_streams:
        fthp_from_streams = estimate_fthp_from_pace_streams(activities_with_streams)
        if fthp_from_streams:
            return fthp_from_streams
    
    # Method 2: Threshold run detection
    fthp_from_tests = find_fthp_from_test_activities(running_activities)
    if fthp_from_tests:
        return fthp_from_tests
    
    # Method 3: Statistical analysis of tempo/threshold efforts
    fthp_from_tempo = estimate_fthp_from_tempo_runs(running_activities)
    if fthp_from_tempo:
        return fthp_from_tempo
        
    logging.warning("Could not estimate FTHP from available running data")
    return None


def estimate_fthp_from_pace_streams(activities_with_streams: List[Tuple[Dict, Dict]]) -> Optional[float]:
    """
    Analyze velocity streams to estimate critical speed (FTHP).
    """
    all_pace_efforts = []
    
    for activity, streams in activities_with_streams:
        if activity['type'] not in ['Run', 'VirtualRun']:
            continue
            
        velocity_stream = streams.get('velocity_smooth', {}).get('data', [])
        if not velocity_stream or len(velocity_stream) < 300:  # Need at least 5 minutes
            continue
        
        # Extract pace efforts of different durations
        pace_efforts = extract_pace_efforts(velocity_stream)
        all_pace_efforts.extend(pace_efforts)
    
    if not all_pace_efforts:
        return None
    
    # Build critical speed curve
    speed_curve = build_speed_curve(all_pace_efforts)
    
    # Estimate FTHP as best 1-hour pace, or extrapolate
    if 3600 in speed_curve:  # 1-hour effort
        return speed_curve[3600]
    elif 2700 in speed_curve and speed_curve[2700] > 2.0:  # 45-min effort
        return speed_curve[2700] * 0.97
    elif 1800 in speed_curve and speed_curve[1800] > 2.5:  # 30-min effort
        return speed_curve[1800] * 0.95
    elif 1200 in speed_curve and speed_curve[1200] > 3.0:  # 20-min effort
        return speed_curve[1200] * 0.93
    
    return None


def extract_pace_efforts(velocity_stream: List[float]) -> List[Dict]:
    """
    Extract best pace efforts from velocity stream.
    """
    if not velocity_stream:
        return []
    
    velocity_array = np.array(velocity_stream)
    efforts = []
    
    # Standard durations for pace curve (seconds)
    durations = [300, 600, 900, 1200, 1800, 2700, 3600]
    
    for duration in durations:
        if len(velocity_array) < duration:
            continue
            
        # Calculate rolling average using numpy for efficiency
        if len(velocity_array) >= duration:
            kernel = np.ones(duration) / duration
            rolling_avg = np.convolve(velocity_array, kernel, mode='valid')
            
            # Find best effort (highest average speed)
            best_speed = np.max(rolling_avg)
            if best_speed > 1.0:  # Reasonable minimum speed
                efforts.append({
                    'duration': duration,
                    'speed': best_speed,
                    'timestamp': datetime.now() if 'datetime' in globals() else None
                })
    
    return efforts


def build_speed_curve(efforts: List[Dict]) -> Dict[int, float]:
    """
    Build critical speed curve from best efforts.
    """
    speed_curve = {}
    
    for effort in efforts:
        duration = effort['duration']
        speed = effort['speed']
        
        if duration not in speed_curve or speed > speed_curve[duration]:
            speed_curve[duration] = speed
    
    return speed_curve


def find_fthp_from_test_activities(running_activities: List[Dict]) -> Optional[float]:
    """
    Look for threshold test runs based on name patterns.
    """
    test_keywords = ['threshold', 'tempo', 'test', 'tt', 'time trial', 'fthp', 'lactate']
    
    for activity in running_activities:
        activity_name = activity.get('name', '').lower()
        moving_time = activity.get('moving_time', 0)
        avg_speed = activity.get('average_speed')
        
        # Check if this looks like a threshold test
        is_test_by_name = any(keyword in activity_name for keyword in test_keywords)
        is_threshold_duration = 1200 <= moving_time <= 3600  # 20-60 minutes
        
        if (is_test_by_name or is_threshold_duration) and avg_speed and avg_speed > 2.0:
            # Threshold runs are typically at threshold pace already
            estimated_fthp = avg_speed
            logging.info(f"Found threshold run: {activity_name}, {avg_speed:.2f}m/s -> {estimated_fthp:.2f}m/s FTHP")
            return estimated_fthp
    
    return None


def estimate_fthp_from_tempo_runs(running_activities: List[Dict]) -> Optional[float]:
    """
    Estimate FTHP from tempo/threshold efforts.
    """
    tempo_efforts = []
    
    for activity in running_activities:
        moving_time = activity.get('moving_time', 0)
        avg_speed = activity.get('average_speed')
        
        # Look for tempo runs (20-60 minutes at steady effort)
        if 1200 <= moving_time <= 3600 and avg_speed and avg_speed > 2.5:
            tempo_efforts.append(avg_speed)
    
    if tempo_efforts:
        # Take median of tempo efforts as FTHP estimate
        return np.median(tempo_efforts)
    
    return None


def estimate_hr_zones_from_activities(
    activities: List[Dict],
    gender: str,
    activities_with_streams: List[Tuple[Dict, Dict]] = None
) -> Dict[str, int]:
    """
    Estimate heart rate zones from activity data.
    """
    all_hr_values = []
    max_hr_observed = 0
    
    # Collect HR data from activities
    for activity in activities:
        max_hr = activity.get('max_heartrate')
        if max_hr and max_hr > max_hr_observed:
            max_hr_observed = max_hr
    
    # Collect HR data from streams if available
    if activities_with_streams:
        for activity, streams in activities_with_streams:
            hr_stream = streams.get('heartrate', {}).get('data', [])
            if hr_stream:
                all_hr_values.extend([hr for hr in hr_stream if hr > 60 and hr < 220])
                stream_max = max(hr_stream) if hr_stream else 0
                if stream_max > max_hr_observed:
                    max_hr_observed = stream_max
    
    # Estimate age from max HR if not enough data
    if not max_hr_observed or max_hr_observed < 120:
        # Default age-based estimation
        estimated_age = 35  # Default assumption
        max_hr_observed = 220 - estimated_age
        logging.warning(f"Using age-based max HR estimate: {max_hr_observed}")
    
    # Estimate resting HR from lowest observed values
    resting_hr = 60  # Default
    if all_hr_values:
        # Take 5th percentile as resting HR estimate
        resting_hr = max(int(np.percentile(all_hr_values, 5)), 40)
    
    return {
        'max_hr': max_hr_observed,
        'resting_hr': resting_hr
    }
