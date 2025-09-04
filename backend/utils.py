# Training Load Calculation and Threshold Estimation Utilities
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import logging
from streams_analysis import (
    analyze_activity_streams, 
    estimate_ftp_from_streams, 
    estimate_functional_threshold_pace_from_streams,
    estimate_running_critical_power,
    analyze_running_intensity_distribution
)

def calculate_utl(activity_summary: Dict[str, Any], threshold: Any, activity_streams: Optional[Dict] = None) -> Tuple[float, str]:
    """
    Calculate Unit Training Load (UTL) for an activity.
    
    Args:
        activity_summary: Strava activity summary data
        threshold: Threshold object with user's performance thresholds
        activity_streams: Optional detailed stream data (power, heart rate, etc.)
    
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
                    trimp = calculate_trimp(hr_data, threshold.max_hr, threshold.resting_hr, moving_time_seconds)
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
    """Calculate TRIMP (Training Impulse) from heart rate data."""
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
