# TrainingLoad - Product Requirements Document

## Executive Summary

TrainingLoad is an evidence-based training load monitoring system that transforms recreational athletes into data-driven training optimizers. By integrating Strava activity data with Intervals.icu wellness metrics, it provides personalized training recommendations that maximize performance gains while preventing overuse injuries.

**Target Users**: Serious recreational cyclists and runners who want coaching-level insights without the cost of a professional coach.

## Product Vision & Principles

### Vision Statement
To be the most intelligent and scientifically-grounded training companion for endurance athletes, providing daily, personalized training recommendations that maximize performance gains while proactively minimizing injury risk.

### Core Principles
1. **Science First**: Every recommendation traceable to established physiological principles and peer-reviewed research
2. **Individuality**: Dynamic, N-of-1 approach that adapts to unique physiology and training history  
3. **Proactive Prevention**: Injury prevention through intelligent load management, not just performance tracking
4. **Data-Driven**: Algorithmic decisions based on objective physiological markers

## Core Features & Capabilities

### 1. Unit Training Load (UTL) Calculation
**Scientific Foundation**: Combines TSS, rTSS, and TRIMP algorithms for universal training stress quantification.

**Key Features**:
- **Power-based TSS** for cycling activities with power meter data
- **Pace-based rTSS** for running activities with GPS pace data  
- **Heart rate TRIMP** as fallback with activity-specific scaling factors
- **Wellness modifiers** from HRV, sleep, and readiness data (0.8x - 1.1x range)

**Value Proposition**: Single "currency" for training stress across all activities, enabling accurate load management.

### 2. Acute:Chronic Workload Ratio (ACWR) - Injury Risk Assessment
**Scientific Foundation**: Validated method for predicting injury risk by comparing recent training load to longer-term averages.

**Key Features**:
- **Overall ACWR**: Combined load across all activities
- **Sport-specific ACWR**: Separate ratios for running, cycling, and other activities
- **Risk zones**: Color-coded assessment from detraining (<0.5) to high risk (>1.5)
- **Injury prevention**: Identifies hidden risks from activity transitions

**Value Proposition**: Prevents overuse injuries through early warning system based on sports medicine research.

### 3. Training Recommendations with Distance Guidance
**Scientific Foundation**: Evidence-based distance calculations using sports science research (Jack Daniels, Stephen Seiler).

**Key Features**:
- **Distance zones**: Easy/recovery, steady/tempo, long run/ride ranges
- **Historical analysis**: Realistic targets based on recent performance patterns
- **Outlier filtering**: Removes GPS errors and data anomalies for accurate recommendations
- **ACWR-adjusted targets**: Weekly volume guidance to maintain optimal training zones

**Value Proposition**: Provides specific, actionable training guidance with injury-safe volume recommendations.

### 4. Automated Threshold Detection & Updates
**Scientific Foundation**: Research-based methods for detecting physiological thresholds from activity data.

**Key Features**:
- **FTP detection**: Critical power analysis from cycling data
- **FTHP detection**: Critical speed analysis from running data
- **Heart rate thresholds**: Max HR and resting HR from activity and wellness data
- **Automatic updates**: Triggered by significant training or wellness changes

**Value Proposition**: Maintains accurate fitness tracking as performance evolves without manual testing.

### 5. Real-time Wellness Integration
**Scientific Foundation**: Integration of HRV, sleep, and readiness metrics as validated markers of recovery status.

**Key Features**:
- **Intervals.icu integration**: Automatic sync of wellness data
- **UTL modification**: Real-time adjustment of training stress based on recovery status
- **Resting HR updates**: Automatic calculation from 14-day wellness averages
- **Training adaptation**: Recommendations adjust based on current wellness state

**Value Proposition**: Personalized training that adapts to daily recovery status and life stress.

## Technical Architecture

### System Components
- **Backend**: FastAPI with SQLAlchemy ORM, PostgreSQL Cloud SQL
- **Frontend**: React with Vite build system
- **Authentication**: OAuth2 integration (Strava, Intervals.icu)
- **Background Processing**: APScheduler with enhanced 3.5-hour sync intervals
- **Deployment**: Google App Engine with Cloud Scheduler

### Data Flow
1. **Onboarding**: Strava OAuth → Initial threshold calculation → 90-day activity import
2. **Ongoing Sync**: 3.5-hour quick sync (activities + wellness) → UTL calculation → ACWR assessment
3. **Recommendations**: Historical analysis → Distance zone calculation → Risk-adjusted targets

### Key APIs
- **Training Recommendations**: `/recommendations/{user_id}` - Complete 5-day training prescription
- **Sync Management**: `/scheduler/jobs` - Background job monitoring and manual triggers
- **User Testing**: `/sync/test/{user_id}` - Individual sync verification

## User Experience Flow

### 1. Onboarding Process
**Duration**: 5-10 minutes
**Steps**:
1. **Strava Connection**: OAuth authentication with activity permissions
2. **Profile Setup**: Age, gender, injury history for personalized calculations
3. **Threshold Initialization**: Research-based calculation from existing activity data
4. **Activity Import**: 90-day historical import with progress tracking
5. **Wellness Integration** (Optional): Intervals.icu connection for enhanced recommendations

### 2. Daily Usage
**Primary Interface**: Dashboard with training recommendations
**Key Metrics**:
- **Today's UTL target** with distance guidance (e.g., "5-7km easy run, 45-55 UTL")
- **ACWR status** with risk assessment and trend visualization
- **Weekly load tracking** with progress toward targets
- **Wellness integration** showing HRV, sleep, and readiness impact

### 3. Long-term Engagement
**Weekly**: Automatic threshold updates and comprehensive data validation
**Monthly**: Full UTL recalculation for accuracy maintenance
**Ongoing**: Real-time sync keeps recommendations current with latest workouts

## Competitive Differentiation

### vs TrainingPeaks
- **Lower barrier to entry**: No manual TSS/CTL management required
- **Automated intelligence**: Self-updating thresholds and wellness integration
- **Injury focus**: ACWR-based recommendations prioritize injury prevention

### vs Strava Premium
- **Scientific depth**: Evidence-based algorithms vs basic fitness metrics
- **Actionable guidance**: Specific training prescriptions vs descriptive analytics
- **Cross-platform integration**: Combines Strava activities with Intervals.icu wellness

### vs Coaching Services
- **Cost efficiency**: $0 vs $200-500/month for professional coaching
- **24/7 availability**: Instant recommendations vs scheduled check-ins
- **Data consistency**: Algorithm-driven vs subjective human interpretation

## Success Metrics

### User Engagement
- **Daily active users**: Target 70% of registered users check recommendations weekly
- **Sync success rate**: >95% of scheduled background jobs complete successfully
- **Feature adoption**: >60% of users connect Intervals.icu for wellness integration

### Platform Performance  
- **Recommendation accuracy**: User satisfaction >4.5/5 for training guidance relevance
- **Injury prevention**: Users report 50% fewer overuse injuries compared to pre-platform training
- **Threshold accuracy**: Automated detection within ±5% of manual testing

### Technical Reliability
- **System uptime**: >99.5% availability for core recommendation APIs
- **Data freshness**: New activities appear in recommendations within 3.5 hours
- **Sync reliability**: <1% failure rate for Strava and Intervals.icu integrations

## Roadmap & Future Enhancements

### Phase 1 (Current): Core Training Intelligence
- ✅ UTL calculation with wellness modifiers
- ✅ ACWR-based injury risk assessment  
- ✅ Science-based distance recommendations
- ✅ Automated threshold detection

### Phase 2 (Next 3 months): Enhanced Personalization
- **Periodization planning**: Training plan generation for target events
- **Weather integration**: Recommendations adjust for temperature/conditions
- **Recovery tracking**: Sleep debt and HRV trend analysis
- **Performance prediction**: Race time estimates based on current fitness

### Phase 3 (6-12 months): Advanced Features
- **Workout library**: Structured training sessions with UTL targets
- **Team/group features**: Shared training insights for clubs and teams
- **Nutrition integration**: Caloric expenditure and fueling recommendations
- **Advanced analytics**: Power curve analysis and VO2 max estimation

### Phase 4 (12+ months): Platform Expansion
- **Multi-sport support**: Swimming, strength training, yoga integration
- **Wearable partnerships**: Direct integration with Garmin, Polar, Wahoo devices
- **Coaching marketplace**: Connect with certified coaches for advanced users
- **Research platform**: Anonymized data for exercise physiology research

## Technical Requirements

### Performance Requirements
- **API Response Time**: <500ms for recommendation generation
- **Background Processing**: 3.5-hour sync cycle with <5 minute execution time
- **Database Performance**: Support for 10,000+ users with sub-second queries

### Security Requirements
- **OAuth2 Compliance**: Secure token management for third-party integrations
- **Data Encryption**: All PII encrypted at rest and in transit
- **GDPR Compliance**: User data export, deletion, and consent management

### Scalability Requirements
- **User Growth**: Architecture supports 100,000+ users without redesign
- **Data Volume**: Handle 1M+ activities with real-time processing
- **Geographic Distribution**: Multi-region deployment capability

---

**Document Version**: 2.0  
**Last Updated**: September 5, 2025  
**Next Review**: December 2025

*This PRD represents the complete vision for TrainingLoad as an evidence-based training optimization platform that transforms serious recreational athletes into data-driven training optimizers while preventing injury through intelligent load management.*
