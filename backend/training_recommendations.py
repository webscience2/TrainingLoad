#!/usr/bin/env python3
"""
Training Load Recommendation Engine

Uses scientific principles from sports science research to generate safe,
optimal training recommendations based on:
- Historical UTL patterns and trends
- Current wellness data (HRV, sleep, readiness)
- Progressive overload principles (10% rule)
- Activity-specific fatigue and recovery patterns
- Injury prevention through load management

Key Research Principles Applied:
1. 10% weekly load increase rule (Gabbett, 2016)
2. Acute:Chronic Workload Ratio < 1.3 (Blanch & Gabbett, 2016)
3. HRV-guided training intensity (Seiler, 2010)
4. Activity-specific recovery requirements (Laursen & Jenkins, 2002)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import User, Activity, WellnessData, Threshold


class TrainingRecommendationEngine:
    
    def __init__(self):
        # Science-based parameters
        self.SAFE_WEEKLY_INCREASE = 0.10  # 10% max weekly increase
        self.OPTIMAL_ACW_RATIO = 1.0      # Acute:Chronic Workload Ratio target
        self.MAX_ACW_RATIO = 1.3          # Upper limit for injury prevention
        self.MIN_ACW_RATIO = 0.8          # Lower limit to maintain fitness
        
        # Activity-specific recovery periods (hours)
        self.RECOVERY_PERIODS = {
            'easy': 12,      # Easy aerobic sessions
            'moderate': 24,  # Tempo/threshold sessions  
            'hard': 48,      # VO2max/anaerobic sessions
            'race': 72       # Race efforts or very high intensity
        }
        
        # Wellness-based intensity modifiers
        self.WELLNESS_MODIFIERS = {
            'excellent': 1.1,  # HRV high, sleep good, readiness high
            'good': 1.0,       # Normal wellness metrics
            'fair': 0.8,       # Some wellness concerns
            'poor': 0.6        # Multiple wellness red flags
        }
    
    def generate_recommendations(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Generate 5-day training recommendations based on comprehensive analysis.
        """
        logging.info(f"Generating training recommendations for user {user_id}")
        
        try:
            # Get user data
            user = db.query(User).filter_by(user_id=user_id).first()
            threshold = db.query(Threshold).filter_by(user_id=user_id).first()
            
            if not user or not threshold:
                return {"error": "User or threshold data not found"}
            
            # Analyze historical patterns
            historical_analysis = self._analyze_historical_patterns(user_id, db)
            
            # Get current wellness status
            wellness_status = self._assess_current_wellness(user_id, db)
            
            # Calculate workload ratios and trends
            workload_analysis = self._calculate_workload_ratios(user_id, db)
            
            # Generate activity-specific recommendations
            cycling_recs = self._generate_cycling_recommendations(
                user_id, db, historical_analysis, wellness_status, workload_analysis
            )
            
            running_recs = self._generate_running_recommendations(
                user_id, db, historical_analysis, wellness_status, workload_analysis
            )
            
            # Create 5-day plan
            daily_recommendations = self._create_daily_plan(
                cycling_recs, running_recs, wellness_status, workload_analysis
            )
            
            # Generate weekly summary
            weekly_summary = self._generate_weekly_summary(cycling_recs, running_recs)
            
            return {
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "wellness_status": wellness_status,
                "workload_analysis": workload_analysis,
                "historical_insights": historical_analysis,
                "cycling_recommendations": cycling_recs,
                "running_recommendations": running_recs,
                "weekly_summary": weekly_summary,
                "daily_plan": daily_recommendations,
                "safety_warnings": self._generate_safety_warnings(workload_analysis, wellness_status)
            }
            
        except Exception as e:
            logging.error(f"Error generating recommendations for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _analyze_historical_patterns(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Analyze historical training patterns to identify trends and preferences.
        """
        # Get last 12 weeks of data
        twelve_weeks_ago = datetime.now() - timedelta(days=84)
        
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.start_date >= twelve_weeks_ago,
            Activity.utl_score.isnot(None)
        ).order_by(Activity.start_date.desc()).all()
        
        if not activities:
            return {"error": "Insufficient historical data"}
        
        # Group by weeks and activity types
        weekly_loads = {}
        activity_patterns = {"cycling": [], "running": [], "other": []}
        
        for activity in activities:
            week_key = activity.start_date.strftime("%Y-W%U")
            if week_key not in weekly_loads:
                weekly_loads[week_key] = {"cycling": 0, "running": 0, "other": 0, "total": 0}
            
            activity_type = "cycling" if activity.type.lower() in ['ride', 'virtualride'] else \
                           "running" if activity.type.lower() in ['run', 'virtualrun'] else "other"
            
            weekly_loads[week_key][activity_type] += activity.utl_score
            weekly_loads[week_key]["total"] += activity.utl_score
            
            activity_patterns[activity_type].append({
                "date": activity.start_date,
                "utl": activity.utl_score,
                "duration": activity.moving_time,
                "type": activity.type
            })
        
        # Calculate trends
        recent_weeks = sorted(weekly_loads.keys())[-4:]  # Last 4 weeks
        older_weeks = sorted(weekly_loads.keys())[-8:-4]  # 4 weeks before that
        
        recent_avg = np.mean([weekly_loads[w]["total"] for w in recent_weeks])
        older_avg = np.mean([weekly_loads[w]["total"] for w in older_weeks]) if older_weeks else recent_avg
        
        load_trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Calculate training distribution
        cycling_percentage = sum([weekly_loads[w]["cycling"] for w in recent_weeks]) / \
                           sum([weekly_loads[w]["total"] for w in recent_weeks]) if recent_weeks else 0
        
        return {
            "weekly_loads": weekly_loads,
            "recent_weekly_average": recent_avg,
            "load_trend": load_trend,
            "cycling_percentage": cycling_percentage,
            "running_percentage": 1 - cycling_percentage,
            "activity_patterns": activity_patterns,
            "total_activities_12w": len(activities)
        }
    
    def _assess_current_wellness(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Assess current wellness status from recent data.
        """
        # Get last 7 days of wellness data
        week_ago = datetime.now() - timedelta(days=7)
        
        wellness_entries = db.query(WellnessData).filter(
            WellnessData.user_id == user_id,
            WellnessData.date >= week_ago.date()
        ).order_by(WellnessData.date.desc()).all()
        
        if not wellness_entries:
            return {
                "status": "unknown",
                "modifier": 1.0,
                "note": "No recent wellness data available"
            }
        
        # Calculate averages from recent data
        hrv_values = [w.hrv for w in wellness_entries if w.hrv is not None]
        sleep_values = [w.sleep_score for w in wellness_entries if w.sleep_score is not None]
        readiness_values = [w.readiness_score for w in wellness_entries if w.readiness_score is not None]
        
        # Simple scoring system (can be enhanced with user baselines)
        scores = []
        
        if hrv_values:
            avg_hrv = np.mean(hrv_values)
            # Assume HRV values are in milliseconds, typical ranges 20-60ms
            hrv_score = min(avg_hrv / 40.0, 1.5)  # Normalize to ~1.0 for 40ms
            scores.append(hrv_score)
        
        if sleep_values:
            avg_sleep = np.mean(sleep_values)
            # Assume sleep scores are 0-100 scale
            sleep_score = avg_sleep / 100.0
            scores.append(sleep_score)
        
        if readiness_values:
            avg_readiness = np.mean(readiness_values)
            # Assume readiness scores are 0-100 scale  
            readiness_score = avg_readiness / 100.0
            scores.append(readiness_score)
        
        if not scores:
            overall_score = 1.0
        else:
            overall_score = np.mean(scores)
        
        # Classify wellness status
        if overall_score >= 1.1:
            status = "excellent"
        elif overall_score >= 0.9:
            status = "good"
        elif overall_score >= 0.7:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "status": status,
            "modifier": self.WELLNESS_MODIFIERS[status],
            "overall_score": overall_score,
            "hrv_avg": np.mean(hrv_values) if hrv_values else None,
            "sleep_avg": np.mean(sleep_values) if sleep_values else None,
            "readiness_avg": np.mean(readiness_values) if readiness_values else None,
            "data_points": len(wellness_entries)
        }
    
    def _calculate_workload_ratios(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Calculate Acute:Chronic Workload Ratio and related metrics for overall and sport-specific loads.
        """
        # Get last 28 days for chronic load (4 weeks)
        chronic_start = datetime.now() - timedelta(days=28)
        # Get last 7 days for acute load (1 week)
        acute_start = datetime.now() - timedelta(days=7)
        
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
        
        # Calculate overall loads
        chronic_load = sum([a.utl_score for a in chronic_activities]) / 4.0  # Weekly average
        acute_load = sum([a.utl_score for a in acute_activities])
        acw_ratio = acute_load / chronic_load if chronic_load > 0 else 1.0
        
        # Calculate sport-specific loads
        sport_specific_analysis = self._calculate_sport_specific_acwr(chronic_activities, acute_activities)
        
        # Assess overall risk level
        risk_assessment = self._assess_acwr_risk(acw_ratio)
        
        # Determine combined risk considering sport-specific factors
        combined_risk = self._assess_combined_risk(risk_assessment, sport_specific_analysis)
        
        return {
            "acute_load": acute_load,
            "chronic_load": chronic_load,
            "acw_ratio": acw_ratio,
            "risk_level": combined_risk["level"],
            "risk_note": combined_risk["note"],
            "target_weekly_load": chronic_load * self.OPTIMAL_ACW_RATIO,
            "max_safe_weekly_load": chronic_load * self.MAX_ACW_RATIO,
            "sport_specific": sport_specific_analysis
        }
    
    def _calculate_sport_specific_acwr(self, chronic_activities: List, acute_activities: List) -> Dict[str, Any]:
        """Calculate ACWR ratios for specific sports (running, cycling)."""
        
        # Categorize activities by sport
        def categorize_activity(activity):
            activity_type = activity.type.lower() if activity.type else ""
            if "run" in activity_type or "jog" in activity_type:
                return "running"
            elif "ride" in activity_type or "cycling" in activity_type or "bike" in activity_type:
                return "cycling"
            else:
                return "other"
        
        # Calculate chronic loads by sport
        chronic_running = sum([a.utl_score for a in chronic_activities if categorize_activity(a) == "running"]) / 4.0
        chronic_cycling = sum([a.utl_score for a in chronic_activities if categorize_activity(a) == "cycling"]) / 4.0
        chronic_other = sum([a.utl_score for a in chronic_activities if categorize_activity(a) == "other"]) / 4.0
        
        # Calculate acute loads by sport
        acute_running = sum([a.utl_score for a in acute_activities if categorize_activity(a) == "running"])
        acute_cycling = sum([a.utl_score for a in acute_activities if categorize_activity(a) == "cycling"])
        acute_other = sum([a.utl_score for a in acute_activities if categorize_activity(a) == "other"])
        
        # Calculate sport-specific ACWR ratios
        running_acwr = acute_running / chronic_running if chronic_running > 0 else (1.0 if acute_running > 0 else 0.0)
        cycling_acwr = acute_cycling / chronic_cycling if chronic_cycling > 0 else (1.0 if acute_cycling > 0 else 0.0)
        other_acwr = acute_other / chronic_other if chronic_other > 0 else (1.0 if acute_other > 0 else 0.0)
        
        return {
            "running": {
                "acute_load": acute_running,
                "chronic_load": chronic_running,
                "acwr": running_acwr,
                "risk_assessment": self._assess_acwr_risk(running_acwr),
                "activity_count_chronic": len([a for a in chronic_activities if categorize_activity(a) == "running"]),
                "activity_count_acute": len([a for a in acute_activities if categorize_activity(a) == "running"])
            },
            "cycling": {
                "acute_load": acute_cycling,
                "chronic_load": chronic_cycling, 
                "acwr": cycling_acwr,
                "risk_assessment": self._assess_acwr_risk(cycling_acwr),
                "activity_count_chronic": len([a for a in chronic_activities if categorize_activity(a) == "cycling"]),
                "activity_count_acute": len([a for a in acute_activities if categorize_activity(a) == "cycling"])
            },
            "other": {
                "acute_load": acute_other,
                "chronic_load": chronic_other,
                "acwr": other_acwr,
                "risk_assessment": self._assess_acwr_risk(other_acwr),
                "activity_count_chronic": len([a for a in chronic_activities if categorize_activity(a) == "other"]),
                "activity_count_acute": len([a for a in acute_activities if categorize_activity(a) == "other"])
            }
        }
    
    def _assess_acwr_risk(self, acwr: float) -> Dict[str, str]:
        """Assess risk level for a given ACWR value."""
        if acwr > self.MAX_ACW_RATIO:
            return {"level": "high", "note": "Acute load too high - injury risk increased"}
        elif acwr < self.MIN_ACW_RATIO:
            return {"level": "detraining", "note": "Load too low - fitness may decline"}
        elif acwr > 1.2:
            return {"level": "moderate", "note": "Approaching upper safe limit"}
        else:
            return {"level": "low", "note": "Load within safe parameters"}
    
    def _assess_combined_risk(self, overall_risk: Dict, sport_specific: Dict) -> Dict[str, str]:
        """Assess combined risk considering both overall and sport-specific ACWR."""
        # Get individual sport risks
        running_risk = sport_specific["running"]["risk_assessment"]["level"]
        cycling_risk = sport_specific["cycling"]["risk_assessment"]["level"]
        overall_risk_level = overall_risk["level"]
        
        # Determine highest risk level
        risk_hierarchy = {"low": 0, "moderate": 1, "detraining": 1, "high": 2}
        max_risk_score = max(
            risk_hierarchy.get(overall_risk_level, 0),
            risk_hierarchy.get(running_risk, 0),
            risk_hierarchy.get(cycling_risk, 0)
        )
        
        # Map back to risk level
        risk_levels = {0: "low", 1: "moderate", 2: "high"}
        combined_level = risk_levels[max_risk_score]
        
        # Generate combined note
        warnings = []
        if running_risk in ["high", "moderate"]:
            warnings.append(f"Running ACWR {sport_specific['running']['acwr']:.2f} - {sport_specific['running']['risk_assessment']['note']}")
        if cycling_risk in ["high", "moderate"]:
            warnings.append(f"Cycling ACWR {sport_specific['cycling']['acwr']:.2f} - {sport_specific['cycling']['risk_assessment']['note']}")
        
        if warnings:
            combined_note = f"Sport-specific concerns: {'; '.join(warnings)}"
        elif combined_level == overall_risk_level:
            combined_note = overall_risk["note"]
        else:
            combined_note = "Mixed sport-specific risk levels detected"
        
        return {"level": combined_level, "note": combined_note}
    
    def _generate_cycling_recommendations(self, user_id: int, db: Session, 
                                        historical: Dict, wellness: Dict, 
                                        workload: Dict) -> Dict[str, Any]:
        """
        Generate cycling-specific recommendations.
        """
        threshold = db.query(Threshold).filter_by(user_id=user_id).first()
        
        # Base recommendations on FTP if available
        if threshold and threshold.ftp_watts and threshold.ftp_watts > 0:
            ftp = threshold.ftp_watts
            
            # Calculate zone-based recommendations
            zones = {
                "recovery": (0.55 * ftp, 0.65 * ftp),      # Zone 1
                "aerobic": (0.65 * ftp, 0.75 * ftp),       # Zone 2
                "tempo": (0.75 * ftp, 0.85 * ftp),         # Zone 3
                "threshold": (0.85 * ftp, 1.05 * ftp),     # Zone 4
                "vo2max": (1.05 * ftp, 1.2 * ftp)          # Zone 5
            }
            
            # Recommend different session types based on current status
            if wellness["status"] == "excellent" and workload["risk_level"] == "low":
                primary_sessions = ["threshold", "vo2max"]
                session_note = "High-quality sessions recommended"
            elif wellness["status"] in ["good", "fair"] and workload["risk_level"] in ["low", "moderate"]:
                primary_sessions = ["aerobic", "tempo"]
                session_note = "Moderate intensity focus"
            else:
                primary_sessions = ["recovery", "aerobic"]
                session_note = "Easy sessions to promote recovery"
            
            return {
                "ftp": ftp,
                "power_zones": zones,
                "recommended_sessions": primary_sessions,
                "session_note": session_note,
                "weekly_hours_target": self._calculate_cycling_hours_target(historical, workload),
                "intensity_distribution": self._get_polarized_distribution()
            }
        else:
            # Heart rate based recommendations
            return {
                "note": "Power-based training unavailable, using HR-based recommendations",
                "recommended_sessions": ["aerobic", "recovery"],
                "weekly_hours_target": self._calculate_cycling_hours_target(historical, workload)
            }
    
    def _generate_running_recommendations(self, user_id: int, db: Session,
                                        historical: Dict, wellness: Dict,
                                        workload: Dict) -> Dict[str, Any]:
        """
        Generate running-specific recommendations.
        """
        threshold = db.query(Threshold).filter_by(user_id=user_id).first()
        
        # Base recommendations on threshold pace if available
        if threshold and threshold.fthp_mps and threshold.fthp_mps > 0:
            threshold_pace = threshold.fthp_mps  # m/s
            
            # Convert to pace zones (minutes per kilometer for metric)
            def mps_to_min_per_km(mps):
                return 16.6667 / mps if mps > 0 else 0  # 1000m / 60s = 16.6667
            
            threshold_pace_min_km = mps_to_min_per_km(threshold_pace)
            
            pace_zones = {
                "easy": mps_to_min_per_km(threshold_pace * 0.8),      # 80% of threshold
                "aerobic": mps_to_min_per_km(threshold_pace * 0.85),   # 85% of threshold
                "tempo": mps_to_min_per_km(threshold_pace * 0.92),     # 92% of threshold
                "threshold": threshold_pace_min_km,                     # 100% of threshold
                "interval": mps_to_min_per_km(threshold_pace * 1.08)   # 108% of threshold
            }
            
            # Recommend session types based on current status
            if wellness["status"] == "excellent" and workload["risk_level"] == "low":
                primary_sessions = ["threshold", "interval"]
                session_note = "Quality speed work recommended"
            elif wellness["status"] in ["good", "fair"]:
                primary_sessions = ["tempo", "aerobic"]
                session_note = "Moderate effort sessions"
            else:
                primary_sessions = ["easy", "aerobic"]
                session_note = "Easy running for recovery"
            
            # Calculate distance recommendations based on weekly targets
            weekly_km_target = self._calculate_running_km_target(historical, workload)
            long_run_analysis = self._analyze_historical_long_runs(historical)
            distance_zones = self._calculate_distance_zones(weekly_km_target, wellness["modifier"], long_run_analysis)
            
            return {
                "threshold_pace_mps": threshold_pace,
                "threshold_pace_min_km": threshold_pace_min_km,
                "pace_zones": pace_zones,
                "distance_zones": distance_zones,
                "recommended_sessions": primary_sessions,
                "session_note": session_note,
                "weekly_km_target": weekly_km_target,
                "long_run_percentage": 0.25  # 25% of weekly mileage in long run
            }
        else:
            # Default distance recommendations when no threshold data
            weekly_km_target = self._calculate_running_km_target(historical, workload)
            long_run_analysis = self._analyze_historical_long_runs(historical) 
            distance_zones = self._calculate_distance_zones(weekly_km_target, wellness["modifier"], long_run_analysis)
            
            return {
                "note": "Pace-based training unavailable, using effort-based recommendations",
                "recommended_sessions": ["easy", "moderate"],
                "distance_zones": distance_zones,
                "weekly_km_target": weekly_km_target
            }
    
    def _create_daily_plan(self, cycling_recs: Dict, running_recs: Dict,
                          wellness: Dict, workload: Dict) -> List[Dict[str, Any]]:
        """
        Create a 5-day training plan based on recommendations.
        """
        daily_plan = []
        
        # Apply wellness modifier to overall volume
        volume_modifier = wellness["modifier"]
        
        # Get current day of week to plan appropriately
        today = datetime.now()
        
        for i in range(5):
            plan_date = today + timedelta(days=i)
            day_name = plan_date.strftime("%A")
            
            # Create daily recommendation
            day_plan = {
                "date": plan_date.strftime("%Y-%m-%d"),
                "day": day_name,
                "activities": []
            }
            
            # Alternate cycling and running based on historical patterns
            if i % 2 == 0:  # Even days - primary activity
                if cycling_recs.get("ftp"):
                    # Cycling day
                    session_type = self._select_session_type(cycling_recs, i, wellness)
                    day_plan["activities"].append({
                        "type": "cycling",
                        "session": session_type,
                        "duration_minutes": self._calculate_session_duration(session_type, "cycling", volume_modifier),
                        "intensity": self._get_session_intensity(session_type, cycling_recs),
                        "notes": self._get_session_notes(session_type, "cycling")
                    })
                
            else:  # Odd days - secondary activity or running
                if running_recs.get("threshold_pace_mps"):
                    # Running day with pace-based guidance
                    session_type = self._select_session_type(running_recs, i, wellness)
                    distance_guidance = self._get_distance_guidance(session_type, running_recs, i)
                    day_plan["activities"].append({
                        "type": "running", 
                        "session": session_type,
                        "duration_minutes": self._calculate_session_duration(session_type, "running", volume_modifier),
                        "pace_guidance": self._get_pace_guidance(session_type, running_recs),
                        "distance_guidance": distance_guidance,
                        "notes": self._get_session_notes(session_type, "running")
                    })
                elif running_recs.get("distance_zones"):
                    # Running day with distance guidance only (no pace data)
                    session_type = self._select_session_type(running_recs, i, wellness)
                    distance_guidance = self._get_distance_guidance(session_type, running_recs, i)
                    day_plan["activities"].append({
                        "type": "running",
                        "session": session_type, 
                        "duration_minutes": self._calculate_session_duration(session_type, "running", volume_modifier),
                        "distance_guidance": distance_guidance,
                        "notes": self._get_session_notes(session_type, "running") + " (Use effort-based pacing)"
                    })
            
            # Add recovery recommendations
            if wellness["status"] in ["fair", "poor"] or workload["risk_level"] == "high":
                day_plan["recovery_focus"] = True
                day_plan["wellness_note"] = "Prioritize recovery - consider rest day or easy activity only"
            
            daily_plan.append(day_plan)
        
        return daily_plan
    
    def _select_session_type(self, activity_recs: Dict, day_index: int, wellness: Dict) -> str:
        """Select appropriate session type based on day and status."""
        recommended_sessions = activity_recs.get("recommended_sessions", ["aerobic"])
        
        # Vary session types across the week
        if day_index == 0:  # Day 1 - moderate
            return recommended_sessions[0] if len(recommended_sessions) > 0 else "aerobic"
        elif day_index == 2:  # Day 3 - harder if wellness allows
            if wellness["status"] in ["excellent", "good"] and len(recommended_sessions) > 1:
                return recommended_sessions[1]
            else:
                return recommended_sessions[0]
        elif day_index == 4:  # Day 5 - longer/easier
            return "aerobic" if "aerobic" in recommended_sessions else recommended_sessions[0]
        else:
            return recommended_sessions[0]
    
    def _calculate_session_duration(self, session_type: str, activity_type: str, volume_modifier: float) -> int:
        """Calculate session duration based on type and modifiers."""
        base_durations = {
            "cycling": {
                "recovery": 60,
                "aerobic": 90,
                "tempo": 75,
                "threshold": 60,
                "vo2max": 45,
                "interval": 45
            },
            "running": {
                "easy": 45,
                "aerobic": 60,
                "tempo": 40,
                "threshold": 35,
                "interval": 30
            }
        }
        
        base_duration = base_durations.get(activity_type, {}).get(session_type, 60)
        return int(base_duration * volume_modifier)
    
    def _get_session_intensity(self, session_type: str, cycling_recs: Dict) -> Dict[str, Any]:
        """Get intensity guidance for cycling sessions."""
        if "power_zones" in cycling_recs:
            zones = cycling_recs["power_zones"]
            if session_type in zones:
                power_range = zones[session_type]
                return {
                    "power_range_watts": power_range,
                    "zone": session_type
                }
        
        return {"guidance": f"Maintain {session_type} effort level"}
    
    def _get_pace_guidance(self, session_type: str, running_recs: Dict) -> Dict[str, Any]:
        """Get pace guidance for running sessions."""
        if "pace_zones" in running_recs:
            zones = running_recs["pace_zones"]
            if session_type in zones:
                return {
                    "target_pace_min_km": zones[session_type],
                    "zone": session_type
                }
        
        return {"guidance": f"Maintain {session_type} effort level"}
    
    def _get_distance_guidance(self, session_type: str, running_recs: Dict, day_index: int) -> Dict[str, Any]:
        """Get distance guidance for running sessions."""
        if "distance_zones" not in running_recs:
            return {"guidance": "Distance guidance unavailable"}
        
        distance_zones = running_recs["distance_zones"]
        
        # Special handling for long runs (typically day 4 - weekend long run)
        if day_index == 4 or session_type == "aerobic":
            # Weekend long run - use larger aerobic range
            if "aerobic" in distance_zones:
                zone_data = distance_zones["aerobic"]
                return {
                    "min_km": zone_data["min_km"],
                    "max_km": zone_data["max_km"], 
                    "recommended_km": zone_data["recommended_km"],
                    "range_description": f"{zone_data['min_km']:.1f}-{zone_data['max_km']:.1f}km",
                    "session_note": "Long aerobic base building run"
                }
        
        # Regular session distance
        if session_type in distance_zones:
            zone_data = distance_zones[session_type]
            return {
                "min_km": zone_data["min_km"],
                "max_km": zone_data["max_km"],
                "recommended_km": zone_data["recommended_km"], 
                "range_description": f"{zone_data['min_km']:.1f}-{zone_data['max_km']:.1f}km",
                "session_note": self._get_distance_session_note(session_type, zone_data)
            }
        
        # Fallback to easy/aerobic zone
        if "easy" in distance_zones:
            zone_data = distance_zones["easy"]
            return {
                "min_km": zone_data["min_km"],
                "max_km": zone_data["max_km"],
                "recommended_km": zone_data["recommended_km"],
                "range_description": f"{zone_data['min_km']:.1f}-{zone_data['max_km']:.1f}km",
                "session_note": "Easy effort distance"
            }
        
        return {"guidance": "Use perceived exertion for distance"}
    
    def _get_distance_session_note(self, session_type: str, zone_data: Dict) -> str:
        """Generate session-specific distance notes."""
        notes = {
            "easy": f"Recovery distance - aim for {zone_data['recommended_km']:.1f}km at comfortable pace",
            "aerobic": f"Base building distance - target {zone_data['recommended_km']:.1f}km, build aerobic capacity", 
            "tempo": f"Sustained effort over {zone_data['recommended_km']:.1f}km - comfortably hard pace",
            "threshold": f"Quality {zone_data['recommended_km']:.1f}km - hard but controlled effort",
            "interval": f"Shorter distance {zone_data['recommended_km']:.1f}km with high-intensity intervals"
        }
        return notes.get(session_type, f"Target {zone_data['recommended_km']:.1f}km for this session")
    
    def _get_session_notes(self, session_type: str, activity_type: str) -> str:
        """Generate helpful notes for each session type."""
        notes = {
            "cycling": {
                "recovery": "Easy spinning, focus on pedaling efficiency",
                "aerobic": "Steady conversational pace, build aerobic base",
                "tempo": "Comfortably hard, sustainable for 20-60 minutes",
                "threshold": "Hard but controlled, 20-40 minute intervals",
                "vo2max": "High intensity, 3-8 minute intervals",
                "interval": "Near maximal efforts, 30 seconds to 3 minutes"
            },
            "running": {
                "easy": "Conversational pace, nose breathing",
                "aerobic": "Comfortable effort, can speak in sentences",
                "tempo": "Comfortably hard, sustainable pace",
                "threshold": "Hard but controlled, race pace effort",
                "interval": "High intensity, short recoveries"
            }
        }
        
        return notes.get(activity_type, {}).get(session_type, "Follow perceived exertion")
    
    def _calculate_cycling_hours_target(self, historical: Dict, workload: Dict) -> float:
        """Calculate weekly cycling hours target."""
        if "weekly_loads" in historical and historical["cycling_percentage"] > 0:
            recent_cycling_load = historical["recent_weekly_average"] * historical["cycling_percentage"]
            # Convert UTL to approximate hours (rough conversion)
            hours_estimate = recent_cycling_load / 60  # Assume ~60 UTL per hour
            return max(hours_estimate * 1.1, 3.0)  # Small progression, min 3 hours
        return 5.0  # Default
    
    def _calculate_running_km_target(self, historical: Dict, workload: Dict) -> float:
        """Calculate weekly running kilometer target based on historical data."""
        if "weekly_loads" in historical and historical["running_percentage"] > 0:
            # Use more robust calculation to handle outliers
            weekly_loads = historical["weekly_loads"]
            recent_running_loads = []
            
            # Get running loads from recent weeks, excluding outlier weeks
            for week_key in sorted(weekly_loads.keys(), reverse=True)[:8]:  # Last 8 weeks
                running_load = weekly_loads[week_key]["running"]
                if running_load > 0:
                    recent_running_loads.append(running_load)
            
            if recent_running_loads:
                # Remove extreme outliers (more than 2.5x median)
                median_load = np.median(recent_running_loads)
                filtered_loads = [load for load in recent_running_loads if load <= median_load * 2.5]
                
                if filtered_loads:
                    avg_weekly_running_load = np.mean(filtered_loads)
                else:
                    avg_weekly_running_load = median_load
                
                # More conservative UTL to km conversion based on typical training
                # Easy pace: ~8-10 UTL per km, Mixed training: ~12-15 UTL per km
                # Use 12 UTL/km as middle ground for mixed intensity training
                km_estimate = avg_weekly_running_load / 12.0
                
                # Apply conservative progression rules
                if workload["risk_level"] == "high":
                    return max(km_estimate * 0.9, 15.0)  # Reduce volume if high risk
                elif workload["risk_level"] == "moderate":
                    return max(km_estimate * 1.05, 18.0)  # Conservative progression  
                else:
                    return max(km_estimate * 1.1, 20.0)  # 10% progression, min 20km
        
        return 30.0  # Default for new runners
    
    def _calculate_distance_zones(self, weekly_km: float, wellness_modifier: float, long_run_analysis: Dict) -> Dict[str, Dict[str, float]]:
        """Calculate session-specific distance ranges based on training science and historical patterns."""
        # Adjust weekly target by wellness modifier
        adjusted_weekly_km = weekly_km * wellness_modifier
        
        # Get historical long run insights
        typical_long_run_km = long_run_analysis.get("typical_long_run_km", 8.0)
        max_historical_km = long_run_analysis.get("max_historical_km", 12.0)
        
        # Science-based session distribution
        distance_zones = {
            "easy": {
                "min_km": max(3.0, adjusted_weekly_km * 0.15),  # 15% of weekly, min 3km
                "max_km": min(adjusted_weekly_km * 0.30, 12.0),  # 30% of weekly, max 12km
                "recommended_km": adjusted_weekly_km * 0.22  # 22% sweet spot
            },
            "aerobic": {
                "min_km": max(4.0, adjusted_weekly_km * 0.18),  # 18% of weekly, min 4km
                "max_km": min(adjusted_weekly_km * 0.35, 15.0),  # 35% of weekly, max 15km
                "recommended_km": adjusted_weekly_km * 0.25  # 25% sweet spot
            },
            "tempo": {
                "min_km": max(3.0, adjusted_weekly_km * 0.12),  # 12% of weekly, min 3km
                "max_km": min(adjusted_weekly_km * 0.25, 10.0),  # 25% of weekly, max 10km
                "recommended_km": adjusted_weekly_km * 0.18  # 18% sweet spot
            },
            "threshold": {
                "min_km": max(3.0, adjusted_weekly_km * 0.10),  # 10% of weekly, min 3km
                "max_km": min(adjusted_weekly_km * 0.20, 8.0),   # 20% of weekly, max 8km
                "recommended_km": adjusted_weekly_km * 0.15  # 15% sweet spot
            },
            "interval": {
                "min_km": max(2.0, adjusted_weekly_km * 0.08),  # 8% of weekly, min 2km
                "max_km": min(adjusted_weekly_km * 0.15, 6.0),   # 15% of weekly, max 6km
                "recommended_km": adjusted_weekly_km * 0.12  # 12% sweet spot
            },
            "long_run": {
                # Use historical patterns to set more appropriate long run targets
                # Base on historical patterns but constrain for safety
                "min_km": max(8.0, typical_long_run_km * 0.85),  # 85% of typical, minimum 8km
                "max_km": max(15.0, min(typical_long_run_km * 1.15, adjusted_weekly_km * 0.50)),  # 115% of typical or 50% weekly, min 15km
                "recommended_km": max(10.0, typical_long_run_km * 0.95)  # 95% of typical, minimum 10km
            }
        }
        
        # Round to reasonable increments (0.5km precision)
        for session_type in distance_zones:
            for key in distance_zones[session_type]:
                distance_zones[session_type][key] = round(distance_zones[session_type][key] * 2) / 2
        
        return distance_zones
    
    def _analyze_historical_long_runs(self, historical: Dict) -> Dict[str, float]:
        """Analyze historical running activities to identify typical long run patterns."""
        if "activity_patterns" not in historical or "running" not in historical["activity_patterns"]:
            return {"typical_long_run_km": 10.0}
        
        running_activities = historical["activity_patterns"]["running"]
        
        # Convert durations to estimated distances (assuming average pace)
        # Use 5:30/km (5.5 min/km) as a reasonable long run pace estimate
        estimated_distances = []
        for activity in running_activities:
            duration_minutes = activity["duration"] / 60.0
            # Estimate distance: duration / pace_per_km
            estimated_km = duration_minutes / 5.5  # 5.5 min/km pace
            
            # Filter out extreme outliers (>35km estimated runs are likely data errors)
            if estimated_km <= 35.0:
                estimated_distances.append(estimated_km)
        
        if not estimated_distances:
            return {"typical_long_run_km": 10.0}
        
        # Remove outliers using median-based approach
        median_distance = np.median(estimated_distances)
        filtered_distances = [d for d in estimated_distances if d <= median_distance * 2.5]
        
        if not filtered_distances:
            return {"typical_long_run_km": 10.0}
        
        # Identify long runs as runs in the top 25% of distances
        sorted_distances = sorted(filtered_distances, reverse=True)
        top_25_percent_count = max(2, len(sorted_distances) // 4)
        long_runs = sorted_distances[:top_25_percent_count]
        
        if long_runs:
            typical_long_run = np.mean(long_runs)
            return {
                "typical_long_run_km": typical_long_run,
                "max_historical_km": max(long_runs),
                "long_run_count": len(long_runs)
            }
        
        return {"typical_long_run_km": 10.0}

    def _calculate_running_mileage_target(self, historical: Dict, workload: Dict) -> float:
        """Calculate weekly running mileage target."""
        if "weekly_loads" in historical and historical["running_percentage"] > 0:
            recent_running_load = historical["recent_weekly_average"] * historical["running_percentage"]
            # Convert UTL to approximate mileage (rough conversion)
            mileage_estimate = recent_running_load / 8  # Assume ~8 UTL per mile
            return max(mileage_estimate * 1.1, 15.0)  # Small progression, min 15 miles
        return 25.0  # Default
    
    def _get_polarized_distribution(self) -> Dict[str, float]:
        """Return polarized training distribution percentages."""
        return {
            "easy_aerobic": 0.80,  # 80% easy/aerobic
            "tempo_threshold": 0.15,  # 15% tempo/threshold
            "high_intensity": 0.05   # 5% high intensity
        }
    
    def _generate_safety_warnings(self, workload: Dict, wellness: Dict) -> List[str]:
        """Generate safety warnings based on analysis."""
        warnings = []
        
        if workload["risk_level"] == "high":
            warnings.append("⚠️ High injury risk: Current training load significantly exceeds safe progression")
            warnings.append("📉 Recommend reducing weekly volume by 20-30%")
        
        if wellness["status"] == "poor":
            warnings.append("🩺 Poor wellness markers detected: Prioritize sleep, nutrition, and stress management")
            warnings.append("😴 Consider additional rest days until wellness improves")
        
        if workload["acw_ratio"] > 1.4:
            warnings.append("🚨 Critical load spike: Take immediate rest day to prevent injury")
        
        if workload["risk_level"] == "detraining":
            warnings.append("📈 Training load too low: Gradually increase activity to maintain fitness")
        
        return warnings
    
    def _generate_weekly_summary(self, cycling_recs: Dict, running_recs: Dict) -> Dict[str, Any]:
        """Generate weekly training volume summary."""
        summary = {
            "targets": {},
            "distribution": {},
            "notes": []
        }
        
        # Cycling targets
        if cycling_recs.get("weekly_hours_target"):
            summary["targets"]["cycling_hours"] = cycling_recs["weekly_hours_target"]
            summary["notes"].append(f"🚴‍♂️ Target {cycling_recs['weekly_hours_target']:.1f} hours cycling per week")
        
        # Running targets  
        if running_recs.get("weekly_km_target"):
            weekly_km = running_recs["weekly_km_target"]
            summary["targets"]["running_km"] = weekly_km
            summary["notes"].append(f"🏃‍♂️ Target {weekly_km:.1f}km running per week")
            
            # Add distance distribution if available
            if "distance_zones" in running_recs:
                zones = running_recs["distance_zones"]
                if "long_run" in zones:
                    long_run_km = zones["long_run"]["recommended_km"]
                    summary["distribution"]["long_run_km"] = long_run_km
                    summary["notes"].append(f"📏 Include one long run of ~{long_run_km:.1f}km")
        
        # Training distribution
        summary["distribution"]["intensity"] = {
            "easy_aerobic": "80% of weekly volume",
            "moderate_tempo": "15% of weekly volume", 
            "high_intensity": "5% of weekly volume"
        }
        summary["notes"].append("⚖️ Follow 80/15/5 polarized training distribution")
        
        return summary
