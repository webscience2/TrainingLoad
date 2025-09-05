#!/usr/bin/env python3
"""
Enhanced Threshold Calculator with Research-Based Methods

This module provides comprehensive threshold estimation using scientifically validated methods
and integrates with the Strava sync process to automatically update thresholds.
"""

import sys
import os
sys.path.append('/Users/adam/src/TrainingLoad/backend')

from config import engine
from sqlalchemy import text
from streams_analysis import estimate_ftp_from_streams, estimate_functional_threshold_pace_from_streams
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class ResearchBasedThresholdCalculator:
    """
    Implements research-validated threshold calculation methods using stream data.
    """
    
    def __init__(self):
        self.cycling_methods = [
            ("60min_power", 1.0, "Gold standard: 60-minute all-out power"),
            ("40min_power", 0.97, "40-minute power × 0.97"),
            ("20min_test", 0.95, "20-minute test × 0.95 (most common)"),
            ("critical_power", 1.0, "Critical Power modeling"),
            ("percentile_95", 0.95, "95th percentile power × 0.95")
        ]
        
        self.running_methods = [
            ("60min_pace", 1.0, "Lactate threshold: 60-minute best pace"),
            ("30min_pace", 1.02, "30-minute pace × 1.02"),
            ("20min_pace", 1.05, "20-minute pace × 1.05"),
            ("critical_speed", 1.0, "Critical speed modeling")
        ]
    
    def calculate_cycling_ftp_from_streams(self, power_data: List[int], time_data: List[int]) -> Dict:
        """
        Calculate FTP using multiple research-based methods and return comprehensive analysis.
        """
        results = {
            'estimates': [],
            'recommended_ftp': None,
            'confidence': None,
            'method_used': None,
            'analysis': {}
        }
        
        try:
            # Method 1: Direct stream analysis (preferred)
            ftp_estimate, method = estimate_ftp_from_streams(power_data, time_data)
            if ftp_estimate:
                results['estimates'].append({
                    'method': method,
                    'ftp': ftp_estimate,
                    'confidence': 'high' if '60min' in method else 'medium' if '40min' in method else 'good'
                })
            
            # Method 2: Best sustained efforts analysis
            durations = [60, 40, 30, 20, 15, 10, 5]
            efforts = {}
            
            for duration in durations:
                best_power, start_idx, end_idx = self._find_best_power_effort(power_data, time_data, duration)
                if best_power > 50:  # Valid power reading
                    efforts[f'{duration}min'] = best_power
            
            results['analysis']['best_efforts'] = efforts
            
            # Apply research-based conversion factors
            if '60min' in efforts:
                results['estimates'].append({
                    'method': '60min_sustained',
                    'ftp': efforts['60min'],
                    'confidence': 'highest'
                })
            elif '40min' in efforts:
                results['estimates'].append({
                    'method': '40min_adjusted',
                    'ftp': efforts['40min'] * 0.97,
                    'confidence': 'high'
                })
            elif '20min' in efforts:
                results['estimates'].append({
                    'method': '20min_test',
                    'ftp': efforts['20min'] * 0.95,
                    'confidence': 'good'
                })
            
            # Method 3: Critical Power modeling (if sufficient data)
            if len(efforts) >= 3:
                cp_estimate = self._calculate_critical_power(efforts)
                if cp_estimate:
                    results['estimates'].append({
                        'method': 'critical_power',
                        'ftp': cp_estimate,
                        'confidence': 'medium'
                    })
            
            # Select best estimate
            if results['estimates']:
                # Prioritize by confidence level and method reliability
                confidence_priority = {'highest': 4, 'high': 3, 'good': 2, 'medium': 1}
                best_estimate = max(results['estimates'], 
                                  key=lambda x: confidence_priority.get(x['confidence'], 0))
                
                results['recommended_ftp'] = best_estimate['ftp']
                results['confidence'] = best_estimate['confidence']
                results['method_used'] = best_estimate['method']
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def calculate_running_threshold_from_streams(self, speed_data: List[float], time_data: List[int]) -> Dict:
        """
        Calculate running threshold using multiple research-based methods.
        """
        results = {
            'estimates': [],
            'recommended_fthp': None,
            'recommended_pace_per_km': None,
            'confidence': None,
            'method_used': None,
            'analysis': {}
        }
        
        try:
            # Method 1: Direct stream analysis
            fthp_estimate, method = estimate_functional_threshold_pace_from_streams(speed_data, time_data)
            if fthp_estimate:
                pace_per_km = (1000 / fthp_estimate) / 60
                results['estimates'].append({
                    'method': method,
                    'fthp': fthp_estimate,
                    'pace_per_km': pace_per_km,
                    'confidence': 'high'
                })
            
            # Method 2: Best sustained pace efforts
            durations = [60, 40, 30, 20, 15, 10, 5]
            efforts = {}
            
            for duration in durations:
                best_speed, start_idx, end_idx = self._find_best_pace_effort(speed_data, time_data, duration)
                if best_speed > 1.0:  # Valid running speed
                    efforts[f'{duration}min'] = best_speed
            
            results['analysis']['best_efforts'] = efforts
            
            # Apply research-based conversion factors
            if '60min' in efforts:
                # 60-minute pace is essentially lactate threshold
                fthp = efforts['60min']
                results['estimates'].append({
                    'method': '60min_lactate_threshold',
                    'fthp': fthp,
                    'pace_per_km': (1000 / fthp) / 60,
                    'confidence': 'highest'
                })
            elif '30min' in efforts:
                # 30-minute pace adjusted to threshold
                fthp = efforts['30min'] / 1.02  # 30-min pace is ~2% faster than threshold
                results['estimates'].append({
                    'method': '30min_adjusted',
                    'fthp': fthp,
                    'pace_per_km': (1000 / fthp) / 60,
                    'confidence': 'high'
                })
            elif '20min' in efforts:
                # 20-minute pace adjusted to threshold
                fthp = efforts['20min'] / 1.05  # 20-min pace is ~5% faster than threshold
                results['estimates'].append({
                    'method': '20min_test',
                    'fthp': fthp,
                    'pace_per_km': (1000 / fthp) / 60,
                    'confidence': 'good'
                })
            
            # Method 3: Critical Speed modeling
            if len(efforts) >= 3:
                cs_estimate = self._calculate_critical_speed(efforts)
                if cs_estimate:
                    results['estimates'].append({
                        'method': 'critical_speed',
                        'fthp': cs_estimate,
                        'pace_per_km': (1000 / cs_estimate) / 60,
                        'confidence': 'medium'
                    })
            
            # Select best estimate
            if results['estimates']:
                confidence_priority = {'highest': 4, 'high': 3, 'good': 2, 'medium': 1}
                best_estimate = max(results['estimates'], 
                                  key=lambda x: confidence_priority.get(x['confidence'], 0))
                
                results['recommended_threshold_mps'] = best_estimate['fthp']
                results['recommended_fthp'] = best_estimate['fthp']  # Keep both for compatibility
                results['recommended_pace_per_km'] = best_estimate['pace_per_km']
                results['confidence'] = best_estimate['confidence']
                results['method_used'] = best_estimate['method']
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _find_best_power_effort(self, power_data: List[int], time_data: List[int], duration_minutes: int) -> Tuple[float, int, int]:
        """Find best sustained power effort using sliding window."""
        if not power_data or not time_data:
            return 0.0, 0, 0
        
        duration_seconds = duration_minutes * 60
        best_power = 0.0
        best_start = 0
        best_end = 0
        
        for start_idx in range(len(time_data)):
            if start_idx + duration_seconds >= len(time_data):
                break
            
            end_idx = min(start_idx + duration_seconds, len(time_data) - 1)
            window_power = power_data[start_idx:end_idx]
            
            if window_power:
                avg_power = sum(p for p in window_power if p > 0) / len([p for p in window_power if p > 0])
                if avg_power > best_power:
                    best_power = avg_power
                    best_start = start_idx
                    best_end = end_idx
        
        return best_power, best_start, best_end
    
    def _find_best_pace_effort(self, speed_data: List[float], time_data: List[int], duration_minutes: int) -> Tuple[float, int, int]:
        """Find best sustained pace effort using sliding window."""
        if not speed_data or not time_data:
            return 0.0, 0, 0
        
        duration_seconds = duration_minutes * 60
        best_speed = 0.0
        best_start = 0
        best_end = 0
        
        for start_idx in range(len(time_data)):
            if start_idx + duration_seconds >= len(time_data):
                break
            
            end_idx = min(start_idx + duration_seconds, len(time_data) - 1)
            window_speed = speed_data[start_idx:end_idx]
            
            if window_speed:
                avg_speed = sum(s for s in window_speed if s > 1.0) / len([s for s in window_speed if s > 1.0])
                if avg_speed > best_speed:
                    best_speed = avg_speed
                    best_start = start_idx
                    best_end = end_idx
        
        return best_speed, best_start, best_end
    
    def _calculate_critical_power(self, efforts: Dict[str, float]) -> Optional[float]:
        """Calculate Critical Power using power-duration modeling."""
        # Simplified critical power calculation - would need more sophisticated modeling for production
        # This is a placeholder for the mathematical approach
        if len(efforts) < 3:
            return None
        
        # Use the longer duration efforts as they're closer to CP
        longer_efforts = {k: v for k, v in efforts.items() if int(k.replace('min', '')) >= 20}
        if longer_efforts:
            return sum(longer_efforts.values()) / len(longer_efforts)
        return None
    
    def _calculate_critical_speed(self, efforts: Dict[str, float]) -> Optional[float]:
        """Calculate Critical Speed using pace-duration modeling."""
        # Simplified critical speed calculation
        if len(efforts) < 3:
            return None
        
        # Use the longer duration efforts as they're closer to CS
        longer_efforts = {k: v for k, v in efforts.items() if int(k.replace('min', '')) >= 20}
        if longer_efforts:
            return sum(longer_efforts.values()) / len(longer_efforts)
        return None

def update_thresholds_from_activity_streams(activity_id: int, user_id: int) -> Dict:
    """
    Analyze an activity's streams and update thresholds if significant improvement found.
    """
    results = {
        'cycling_analysis': None,
        'running_analysis': None,
        'thresholds_updated': False,
        'updates': []
    }
    
    try:
        with engine.connect() as conn:
            # Get activity with streams data
            result = conn.execute(text("""
                SELECT a.name, a.type, a.data::json as activity_data
                FROM activities a
                WHERE a.activity_id = :activity_id AND a.user_id = :user_id
            """), {"activity_id": activity_id, "user_id": user_id})
            
            activity = result.fetchone()
            if not activity:
                return results
            
            name, activity_type, activity_data = activity
            streams = activity_data.get('streams', {}) if activity_data else {}
            
            calculator = ResearchBasedThresholdCalculator()
            
            # Analyze cycling activities
            if activity_type in ['Ride', 'VirtualRide'] and 'watts' in streams:
                power_data = streams['watts']['data']
                time_data = streams['time']['data']
                
                cycling_analysis = calculator.calculate_cycling_ftp_from_streams(power_data, time_data)
                results['cycling_analysis'] = cycling_analysis
                
                if cycling_analysis.get('recommended_ftp'):
                    # Check if this is a significant improvement
                    current_ftp = get_current_ftp(user_id)
                    recommended_ftp = cycling_analysis['recommended_ftp']
                    
                    if not current_ftp or recommended_ftp > current_ftp * 1.02:  # 2% improvement threshold
                        update_user_ftp(user_id, recommended_ftp, cycling_analysis['method_used'])
                        results['thresholds_updated'] = True
                        results['updates'].append({
                            'type': 'FTP',
                            'old_value': current_ftp,
                            'new_value': recommended_ftp,
                            'method': cycling_analysis['method_used'],
                            'activity': name
                        })
            
            # Analyze running activities
            elif activity_type in ['Run', 'VirtualRun'] and 'velocity_smooth' in streams:
                speed_data = streams['velocity_smooth']['data']
                time_data = streams['time']['data']
                
                running_analysis = calculator.calculate_running_threshold_from_streams(speed_data, time_data)
                results['running_analysis'] = running_analysis
                
                if running_analysis.get('recommended_fthp'):
                    # Check if this is a significant improvement
                    current_fthp = get_current_fthp(user_id)
                    recommended_fthp = running_analysis['recommended_fthp']
                    
                    if not current_fthp or recommended_fthp > current_fthp * 1.02:  # 2% improvement threshold
                        update_user_fthp(user_id, recommended_fthp, running_analysis['method_used'])
                        results['thresholds_updated'] = True
                        results['updates'].append({
                            'type': 'FTHP',
                            'old_value': current_fthp,
                            'new_value': recommended_fthp,
                            'method': running_analysis['method_used'],
                            'activity': name
                        })
    
    except Exception as e:
        results['error'] = str(e)
    
    return results

def get_current_ftp(user_id: int) -> Optional[float]:
    """Get current FTP for user."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT ftp_watts FROM thresholds 
                WHERE user_id = :user_id AND ftp_watts IS NOT NULL
                ORDER BY date_updated DESC LIMIT 1
            """), {"user_id": user_id})
            row = result.fetchone()
            return float(row[0]) if row else None
    except:
        return None

def calculate_initial_thresholds_for_new_user(user_id: int) -> Dict:
    """
    Calculate initial thresholds for a new user using all their historical activities with stream analysis.
    This provides the most accurate initial threshold estimates using research-based methods.
    """
    try:
        with engine.connect() as conn:
            # Get all activities for this user that have streams data
            result = conn.execute(text("""
                SELECT a.strava_activity_id, a.type, a.moving_time, a.distance, 
                       a.average_speed, a.data
                FROM activities a
                WHERE a.user_id = :user_id
                  AND a.data IS NOT NULL
                  AND a.data::json->'streams' IS NOT NULL
                  AND a.moving_time > 600  -- At least 10 minutes
                ORDER BY a.start_date DESC
            """), {"user_id": user_id})
            
            activities = result.fetchall()
            
            if not activities:
                logging.warning(f"No activities with streams found for new user {user_id}")
                return {}
            
            calculator = ResearchBasedThresholdCalculator()
            cycling_activities = []
            running_activities = []
            
            # Process each activity's streams
            for activity in activities:
                activity_id, activity_type, moving_time, distance, avg_speed, data = activity
                
                if not data or 'streams' not in data or not data['streams']:
                    continue
                    
                streams = data['streams']
                
                # Collect cycling activities with power data
                if activity_type in ['Ride', 'VirtualRide'] and 'watts' in streams:
                    power_data = streams['watts']['data']
                    time_data = streams['time']['data'] if 'time' in streams else list(range(len(power_data)))
                    
                    if power_data and len(power_data) > 100:  # Sufficient data
                        cycling_activities.append({
                            'power_data': power_data,
                            'time_data': time_data,
                            'activity_type': activity_type,
                            'moving_time': moving_time,
                            'activity_id': activity_id
                        })
                
                # Collect running activities with speed/pace data
                if activity_type in ['Run', 'VirtualRun'] and 'velocity_smooth' in streams:
                    velocity_data = streams['velocity_smooth']['data']
                    time_data = streams['time']['data'] if 'time' in streams else list(range(len(velocity_data)))
                    
                    if velocity_data and len(velocity_data) > 100:  # Sufficient data
                        running_activities.append({
                            'velocity_data': velocity_data,
                            'time_data': time_data,
                            'activity_type': activity_type,
                            'moving_time': moving_time,
                            'distance': distance,
                            'activity_id': activity_id
                        })
            
            estimates = {}
            
            # Calculate cycling FTP using research-based methods
            if cycling_activities:
                logging.info(f"Analyzing {len(cycling_activities)} cycling activities for FTP estimation")
                best_ftp = 0
                best_analysis = None
                
                for activity in cycling_activities[:10]:  # Analyze top 10 recent activities
                    try:
                        analysis = calculator.calculate_cycling_ftp_from_streams(
                            activity['power_data'], 
                            activity['time_data']
                        )
                        
                        if analysis.get('recommended_ftp', 0) > best_ftp:
                            best_ftp = analysis['recommended_ftp']
                            best_analysis = analysis
                            
                        logging.info(f"Activity {activity['activity_id']}: FTP estimate {analysis.get('recommended_ftp', 0)}W")
                    except Exception as e:
                        logging.warning(f"Could not analyze activity {activity['activity_id']}: {e}")
                
                if best_ftp > 0:
                    estimates['ftp_watts'] = best_ftp
                    logging.info(f"Best FTP estimate: {best_ftp}W using {best_analysis.get('method_used', 'stream analysis')}")
            
            # Calculate running threshold using research-based methods
            if running_activities:
                logging.info(f"Analyzing {len(running_activities)} running activities for threshold pace estimation")
                best_threshold = 0
                best_analysis = None
                
                for activity in running_activities[:10]:  # Analyze top 10 recent activities
                    try:
                        analysis = calculator.calculate_running_threshold_from_streams(
                            activity['velocity_data'],
                            activity['time_data']
                        )
                        
                        if analysis.get('recommended_threshold_mps', 0) > best_threshold:
                            best_threshold = analysis['recommended_threshold_mps']
                            best_analysis = analysis
                            
                        pace_min_km = (1000 / analysis.get('recommended_threshold_mps', 1)) / 60 if analysis.get('recommended_threshold_mps', 0) > 0 else 0
                        logging.info(f"Activity {activity['activity_id']}: Threshold estimate {analysis.get('recommended_threshold_mps', 0):.2f} m/s ({pace_min_km:.1f} min/km)")
                    except Exception as e:
                        logging.warning(f"Could not analyze activity {activity['activity_id']}: {e}")
                
                if best_threshold > 0:
                    estimates['fthp_mps'] = best_threshold
                    pace_min_km = (1000 / best_threshold) / 60
                    logging.info(f"Best threshold pace estimate: {best_threshold:.2f} m/s ({pace_min_km:.1f} min/km) using {best_analysis.get('method_used', 'stream analysis')}")
            
            # Estimate heart rate values from activity data if available
            try:
                hr_result = conn.execute(text("""
                    SELECT MAX((a.data::json->>'max_heartrate')::float::int) as max_hr
                    FROM activities a
                    WHERE a.user_id = :user_id
                      AND a.data::json->>'max_heartrate' IS NOT NULL
                      AND (a.data::json->>'max_heartrate')::float > 120
                """), {"user_id": user_id})
                
                hr_row = hr_result.fetchone()
                if hr_row and hr_row[0]:
                    estimates['max_hr'] = hr_row[0]
                    # Conservative resting HR estimate
                    estimates['resting_hr'] = max(40, int(hr_row[0] * 0.4))
                    
            except Exception as e:
                logging.warning(f"Could not estimate heart rate thresholds: {e}")
            
            logging.info(f"Research-based initial thresholds for user {user_id}: {estimates}")
            return estimates
            
    except Exception as e:
        logging.error(f"Error calculating initial thresholds for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_current_fthp(user_id: int) -> Optional[float]:
    """Get current FTHP for user."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT fthp_mps FROM thresholds 
                WHERE user_id = :user_id AND fthp_mps IS NOT NULL
                ORDER BY date_updated DESC LIMIT 1
            """), {"user_id": user_id})
            row = result.fetchone()
            return float(row[0]) if row else None
    except:
        return None

def update_user_ftp(user_id: int, ftp_watts: float, method: str):
    """Update user's FTP in database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE thresholds 
                SET ftp_watts = :ftp_watts, 
                    date_updated = CURRENT_TIMESTAMP,
                    calculation_method = :method
                WHERE user_id = :user_id
            """), {"ftp_watts": ftp_watts, "method": method, "user_id": user_id})
            conn.commit()
    except Exception as e:
        print(f"Error updating FTP: {e}")

def update_user_fthp(user_id: int, fthp_mps: float, method: str):
    """Update user's FTHP in database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE thresholds 
                SET fthp_mps = :fthp_mps, 
                    date_updated = CURRENT_TIMESTAMP,
                    calculation_method = :method
                WHERE user_id = :user_id
            """), {"fthp_mps": fthp_mps, "method": method, "user_id": user_id})
            conn.commit()
    except Exception as e:
        print(f"Error updating FTHP: {e}")

def recalculate_all_thresholds_from_streams(user_id: int, lookback_days: int = 365) -> Dict:
    """
    Recalculate thresholds from all activities with streams data.
    """
    results = {
        'activities_analyzed': 0,
        'cycling_activities': 0,
        'running_activities': 0,
        'ftp_updates': [],
        'fthp_updates': [],
        'final_ftp': None,
        'final_fthp': None
    }
    
    try:
        calculator = ResearchBasedThresholdCalculator()
        
        with engine.connect() as conn:
            # Get all activities with streams data
            result = conn.execute(text("""
                SELECT a.activity_id, a.name, a.type, a.start_date, a.data::json as activity_data
                FROM activities a
                WHERE a.user_id = :user_id 
                  AND a.data::json->'streams' IS NOT NULL
                  AND a.start_date > CURRENT_DATE - INTERVAL :lookback_days DAY
                ORDER BY a.start_date DESC
            """), {"user_id": user_id, "lookback_days": lookback_days})
            
            activities = result.fetchall()
            results['activities_analyzed'] = len(activities)
            
            best_ftp = None
            best_fthp = None
            
            for activity in activities:
                activity_id, name, activity_type, start_date, activity_data = activity
                streams = activity_data.get('streams', {})
                
                # Analyze cycling activities
                if activity_type in ['Ride', 'VirtualRide'] and 'watts' in streams:
                    results['cycling_activities'] += 1
                    power_data = streams['watts']['data']
                    time_data = streams['time']['data']
                    
                    analysis = calculator.calculate_cycling_ftp_from_streams(power_data, time_data)
                    if analysis.get('recommended_ftp'):
                        ftp = analysis['recommended_ftp']
                        if not best_ftp or ftp > best_ftp:
                            best_ftp = ftp
                            results['ftp_updates'].append({
                                'date': start_date,
                                'activity': name,
                                'ftp': ftp,
                                'method': analysis['method_used'],
                                'confidence': analysis['confidence']
                            })
                
                # Analyze running activities  
                elif activity_type in ['Run', 'VirtualRun'] and 'velocity_smooth' in streams:
                    results['running_activities'] += 1
                    speed_data = streams['velocity_smooth']['data']
                    time_data = streams['time']['data']
                    
                    analysis = calculator.calculate_running_threshold_from_streams(speed_data, time_data)
                    if analysis.get('recommended_fthp'):
                        fthp = analysis['recommended_fthp']
                        if not best_fthp or fthp > best_fthp:
                            best_fthp = fthp
                            results['fthp_updates'].append({
                                'date': start_date,
                                'activity': name,
                                'fthp': fthp,
                                'pace_per_km': analysis['recommended_pace_per_km'],
                                'method': analysis['method_used'],
                                'confidence': analysis['confidence']
                            })
            
            # Update thresholds with best values found
            if best_ftp:
                best_ftp_entry = max(results['ftp_updates'], key=lambda x: x['ftp'])
                update_user_ftp(user_id, best_ftp, best_ftp_entry['method'])
                results['final_ftp'] = best_ftp
            
            if best_fthp:
                best_fthp_entry = max(results['fthp_updates'], key=lambda x: x['fthp'])
                update_user_fthp(user_id, best_fthp, best_fthp_entry['method'])
                results['final_fthp'] = best_fthp
    
    except Exception as e:
        results['error'] = str(e)
    
    return results

if __name__ == "__main__":
    # Example usage for your account
    print("🔬 Research-Based Threshold Recalculation")
    print("=" * 50)
    
    # Get user ID (assuming adam's account)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT user_id FROM users WHERE email LIKE '%adam%' LIMIT 1"))
        user_row = result.fetchone()
        if user_row:
            user_id = user_row[0]
            print(f"Recalculating thresholds for user ID: {user_id}")
            
            results = recalculate_all_thresholds_from_streams(user_id)
            
            print(f"\n📊 Analysis Results:")
            print(f"Activities analyzed: {results['activities_analyzed']}")
            print(f"Cycling activities: {results['cycling_activities']}")
            print(f"Running activities: {results['running_activities']}")
            
            if results.get('final_ftp'):
                print(f"\n🚴 Final FTP: {results['final_ftp']:.0f}W")
                if results['ftp_updates']:
                    best_ftp = max(results['ftp_updates'], key=lambda x: x['ftp'])
                    print(f"From: {best_ftp['activity']} ({best_ftp['method']})")
            
            if results.get('final_fthp'):
                pace_km = (1000 / results['final_fthp']) / 60
                print(f"\n🏃 Final FTHP: {results['final_fthp']:.2f} m/s ({pace_km:.1f} min/km)")
                if results['fthp_updates']:
                    best_fthp = max(results['fthp_updates'], key=lambda x: x['fthp'])
                    print(f"From: {best_fthp['activity']} ({best_fthp['method']})")
        else:
            print("User not found")
