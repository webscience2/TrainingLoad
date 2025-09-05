import React, { useState, useEffect } from 'react';

const TrainingRecommendations = ({ userId }) => {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, [userId]);

  const fetchRecommendations = async () => {
    if (!userId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/recommendations/${userId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setRecommendations(data.data);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getWellnessStatusIcon = (status) => {
    const icons = {
      excellent: '✅',
      good: '🟢', 
      fair: '🟡',
      poor: '🔴',
      unknown: '⚪'
    };
    return icons[status] || icons.unknown;
  };

  const getWellnessStatusColor = (status) => {
    const colors = {
      excellent: { background: '#e8f5e8', color: '#2e7d32', border: '1px solid #a5d6a7' },
      good: { background: '#e3f2fd', color: '#1565c0', border: '1px solid #90caf9' },
      fair: { background: '#fff8e1', color: '#ef6c00', border: '1px solid #ffcc02' },
      poor: { background: '#ffebee', color: '#c62828', border: '1px solid #ef5350' },
      unknown: { background: '#f5f5f5', color: '#616161', border: '1px solid #bdbdbd' }
    };
    return colors[status] || colors.unknown;
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      low: { background: '#e8f5e8', color: '#2e7d32' },
      moderate: { background: '#fff8e1', color: '#ef6c00' },
      high: { background: '#ffebee', color: '#c62828' },
      detraining: { background: '#e3f2fd', color: '#1565c0' }
    };
    return colors[riskLevel] || { background: '#f5f5f5', color: '#616161' };
  };

  const formatPace = (paceMinKm) => {
    if (!paceMinKm) return '';
    const minutes = Math.floor(paceMinKm);
    const seconds = Math.round((paceMinKm - minutes) * 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}/km`;
  };

  const formatPower = (powerRange) => {
    if (!powerRange || !Array.isArray(powerRange)) return '';
    return `${Math.round(powerRange[0])}-${Math.round(powerRange[1])}W`;
  };

  if (loading) {
    return (
      <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⚡ Training Recommendations
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 0' }}>
          <div style={{ 
            width: '32px', 
            height: '32px', 
            border: '3px solid #f3f3f3', 
            borderTop: '3px solid #1976d2', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite',
            marginRight: '1rem'
          }}></div>
          <span style={{ color: '#666' }}>Analyzing your training data...</span>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⚡ Training Recommendations
        </h3>
        <div style={{ background: '#ffebee', border: '1px solid #ef5350', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span>⚠️</span>
            <strong style={{ color: '#c62828' }}>Unable to Generate Recommendations</strong>
          </div>
          <p style={{ margin: 0, color: '#c62828' }}>{error}</p>
        </div>
        <button
          onClick={fetchRecommendations}
          style={{ 
            padding: '0.5rem 1rem', 
            background: '#1976d2', 
            color: 'white', 
            border: 'none', 
            borderRadius: '6px', 
            cursor: 'pointer' 
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!recommendations) {
    return null;
  }

  const { wellness_status, workload_analysis, daily_plan, safety_warnings } = recommendations;

  return (
    <div style={{ width: '100%' }}>
      <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#1976d2', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            ⚡ Training Recommendations
          </h3>
          <p style={{ margin: 0, color: '#666', fontSize: '0.9rem' }}>
            Science-based 5-day training plan personalized to your data
          </p>
        </div>
        
        {/* Safety Warnings */}
        {safety_warnings && safety_warnings.length > 0 && (
          <div style={{ 
            background: '#ffebee', 
            border: '1px solid #ef5350', 
            padding: '1rem', 
            borderRadius: '8px', 
            marginBottom: '1.5rem' 
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span>⚠️</span>
              <strong style={{ color: '#c62828' }}>Safety Alerts</strong>
            </div>
            <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem', color: '#c62828' }}>
              {safety_warnings.map((warning, idx) => (
                <li key={idx} style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Current Status Overview */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ 
            border: '1px solid #e0e0e0', 
            borderRadius: '8px', 
            padding: '1rem',
            background: '#fafafa'
          }}>
            <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', color: '#666', fontWeight: '500' }}>
              Wellness Status
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.2rem' }}>{getWellnessStatusIcon(wellness_status?.status)}</span>
              <span style={{ 
                padding: '0.25rem 0.5rem', 
                borderRadius: '4px', 
                fontSize: '0.8rem', 
                fontWeight: '500',
                ...getWellnessStatusColor(wellness_status?.status)
              }}>
                {wellness_status?.status?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            {wellness_status?.note && (
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#666' }}>{wellness_status.note}</p>
            )}
          </div>

          <div style={{ 
            border: '1px solid #e0e0e0', 
            borderRadius: '8px', 
            padding: '1rem',
            background: '#fafafa'
          }}>
            <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem', color: '#666', fontWeight: '500' }}>
              Training Load Risk
            </h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.2rem' }}>📊</span>
              <span style={{ 
                padding: '0.25rem 0.5rem', 
                borderRadius: '4px', 
                fontSize: '0.8rem', 
                fontWeight: '500',
                ...getRiskLevelColor(workload_analysis?.risk_level)
              }}>
                {workload_analysis?.risk_level?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            {workload_analysis?.risk_note && (
              <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#666' }}>{workload_analysis.risk_note}</p>
            )}
            {workload_analysis?.acw_ratio && (
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#999' }}>
                Acute:Chronic Ratio: {workload_analysis.acw_ratio.toFixed(2)}
              </p>
            )}
          </div>
        </div>

        {/* Weekly Training Summary */}
        {recommendations.weekly_summary && (
          <div style={{ 
            border: '1px solid #e0e0e0', 
            borderRadius: '8px', 
            padding: '1rem', 
            marginBottom: '1.5rem',
            background: '#f8f9fa'
          }}>
            <h4 style={{ 
              margin: '0 0 0.75rem 0', 
              fontSize: '0.95rem', 
              color: '#333', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              📊 Weekly Volume Targets
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {recommendations.weekly_summary.targets?.running_km && (
                <div style={{ 
                  background: 'white', 
                  padding: '0.75rem', 
                  borderRadius: '6px', 
                  border: '1px solid #e8f5e8',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{ fontSize: '1.2rem' }}>🏃‍♂️</span>
                  <div>
                    <div style={{ fontWeight: '600', color: '#2e7d32', fontSize: '1.1rem' }}>
                      {recommendations.weekly_summary.targets.running_km.toFixed(1)}km
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#666' }}>Running per week</div>
                  </div>
                </div>
              )}
              
              {recommendations.weekly_summary.targets?.cycling_hours && (
                <div style={{ 
                  background: 'white', 
                  padding: '0.75rem', 
                  borderRadius: '6px', 
                  border: '1px solid #e3f2fd',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{ fontSize: '1.2rem' }}>🚴‍♂️</span>
                  <div>
                    <div style={{ fontWeight: '600', color: '#1565c0', fontSize: '1.1rem' }}>
                      {recommendations.weekly_summary.targets.cycling_hours.toFixed(1)}h
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#666' }}>Cycling per week</div>
                  </div>
                </div>
              )}
              
              {recommendations.weekly_summary.distribution?.long_run_km && (
                <div style={{ 
                  background: 'white', 
                  padding: '0.75rem', 
                  borderRadius: '6px', 
                  border: '1px solid #fff3e0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{ fontSize: '1.2rem' }}>📏</span>
                  <div>
                    <div style={{ fontWeight: '600', color: '#ef6c00', fontSize: '1.1rem' }}>
                      {recommendations.weekly_summary.distribution.long_run_km.toFixed(1)}km
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#666' }}>Long run target</div>
                  </div>
                </div>
              )}
            </div>
            
            {recommendations.weekly_summary.notes && recommendations.weekly_summary.notes.length > 0 && (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(25, 118, 210, 0.05)', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', color: '#1976d2', fontWeight: '500', marginBottom: '0.5rem' }}>
                  💡 Training Guidelines:
                </div>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#666' }}>
                  {recommendations.weekly_summary.notes.map((note, idx) => (
                    <li key={idx} style={{ marginBottom: '0.25rem' }}>
                      {note.replace(/^[🏃‍♂️🚴‍♂️📏⚖️]\s*/, '')}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* 5-Day Training Plan */}
        <div>
          <h3 style={{ 
            fontSize: '1.1rem', 
            fontWeight: '600', 
            marginBottom: '1rem', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem',
            color: '#333'
          }}>
            📅 5-Day Training Plan
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {daily_plan?.map((day, idx) => (
              <div 
                key={idx} 
                style={{ 
                  border: '1px solid #e0e0e0', 
                  borderRadius: '8px',
                  background: day.recovery_focus ? '#fff8e1' : 'white',
                  borderColor: day.recovery_focus ? '#ffcc02' : '#e0e0e0'
                }}
              >
                <div style={{ padding: '1rem 1rem 0.5rem 1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: '500' }}>
                      {day.day} - {new Date(day.date).toLocaleDateString()}
                    </h4>
                    {day.recovery_focus && (
                      <span style={{ 
                        background: '#fff8e1', 
                        color: '#ef6c00', 
                        padding: '0.25rem 0.5rem', 
                        borderRadius: '4px', 
                        fontSize: '0.75rem',
                        border: '1px solid #ffcc02'
                      }}>
                        Recovery Focus
                      </span>
                    )}
                  </div>
                </div>
                
                <div style={{ padding: '0 1rem 1rem 1rem' }}>
                  {day.activities?.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {day.activities.map((activity, actIdx) => (
                        <div key={actIdx} style={{ padding: '0.75rem', background: '#f8f9fa', borderRadius: '6px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '1rem' }}>🏃</span>
                            <span style={{ fontWeight: '500', textTransform: 'capitalize' }}>{activity.type}</span>
                            <span style={{ 
                              border: '1px solid #ddd', 
                              padding: '0.15rem 0.4rem', 
                              borderRadius: '3px', 
                              fontSize: '0.7rem',
                              background: 'white'
                            }}>
                              {activity.session}
                            </span>
                          </div>
                          
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <span>⏱️</span>
                              <span>{activity.duration_minutes} minutes</span>
                            </div>
                            
                            {activity.intensity?.power_range_watts && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <span>⚡</span>
                                <span>{formatPower(activity.intensity.power_range_watts)}</span>
                              </div>
                            )}
                            
                            {activity.pace_guidance?.target_pace_min_km && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <span>❤️</span>
                                <span>{formatPace(activity.pace_guidance.target_pace_min_km)}</span>
                              </div>
                            )}
                            
                            {activity.distance_guidance?.range_description && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <span>📏</span>
                                <span style={{ fontWeight: '500' }}>
                                  {activity.distance_guidance.range_description}
                                </span>
                              </div>
                            )}
                          </div>
                          
                          {activity.notes && (
                            <p style={{ 
                              margin: '0.5rem 0 0 0', 
                              fontSize: '0.8rem', 
                              color: '#666', 
                              fontStyle: 'italic' 
                            }}>
                              💡 {activity.notes}
                            </p>
                          )}
                          
                          {activity.distance_guidance?.session_note && (
                            <p style={{ 
                              margin: '0.25rem 0 0 0', 
                              fontSize: '0.8rem', 
                              color: '#2e7d32',
                              fontStyle: 'italic',
                              backgroundColor: '#f1f8e9',
                              padding: '0.5rem',
                              borderRadius: '4px',
                              border: '1px solid #c8e6c9'
                            }}>
                              📏 {activity.distance_guidance.session_note}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '1rem 0', color: '#999' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: '0.5' }}>🛌</div>
                      <p style={{ margin: '0 0 0.25rem 0', fontWeight: '500' }}>Rest Day</p>
                      <p style={{ margin: 0, fontSize: '0.85rem' }}>Recovery and adaptation</p>
                    </div>
                  )}
                  
                  {day.wellness_note && (
                    <div style={{ 
                      background: '#fff8e1', 
                      border: '1px solid #ffcc02', 
                      padding: '0.75rem', 
                      borderRadius: '6px',
                      marginTop: '0.75rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.9rem' }}>⚠️</span>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: '#ef6c00' }}>
                          {day.wellness_note}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Refresh Button */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
          <button
            onClick={fetchRecommendations}
            style={{ 
              padding: '0.75rem 1.5rem', 
              background: '#1976d2', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '500'
            }}
            onMouseOver={(e) => e.target.style.background = '#1565c0'}
            onMouseOut={(e) => e.target.style.background = '#1976d2'}
          >
            Refresh Recommendations
          </button>
        </div>
        
      </div>
    </div>
  );
};

export default TrainingRecommendations;
