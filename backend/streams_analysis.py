# Advanced Streams Analysis for Sliding Window Power/Pace Analysis
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import logging

def find_best_power_effort(power_data: List[int], time_data: List[int], duration_minutes: int) -> Tuple[float, int, int]:
    """
    Find the best sustained power effort over a given duration using sliding window analysis.
    
    Args:
        power_data: List of power values in watts
        time_data: List of time values in seconds
        duration_minutes: Target duration in minutes
        
    Returns:
        Tuple of (best_average_power, start_index, end_index)
    """
    try:
        if not power_data or not time_data or len(power_data) != len(time_data):
            return 0.0, 0, 0
            
        if len(power_data) < 2:
            return float(power_data[0]) if power_data else 0.0, 0, 0
            
        duration_seconds = duration_minutes * 60
        best_power = 0.0
        best_start = 0
        best_end = 0
        
        # Sliding window approach
        for start_idx in range(len(time_data)):
            start_time = time_data[start_idx]
            target_end_time = start_time + duration_seconds
            
            # Find the end index for this duration
            end_idx = start_idx
            for i in range(start_idx, len(time_data)):
                if time_data[i] >= target_end_time:
                    end_idx = i
                    break
                end_idx = i
            
            # Calculate average power for this window
            if end_idx > start_idx:
                actual_duration = time_data[end_idx] - time_data[start_idx]
                if actual_duration >= duration_seconds * 0.95:  # At least 95% of target duration
                    window_power = power_data[start_idx:end_idx + 1]
                    avg_power = np.mean([p for p in window_power if p > 0])  # Exclude zero power
                    
                    if avg_power > best_power:
                        best_power = avg_power
                        best_start = start_idx
                        best_end = end_idx
        
        return best_power, best_start, best_end
        
    except Exception as e:
        logging.error(f"Error finding best power effort: {str(e)}")
        return 0.0, 0, 0


def find_best_pace_effort(distance_data: List[float], time_data: List[int], duration_minutes: int) -> Tuple[float, int, int]:
    """
    Find the best sustained pace effort over a given duration using sliding window analysis.
    
    Args:
        distance_data: List of distance values in meters
        time_data: List of time values in seconds
        duration_minutes: Target duration in minutes
        
    Returns:
        Tuple of (best_pace_mps, start_index, end_index)
    """
    try:
        if not distance_data or not time_data or len(distance_data) != len(time_data):
            return 0.0, 0, 0
            
        if len(distance_data) < 2:
            return 0.0, 0, 0
            
        duration_seconds = duration_minutes * 60
        best_pace = 0.0
        best_start = 0
        best_end = 0
        
        # Sliding window approach
        for start_idx in range(len(time_data)):
            start_time = time_data[start_idx]
            target_end_time = start_time + duration_seconds
            
            # Find the end index for this duration
            end_idx = start_idx
            for i in range(start_idx, len(time_data)):
                if time_data[i] >= target_end_time:
                    end_idx = i
                    break
                end_idx = i
            
            # Calculate pace for this window
            if end_idx > start_idx:
                actual_duration = time_data[end_idx] - time_data[start_idx]
                if actual_duration >= duration_seconds * 0.95:  # At least 95% of target duration
                    distance_covered = distance_data[end_idx] - distance_data[start_idx]
                    if distance_covered > 0:
                        pace_mps = distance_covered / actual_duration
                        
                        if pace_mps > best_pace:
                            best_pace = pace_mps
                            best_start = start_idx
                            best_end = end_idx
        
        return best_pace, best_start, best_end
        
    except Exception as e:
        logging.error(f"Error finding best pace effort: {str(e)}")
        return 0.0, 0, 0


def estimate_ftp_from_streams(power_data: List[int], time_data: List[int]) -> Tuple[Optional[float], str]:
    """
    Estimate FTP using proper sliding window analysis of power streams.
    
    Args:
        power_data: List of power values in watts
        time_data: List of time values in seconds
        
    Returns:
        Tuple of (estimated_ftp, method_used)
    """
    try:
        if not power_data or not time_data:
            return None, "no_data"
            
        # Try different duration methods in order of preference
        
        # Method 1: 60-minute power (gold standard)
        best_60min, _, _ = find_best_power_effort(power_data, time_data, 60)
        if best_60min > 50:  # Reasonable minimum threshold
            return best_60min, "60min_power"
            
        # Method 2: 40-minute power with 97% factor
        best_40min, _, _ = find_best_power_effort(power_data, time_data, 40)
        if best_40min > 50:
            return best_40min * 0.97, "40min_power_adjusted"
            
        # Method 3: 20-minute power with 95% factor (most common)
        best_20min, _, _ = find_best_power_effort(power_data, time_data, 20)
        if best_20min > 50:
            return best_20min * 0.95, "20min_test"
            
        # Method 4: 10-minute power with 90% factor (less accurate)
        best_10min, _, _ = find_best_power_effort(power_data, time_data, 10)
        if best_10min > 50:
            return best_10min * 0.90, "10min_power_adjusted"
            
        # Method 5: 5-minute power with 85% factor (rough estimate)
        best_5min, _, _ = find_best_power_effort(power_data, time_data, 5)
        if best_5min > 50:
            return best_5min * 0.85, "5min_power_adjusted"
            
        return None, "insufficient_data"
        
    except Exception as e:
        logging.error(f"Error estimating FTP from streams: {str(e)}")
        return None, "error"


def estimate_functional_threshold_pace_from_streams(distance_data: List[float], time_data: List[int]) -> Tuple[Optional[float], str]:
    """
    Estimate Functional Threshold Pace using sliding window analysis.
    Based on running science - uses multiple methods for accurate threshold estimation.
    
    Running Science Methods:
    1. 60-min pace (threshold pace) - gold standard
    2. 30-min pace × 0.97 (30-min test with lactate threshold correction)
    3. 20-min pace × 0.95 (similar to cycling 20-min test)
    4. 10K pace × 0.98 (for shorter high-intensity efforts)
    
    Args:
        distance_data: List of cumulative distance values in meters
        time_data: List of time values in seconds
        
    Returns:
        Tuple of (estimated_threshold_pace_mps, method_used)
    """
    try:
        if not distance_data or not time_data or len(distance_data) != len(time_data):
            return None, "insufficient_data"
        
        # Method 1: 60-minute pace (threshold pace - gold standard)
        best_60min_pace, _, _ = find_best_pace_effort(distance_data, time_data, 60)
        if best_60min_pace > 2.0:  # Reasonable minimum (2 m/s ≈ 8:20/mile pace)
            return best_60min_pace, "60min_threshold"
        
        # Method 2: 30-minute pace with 97% factor (lactate threshold estimation)
        best_30min_pace, _, _ = find_best_pace_effort(distance_data, time_data, 30)
        if best_30min_pace > 2.2:  # Reasonable minimum for 30-min effort
            threshold_pace = best_30min_pace * 0.97
            return threshold_pace, "30min_test"
        
        # Method 3: 20-minute pace with 95% factor
        best_20min_pace, _, _ = find_best_pace_effort(distance_data, time_data, 20)
        if best_20min_pace > 2.5:  # Reasonable minimum for 20-min effort
            threshold_pace = best_20min_pace * 0.95
            return threshold_pace, "20min_test"
        
        # Method 4: 10K pace estimation (typical 10K is ~35-50 minutes, use 98% factor)
        # Look for best 40-minute effort as proxy for 10K pace
        best_40min_pace, _, _ = find_best_pace_effort(distance_data, time_data, 40)
        if best_40min_pace > 2.8:  # Reasonable minimum for 10K effort
            threshold_pace = best_40min_pace * 0.98
            return threshold_pace, "10k_pace"
        
        # Fallback: Use best available sustained pace with conservative factor
        activity_duration_min = max(time_data) / 60
        if activity_duration_min >= 15:
            # Use 15-minute best with very conservative factor
            best_15min_pace, _, _ = find_best_pace_effort(distance_data, time_data, 15)
            if best_15min_pace > 3.0:
                threshold_pace = best_15min_pace * 0.90  # Very conservative
                return threshold_pace, "15min_conservative"
        
        return None, "no_suitable_efforts"
        
    except Exception as e:
        logging.error(f"Error estimating functional threshold pace: {str(e)}")
        return None, "error"


def estimate_running_critical_power(distance_data: List[float], time_data: List[int]) -> Tuple[Optional[float], str]:
    """
    Estimate Critical Power for running using Power-Duration model.
    This is similar to cycling CP but adapted for running pace/power relationship.
    
    Critical Power in running represents the highest sustainable power output
    and correlates strongly with lactate threshold and functional threshold pace.
    
    Args:
        distance_data: List of cumulative distance values in meters  
        time_data: List of time values in seconds
        
    Returns:
        Tuple of (critical_pace_mps, method_used)
    """
    try:
        # Collect best efforts at different durations for power-duration modeling
        durations = [5, 10, 15, 20, 30, 40, 60]  # minutes
        efforts = []
        
        for duration in durations:
            pace, _, _ = find_best_pace_effort(distance_data, time_data, duration)
            if pace > 1.0:  # Valid pace
                efforts.append((duration * 60, pace))  # Convert to seconds
        
        if len(efforts) < 3:
            return None, "insufficient_efforts"
        
        # For simplicity, use the scientifically validated approach:
        # Critical pace ≈ best 60-minute pace, or 97% of best 30-minute pace
        
        best_60min = None
        best_30min = None
        
        for duration_sec, pace in efforts:
            if duration_sec >= 3600:  # 60+ minutes
                if best_60min is None or pace > best_60min:
                    best_60min = pace
            elif duration_sec >= 1800:  # 30+ minutes
                if best_30min is None or pace > best_30min:
                    best_30min = pace
        
        if best_60min:
            return best_60min, "60min_critical_pace"
        elif best_30min:
            return best_30min * 0.97, "30min_critical_pace"
        
        return None, "no_long_efforts"
        
    except Exception as e:
        logging.error(f"Error estimating running critical power: {str(e)}")
        return None, "error"


def analyze_running_intensity_distribution(distance_data: List[float], time_data: List[int], heartrate_data: List[int] = None) -> Dict[str, float]:
    """
    Analyze running intensity distribution using pace zones.
    This provides better activity classification than simple time-based scoring.
    
    Pace Zones (based on threshold pace):
    Zone 1: Recovery/Easy (< 81% threshold pace)
    Zone 2: Aerobic/Base (81-89% threshold pace) 
    Zone 3: Tempo (90-94% threshold pace)
    Zone 4: Lactate Threshold (95-105% threshold pace)
    Zone 5: VO2 Max (106-120% threshold pace)
    Zone 6: Neuromuscular (> 120% threshold pace)
    
    Args:
        distance_data: List of cumulative distance values
        time_data: List of time values  
        heartrate_data: Optional heart rate data
        
    Returns:
        Dictionary with intensity distribution percentages
    """
    try:
        # First estimate threshold pace for this activity
        threshold_pace, _ = estimate_functional_threshold_pace_from_streams(distance_data, time_data)
        
        if not threshold_pace:
            return {"error": "Could not determine threshold pace"}
        
        # Calculate instantaneous pace for each data point
        instantaneous_paces = []
        for i in range(1, len(distance_data)):
            distance_diff = distance_data[i] - distance_data[i-1]
            time_diff = time_data[i] - time_data[i-1]
            if time_diff > 0:
                pace = distance_diff / time_diff
                instantaneous_paces.append(pace)
            else:
                instantaneous_paces.append(0)
        
        if not instantaneous_paces:
            return {"error": "Could not calculate pace data"}
        
        # Classify each data point into intensity zones
        zone_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        total_points = len(instantaneous_paces)
        
        for pace in instantaneous_paces:
            if pace > 0:
                intensity_percent = (pace / threshold_pace) * 100
                
                if intensity_percent < 81:
                    zone_counts[1] += 1
                elif intensity_percent < 89:
                    zone_counts[2] += 1  
                elif intensity_percent < 94:
                    zone_counts[3] += 1
                elif intensity_percent < 105:
                    zone_counts[4] += 1
                elif intensity_percent < 120:
                    zone_counts[5] += 1
                else:
                    zone_counts[6] += 1
        
        # Convert to percentages
        zone_distribution = {}
        for zone, count in zone_counts.items():
            zone_distribution[f"zone_{zone}_percent"] = (count / total_points) * 100
        
        # Add intensity classification
        zone_4_5_6 = zone_distribution["zone_4_percent"] + zone_distribution["zone_5_percent"] + zone_distribution["zone_6_percent"]
        
        if zone_4_5_6 > 30:
            intensity_type = "high_intensity"
        elif zone_distribution["zone_3_percent"] > 20:
            intensity_type = "tempo"
        elif zone_distribution["zone_2_percent"] > 60:
            intensity_type = "aerobic_base"
        else:
            intensity_type = "recovery"
        
        zone_distribution["intensity_classification"] = intensity_type
        zone_distribution["threshold_pace_mps"] = threshold_pace
        
        return zone_distribution
        
    except Exception as e:
        logging.error(f"Error analyzing running intensity distribution: {str(e)}")
        return {"error": str(e)}


def analyze_activity_streams(activity_streams: Dict) -> Dict[str, Any]:
    """
    Comprehensive analysis of activity streams data.
    
    Args:
        activity_streams: Strava streams data
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "power_analysis": None,
        "pace_analysis": None,
        "heart_rate_analysis": None,
        "estimated_ftp": None,
        "estimated_fthp": None
    }
    
    try:
        # Power analysis
        if "watts" in activity_streams and "time" in activity_streams:
            power_data = activity_streams["watts"]["data"]
            time_data = activity_streams["time"]["data"]
            
            if power_data and time_data:
                # Find best efforts for common durations
                power_analysis = {}
                for duration in [5, 10, 20, 40, 60]:
                    best_power, start_idx, end_idx = find_best_power_effort(power_data, time_data, duration)
                    if best_power > 0:
                        power_analysis[f"best_{duration}min"] = {
                            "power": best_power,
                            "start_time": time_data[start_idx] if start_idx < len(time_data) else 0,
                            "end_time": time_data[end_idx] if end_idx < len(time_data) else 0
                        }
                
                analysis["power_analysis"] = power_analysis
                
                # Estimate FTP
                ftp, method = estimate_ftp_from_streams(power_data, time_data)
                if ftp:
                    analysis["estimated_ftp"] = {"value": ftp, "method": method}
        
        # Pace analysis
        if "distance" in activity_streams and "time" in activity_streams:
            distance_data = activity_streams["distance"]["data"]
            time_data = activity_streams["time"]["data"]
            
            if distance_data and time_data:
                # Find best pace efforts
                pace_analysis = {}
                for duration in [5, 10, 20, 30, 60]:
                    best_pace, start_idx, end_idx = find_best_pace_effort(distance_data, time_data, duration)
                    if best_pace > 0:
                        pace_analysis[f"best_{duration}min"] = {
                            "pace_mps": best_pace,
                            "pace_per_mile": 1609.34 / best_pace / 60,  # minutes per mile
                            "start_time": time_data[start_idx] if start_idx < len(time_data) else 0,
                            "end_time": time_data[end_idx] if end_idx < len(time_data) else 0
                        }
                
                analysis["pace_analysis"] = pace_analysis
                
                # Estimate functional threshold pace
                fthp, method = estimate_functional_threshold_pace_from_streams(distance_data, time_data)
                if fthp:
                    analysis["estimated_fthp"] = {"value": fthp, "method": method}
        
        # Heart rate analysis
        if "heartrate" in activity_streams:
            hr_data = activity_streams["heartrate"]["data"]
            if hr_data:
                analysis["heart_rate_analysis"] = {
                    "max_hr": max(hr_data),
                    "avg_hr": np.mean(hr_data),
                    "min_hr": min([hr for hr in hr_data if hr > 0])  # Exclude zero HR
                }
        
        return analysis
        
    except Exception as e:
        logging.error(f"Error analyzing activity streams: {str(e)}")
        return analysis


def enhanced_threshold_estimation(activities_with_streams: List[Tuple[Dict, Dict]], gender: str) -> Dict[str, Optional[float]]:
    """
    Enhanced threshold estimation using streams data from multiple activities.
    
    Args:
        activities_with_streams: List of tuples (activity_summary, activity_streams)
        gender: User's gender
        
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
        best_ftp_estimates = []
        best_fthp_estimates = []
        all_max_hrs = []
        
        for activity_summary, activity_streams in activities_with_streams:
            if not activity_streams:
                continue
                
            activity_type = activity_summary.get("type", "").lower()
            
            # Analyze power data for cycling activities
            if activity_type in ["ride", "cycling"] and "watts" in activity_streams and "time" in activity_streams:
                ftp_estimate, method = estimate_ftp_from_streams(
                    activity_streams["watts"]["data"],
                    activity_streams["time"]["data"]
                )
                if ftp_estimate:
                    best_ftp_estimates.append((ftp_estimate, method))
            
            # Analyze pace data for running activities  
            if activity_type in ["run", "running"] and "distance" in activity_streams and "time" in activity_streams:
                fthp_estimate, method = estimate_functional_threshold_pace_from_streams(
                    activity_streams["distance"]["data"],
                    activity_streams["time"]["data"]
                )
                if fthp_estimate:
                    best_fthp_estimates.append((fthp_estimate, method))
            
            # Collect heart rate data
            if "heartrate" in activity_streams:
                hr_data = activity_streams["heartrate"]["data"]
                if hr_data:
                    max_hr = max(hr_data)
                    if max_hr > 100:  # Reasonable threshold
                        all_max_hrs.append(max_hr)
        
        # Select best FTP estimate (prefer longer duration methods)
        if best_ftp_estimates:
            method_priority = {
                "60min_power": 1,
                "40min_power_adjusted": 2,
                "20min_test": 3,
                "10min_power_adjusted": 4,
                "5min_power_adjusted": 5
            }
            
            best_ftp_estimates.sort(key=lambda x: (method_priority.get(x[1], 999), -x[0]))
            estimates['ftp_watts'] = best_ftp_estimates[0][0]
        
        # Select best threshold pace estimate
        if best_fthp_estimates:
            method_priority = {
                "60min_pace": 1,
                "30min_pace_adjusted": 2,
                "20min_pace_adjusted": 3,
                "10min_pace_adjusted": 4
            }
            
            best_fthp_estimates.sort(key=lambda x: (method_priority.get(x[1], 999), -x[0]))
            estimates['fthp_mps'] = best_fthp_estimates[0][0]
        
        # Estimate max HR
        if all_max_hrs:
            estimates['max_hr'] = max(all_max_hrs)
            
            # Rough resting HR estimate
            if gender.lower() == 'female':
                estimates['resting_hr'] = 75
            else:
                estimates['resting_hr'] = 70
        
        return estimates
        
    except Exception as e:
        logging.error(f"Error in enhanced threshold estimation: {str(e)}")
        return estimates
