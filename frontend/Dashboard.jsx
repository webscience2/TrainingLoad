import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function Dashboard({ user, onLogout }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingThresholds, setEditingThresholds] = useState(false);
  const [showUtlModal, setShowUtlModal] = useState(false);
  const [thresholdOverrides, setThresholdOverrides] = useState({
    ftp_watts: '',
    fthp_mps: '',
    max_hr: '',
    resting_hr: ''
  });
  
  // Intervals.icu state
  const [intervalsConnected, setIntervalsConnected] = useState(false);
  const [intervalsApiKey, setIntervalsApiKey] = useState('');
  const [intervalsUserId, setIntervalsUserId] = useState('');
  const [showIntervalsConnect, setShowIntervalsConnect] = useState(false);
  const [wellnessData, setWellnessData] = useState(null);
  const [syncingWellness, setSyncingWellness] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    checkIntervalsConnection();
  }, [user]);

  useEffect(() => {
    if (intervalsConnected) {
      fetchWellnessData();
    }
  }, [intervalsConnected]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/dashboard/${user.user_id}`);
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleThresholdUpdate = async () => {
    try {
      const payload = {};
      Object.keys(thresholdOverrides).forEach(key => {
        if (thresholdOverrides[key] !== '') {
          payload[key] = parseFloat(thresholdOverrides[key]);
        }
      });

      const response = await fetch(`http://localhost:8000/dashboard/${user.user_id}/thresholds`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('Failed to update thresholds');

      // Reset form and refresh data
      setThresholdOverrides({ ftp_watts: '', fthp_mps: '', max_hr: '', resting_hr: '' });
      setEditingThresholds(false);
      await fetchDashboardData();
    } catch (err) {
      setError(err.message);
    }
  };

  // Intervals.icu functions
  const checkIntervalsConnection = async () => {
    try {
      const response = await fetch(`http://localhost:8000/intervals/connection_status/${user.user_id}`);
      if (response.ok) {
        const data = await response.json();
        setIntervalsConnected(data.connected);
        if (data.connected && data.user_id) {
          setIntervalsUserId(data.user_id);
        }
      }
    } catch (error) {
      console.error('Error checking intervals connection:', error);
    }
  };

  const handleIntervalsConnect = async () => {
    try {
      const response = await fetch(`http://localhost:8000/intervals/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.user_id,
          api_key: intervalsApiKey,
          intervals_user_id: intervalsUserId
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setIntervalsConnected(true);
        setShowIntervalsConnect(false);
        setIntervalsApiKey('');
        alert('Successfully connected to intervals.icu!');
        await fetchWellnessData();
      } else {
        alert(data.detail || 'Failed to connect to intervals.icu');
      }
    } catch (error) {
      console.error('Error connecting to intervals:', error);
      alert('Failed to connect to intervals.icu. Please try again.');
    }
  };

  const handleIntervalsDisconnect = async () => {
    try {
      const response = await fetch(`http://localhost:8000/intervals/disconnect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.user_id
        }),
      });

      if (response.ok) {
        setIntervalsConnected(false);
        setWellnessData(null);
        alert('Disconnected from intervals.icu');
      }
    } catch (error) {
      console.error('Error disconnecting from intervals:', error);
      alert('Failed to disconnect from intervals.icu');
    }
  };

  const fetchWellnessData = async () => {
    if (!intervalsConnected) return;
    
    try {
      const response = await fetch(`http://localhost:8000/intervals/wellness/${user.user_id}?days=91`);
      if (response.ok) {
        const data = await response.json();
        setWellnessData(data);
      }
    } catch (error) {
      console.error('Error fetching wellness data:', error);
    }
  };

  const syncWellnessData = async () => {
    setSyncingWellness(true);
    try {
      // Use query parameters instead of JSON body, and sync 3 months of data
      const response = await fetch(`http://localhost:8000/intervals/sync_wellness?user_id=${user.user_id}&days=91`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const result = await response.json();
        await fetchWellnessData();
        alert(result.message || 'Wellness data sync started for last 3 months!');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to sync wellness data');
      }
    } catch (error) {
      console.error('Error syncing wellness data:', error);
      alert('Failed to sync wellness data');
    } finally {
      setSyncingWellness(false);
    }
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatDistance = (meters) => {
    return `${(meters / 1000).toFixed(1)} km`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <div>Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#d32f2f' }}>
        <div>Error: {error}</div>
        <button onClick={fetchDashboardData} style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#1976d2', color: 'white', border: 'none', borderRadius: '4px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (!dashboardData) return null;

  const { activity_summary, training_totals, thresholds, recent_activities } = dashboardData;

  // Prepare chart data
  const chartData = recent_activities.slice(0, 7).reverse().map(activity => ({
    date: formatDate(activity.start_date),
    distance: (activity.distance / 1000).toFixed(1),
    utl: activity.utl_score || 0
  }));

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', background: '#f5f5f5', minHeight: '100vh', padding: '1rem' }}>
      {/* Header */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <div>
            <h1 style={{ margin: 0, color: '#1976d2', fontSize: '2rem', fontWeight: '700' }}>Training Dashboard</h1>
            <p style={{ margin: '0.5rem 0', color: '#666' }}>Welcome back, {user.name || 'Athlete'}!</p>
          </div>
          <button
            onClick={onLogout}
            style={{ padding: '0.5rem 1rem', background: '#d32f2f', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Training Totals */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
        <h2 style={{ color: '#333', marginBottom: '1rem' }}>Training Totals</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          {Object.entries(training_totals).map(([period, data]) => (
            <div key={period} style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2', textTransform: 'capitalize' }}>
                {period.replace('_', ' ')}
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div><strong>{data.activities}</strong> activities</div>
                <div><strong>{formatDistance(data.distance)}</strong></div>
                <div><strong>{formatDuration(data.moving_time)}</strong></div>
                <div><strong>{data.elevation_gain}m</strong> elevation</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts and Activity Summary */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
          {/* Charts */}
          <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2' }}>Recent Training Load</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="utl" stroke="#1976d2" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Activity Summary */}
          <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2' }}>Activity Summary</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Total Activities:</span>
                <strong>{activity_summary.total_activities}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Total Distance:</span>
                <strong>{formatDistance(activity_summary.total_distance)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Total Time:</span>
                <strong>{formatDuration(activity_summary.total_moving_time)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Avg Pace:</span>
                <strong>{activity_summary.avg_pace.toFixed(1)} min/km</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Elevation Gain:</span>
                <strong>{activity_summary.total_elevation_gain}m</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Thresholds */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
        <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#1976d2' }}>Training Thresholds</h3>
            <button
              onClick={() => setEditingThresholds(!editingThresholds)}
              style={{ padding: '0.5rem 1rem', background: editingThresholds ? '#d32f2f' : '#1976d2', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
            >
              {editingThresholds ? 'Cancel' : 'Edit'}
            </button>
          </div>

          {editingThresholds ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>FTP (Watts)</label>
                <input
                  type="number"
                  value={thresholdOverrides.ftp_watts}
                  onChange={(e) => setThresholdOverrides({...thresholdOverrides, ftp_watts: e.target.value})}
                  placeholder={thresholds.ftp_watts || 'Enter FTP'}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>FThP (m/s)</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholdOverrides.fthp_mps}
                  onChange={(e) => setThresholdOverrides({...thresholdOverrides, fthp_mps: e.target.value})}
                  placeholder={thresholds.fthp_mps || 'Enter FThP'}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Max HR (bpm)</label>
                <input
                  type="number"
                  value={thresholdOverrides.max_hr}
                  onChange={(e) => setThresholdOverrides({...thresholdOverrides, max_hr: e.target.value})}
                  placeholder={thresholds.max_hr || 'Enter Max HR'}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Resting HR (bpm)</label>
                <input
                  type="number"
                  value={thresholdOverrides.resting_hr}
                  onChange={(e) => setThresholdOverrides({...thresholdOverrides, resting_hr: e.target.value})}
                  placeholder={thresholds.resting_hr || 'Enter Resting HR'}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div style={{ gridColumn: 'span 4', display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button
                  onClick={handleThresholdUpdate}
                  style={{ padding: '0.5rem 1rem', background: '#388e3c', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                >
                  Save Changes
                </button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1976d2' }}>{thresholds.ftp_watts || 'N/A'}</div>
                <div style={{ color: '#666', fontSize: '0.9rem' }}>FTP (Watts)</div>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1976d2' }}>{thresholds.fthp_mps ? thresholds.fthp_mps.toFixed(1) : 'N/A'}</div>
                <div style={{ color: '#666', fontSize: '0.9rem' }}>FThP (m/s)</div>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1976d2' }}>{thresholds.max_hr || 'N/A'}</div>
                <div style={{ color: '#666', fontSize: '0.9rem' }}>Max HR (bpm)</div>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1976d2' }}>{thresholds.resting_hr || 'N/A'}</div>
                <div style={{ color: '#666', fontSize: '0.9rem' }}>Resting HR (bpm)</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Intervals.icu Integration */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
        <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#1976d2' }}>Intervals.icu Integration</h3>
            {intervalsConnected ? (
              <button
                onClick={handleIntervalsDisconnect}
                style={{ padding: '0.5rem 1rem', background: '#d32f2f', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={() => setShowIntervalsConnect(!showIntervalsConnect)}
                style={{ padding: '0.5rem 1rem', background: '#1976d2', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                Connect
              </button>
            )}
          </div>

          {intervalsConnected ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', padding: '1rem', background: '#e8f5e8', borderRadius: '8px' }}>
                <div style={{ width: '12px', height: '12px', background: '#4caf50', borderRadius: '50%' }}></div>
                <span style={{ color: '#2e7d32', fontWeight: '500' }}>
                  Connected to intervals.icu {intervalsUserId && `(User: ${intervalsUserId})`}
                </span>
              </div>

              {wellnessData && wellnessData.length > 0 ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h4 style={{ margin: 0, color: '#1976d2' }}>Recent Wellness Data</h4>
                    <button
                      onClick={syncWellnessData}
                      disabled={syncingWellness}
                      style={{ 
                        padding: '0.25rem 0.75rem', 
                        background: syncingWellness ? '#ccc' : '#388e3c', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '4px', 
                        cursor: syncingWellness ? 'not-allowed' : 'pointer',
                        fontSize: '0.85rem'
                      }}
                    >
                      {syncingWellness ? 'Syncing...' : 'Sync Data (3 months)'}
                    </button>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {wellnessData.slice(0, 1).map((data, index) => (
                      <div key={index} style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                        <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>
                          {new Date(data.date).toLocaleDateString()}
                        </div>
                        {data.hrv4_training && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1976d2' }}>{data.hrv4_training}</div>
                            <div style={{ fontSize: '0.75rem', color: '#666' }}>HRV4Training</div>
                          </div>
                        )}
                        {data.resting_hr && (
                          <div style={{ marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1976d2' }}>{data.resting_hr}</div>
                            <div style={{ fontSize: '0.75rem', color: '#666' }}>Resting HR</div>
                          </div>
                        )}
                        {data.sleep_hours && (
                          <div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1976d2' }}>{data.sleep_hours}h</div>
                            <div style={{ fontSize: '0.75rem', color: '#666' }}>Sleep</div>
                          </div>
                        )}
                      </div>
                    ))}
                    
                    {/* Summary stats from recent data */}
                    {wellnessData.length > 1 && (
                      <>
                        <div style={{ padding: '1rem', background: '#f0f8ff', borderRadius: '8px' }}>
                          <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>7-Day Average</div>
                          {wellnessData.filter(d => d.resting_hr).length > 0 && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1976d2' }}>
                                {Math.round(wellnessData.filter(d => d.resting_hr).reduce((sum, d) => sum + d.resting_hr, 0) / wellnessData.filter(d => d.resting_hr).length)}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: '#666' }}>Avg Resting HR</div>
                            </div>
                          )}
                          {wellnessData.filter(d => d.sleep_hours).length > 0 && (
                            <div>
                              <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1976d2' }}>
                                {(wellnessData.filter(d => d.sleep_hours).reduce((sum, d) => sum + d.sleep_hours, 0) / wellnessData.filter(d => d.sleep_hours).length).toFixed(1)}h
                              </div>
                              <div style={{ fontSize: '0.75rem', color: '#666' }}>Avg Sleep</div>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                  
                  <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#666' }}>
                    Last synced: {wellnessData[0] ? new Date(wellnessData[0].date).toLocaleDateString() : 'Never'}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                  <p>No wellness data available.</p>
                  <button
                    onClick={syncWellnessData}
                    disabled={syncingWellness}
                    style={{ 
                      padding: '0.5rem 1rem', 
                      background: syncingWellness ? '#ccc' : '#1976d2', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '6px', 
                      cursor: syncingWellness ? 'not-allowed' : 'pointer'
                    }}
                  >
                    {syncingWellness ? 'Syncing...' : 'Sync Wellness Data (3 months)'}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', padding: '1rem', background: '#fff3e0', borderRadius: '8px' }}>
                <div style={{ width: '12px', height: '12px', background: '#ff9800', borderRadius: '50%' }}></div>
                <span style={{ color: '#f57c00' }}>Not connected to intervals.icu</span>
              </div>
              
              {showIntervalsConnect && (
                <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '1rem', background: '#fafafa' }}>
                  <h4 style={{ margin: '0 0 1rem 0', color: '#1976d2' }}>Connect to Intervals.icu</h4>
                  <p style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: '#666' }}>
                    Connect your intervals.icu account to sync HRV, resting heart rate, sleep data, and other wellness metrics.
                  </p>
                  
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      Intervals.icu User ID:
                    </label>
                    <input
                      type="text"
                      value={intervalsUserId}
                      onChange={(e) => setIntervalsUserId(e.target.value)}
                      placeholder="e.g., i123456"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                      API Key:
                    </label>
                    <input
                      type="password"
                      value={intervalsApiKey}
                      onChange={(e) => setIntervalsApiKey(e.target.value)}
                      placeholder="Enter your intervals.icu API key"
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  
                  <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '1rem' }}>
                    Get your API key from <a href="https://intervals.icu/settings" target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>intervals.icu settings</a>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <button
                      onClick={handleIntervalsConnect}
                      disabled={!intervalsApiKey.trim() || !intervalsUserId.trim()}
                      style={{ 
                        padding: '0.5rem 1rem', 
                        background: (!intervalsApiKey.trim() || !intervalsUserId.trim()) ? '#ccc' : '#388e3c', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '6px', 
                        cursor: (!intervalsApiKey.trim() || !intervalsUserId.trim()) ? 'not-allowed' : 'pointer'
                      }}
                    >
                      Connect
                    </button>
                    <button
                      onClick={() => setShowIntervalsConnect(false)}
                      style={{ padding: '0.5rem 1rem', background: '#999', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Recent Activities */}
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ background: 'white', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#1976d2' }}>Recent Activities</h3>
          
          {/* Table Headers */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: '1rem', padding: '1rem', background: '#e3f2fd', borderRadius: '8px', marginBottom: '0.5rem', fontWeight: '600', color: '#1976d2' }}>
            <div>Activity</div>
            <div style={{ textAlign: 'center' }}>Distance</div>
            <div style={{ textAlign: 'center' }}>Duration</div>
            <div style={{ textAlign: 'center' }}>Avg Speed</div>
            <div style={{ textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              UTL Score
              <button
                onClick={() => setShowUtlModal(true)}
                style={{ 
                  background: '#1976d2', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '50%', 
                  width: '20px', 
                  height: '20px', 
                  fontSize: '12px', 
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title="Click to learn about UTL Score"
              >
                ?
              </button>
            </div>
          </div>

          {/* Activity Rows */}
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {recent_activities.map(activity => (
              <div key={activity.id || activity.activity_id} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>{activity.name}</div>
                  <div style={{ color: '#666', fontSize: '0.9rem' }}>{formatDate(activity.start_date)}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: '600' }}>{formatDistance(activity.distance)}</div>
                  <div style={{ color: '#666', fontSize: '0.8rem' }}>{activity.type}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: '600' }}>{formatDuration(activity.moving_time)}</div>
                  <div style={{ color: '#666', fontSize: '0.8rem' }}>Time</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: '600' }}>{activity.average_speed ? (activity.average_speed * 3.6).toFixed(1) + ' km/h' : 'N/A'}</div>
                  <div style={{ color: '#666', fontSize: '0.8rem' }}>Avg Speed</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontWeight: '600', color: activity.utl_score > 100 ? '#d32f2f' : activity.utl_score > 70 ? '#f57c00' : '#388e3c' }}>
                    {activity.utl_score ? activity.utl_score.toFixed(1) : 'N/A'}
                  </div>
                  <div style={{ color: '#666', fontSize: '0.8rem' }}>
                    {activity.calculation_method || 'Score'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* UTL Score Modal */}
      {showUtlModal && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          background: 'rgba(0,0,0,0.5)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          zIndex: 1000 
        }}>
          <div style={{ 
            background: 'white', 
            padding: '2rem', 
            borderRadius: '12px', 
            maxWidth: '600px', 
            maxHeight: '80vh', 
            overflow: 'auto',
            margin: '1rem',
            position: 'relative'
          }}>
            <button
              onClick={() => setShowUtlModal(false)}
              style={{ 
                position: 'absolute', 
                top: '1rem', 
                right: '1rem', 
                background: 'none', 
                border: 'none', 
                fontSize: '24px', 
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
            
            <h2 style={{ color: '#1976d2', marginBottom: '1rem' }}>Understanding UTL Score</h2>
            
            <div style={{ lineHeight: '1.6', color: '#333' }}>
              <p><strong>UTL (Unit Training Load)</strong> represents the physiological stress of your training session.</p>
              
              <h3 style={{ color: '#1976d2', marginTop: '1.5rem' }}>Calculation Methods:</h3>
              
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#333', marginBottom: '0.5rem' }}>🚴 TSS (Training Stress Score)</h4>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
                  For cycling activities with power data:<br/>
                  <code style={{ background: '#f5f5f5', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                    TSS = (duration × normalized_power² × intensity_factor) / (FTP² × 3600) × 100
                  </code>
                </p>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#333', marginBottom: '0.5rem' }}>🏃 rTSS (Running Training Stress Score)</h4>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
                  For running activities with pace data:<br/>
                  <code style={{ background: '#f5f5f5', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                    rTSS = (duration × intensity_factor²) / 3600 × 100
                  </code>
                </p>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#333', marginBottom: '0.5rem' }}>❤️ TRIMP (Heart Rate Training Impulse)</h4>
                <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>
                  For activities with heart rate data:<br/>
                  <code style={{ background: '#f5f5f5', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                    TRIMP = duration × ΔHR × 0.64^(e^(k×ΔHR))
                  </code>
                  <br/><small>Where ΔHR = (avg_hr - resting_hr) / (max_hr - resting_hr)</small>
                </p>
              </div>

              <h3 style={{ color: '#1976d2', marginTop: '1.5rem' }}>Score Interpretation:</h3>
              <div style={{ display: 'grid', gap: '0.5rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: '12px', height: '12px', background: '#388e3c', borderRadius: '50%' }}></div>
                  <span><strong>≤ 70:</strong> Easy/Recovery training</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: '12px', height: '12px', background: '#f57c00', borderRadius: '50%' }}></div>
                  <span><strong>71-100:</strong> Moderate training stress</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{ width: '12px', height: '12px', background: '#d32f2f', borderRadius: '50%' }}></div>
                  <span><strong>&gt; 100:</strong> High intensity/long duration</span>
                </div>
              </div>

              <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666', fontStyle: 'italic' }}>
                The calculation method used depends on available data: power (TSS), pace (rTSS), or heart rate (TRIMP).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
