import React from "react";
import OnboardingForm from "./OnboardingForm";
import Dashboard from "./Dashboard";

export default function App() {
  const [user, setUser] = React.useState(null);
  const [onboarded, setOnboarded] = React.useState(false);
  const [stravaLoading, setStravaLoading] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  // Check for existing authentication on app load
  React.useEffect(() => {
    const checkExistingAuth = async () => {
      try {
        // Check localStorage for saved user data
        const savedUser = localStorage.getItem('trainload_user');
        if (savedUser) {
          const userData = JSON.parse(savedUser);
          console.log('Found saved user:', userData);
          
          // Verify user still exists and get their current status
          const response = await fetch(`http://localhost:8000/dashboard/${userData.user_id}`);
          if (response.ok) {
            const dashboardData = await response.json();
            // If dashboard returns data, user has completed onboarding
            setUser(userData);
            setOnboarded(true);
            setLoading(false);
            return;
          } else {
            // User data is stale, clear it
            console.log('Stored user data is stale, clearing localStorage');
            localStorage.removeItem('trainload_user');
          }
        }
        
        // Check for user info in query params (OAuth callback)
        const params = new URLSearchParams(window.location.search);
        const userId = params.get("user_id");
        const name = params.get("name");
        const email = params.get("email");
        const gender = params.get("gender");
        
        if (userId) {
          const userData = { user_id: userId, name, email, gender };
          
          // Check if user has completed onboarding by trying to fetch dashboard
          try {
            const response = await fetch(`http://localhost:8000/dashboard/${userId}`);
            if (response.ok) {
              const dashboardData = await response.json();
              // User has dashboard data, they've completed onboarding
              setUser(userData);
              setOnboarded(true);
              localStorage.setItem('trainload_user', JSON.stringify(userData));
              
              // Clean up URL
              window.history.replaceState({}, document.title, window.location.pathname);
            } else {
              // User exists but needs onboarding
              setUser(userData);
              setOnboarded(false);
              
              // Clean up URL but don't save to localStorage yet
              window.history.replaceState({}, document.title, window.location.pathname);
            }
          } catch (error) {
            console.error('Error checking user onboarding status:', error);
            // Assume needs onboarding if we can't check
            setUser(userData);
            setOnboarded(false);
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        }
      } catch (error) {
        console.error('Error checking authentication:', error);
      } finally {
        setLoading(false);
      }
    };

    checkExistingAuth();
  }, []);

  // Simulate Strava OAuth flow
  const handleStravaLogin = async () => {
    setStravaLoading(true);
    // Redirect to backend Strava OAuth endpoint (use absolute URL)
    window.location.href = "http://localhost:8000/auth/strava/auth";
  };

  const handleOnboardingComplete = () => {
    setOnboarded(true);
    // Save user to localStorage after onboarding is complete
    if (user) {
      localStorage.setItem('trainload_user', JSON.stringify(user));
    }
  };

  const handleLogout = () => {
    setUser(null);
    setOnboarded(false);
    // Clear stored user data
    localStorage.removeItem('trainload_user');
    window.history.replaceState({}, document.title, window.location.pathname);
  };

  const handleClearCache = () => {
    localStorage.removeItem('trainload_user');
    window.location.reload();
  };

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div style={{ 
        fontFamily: "sans-serif", 
        background: "#f9f9f9", 
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ 
            width: 40, 
            height: 40, 
            border: "4px solid #e0e7ef", 
            borderTop: "4px solid #1976d2",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
            margin: "0 auto 16px"
          }}></div>
          <div style={{ color: "#666", fontSize: 16 }}>Loading TrainLoad...</div>
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

  return (
    <div style={{ fontFamily: "sans-serif", background: "#f9f9f9", minHeight: "100vh" }}>
      {!user ? (
        <div style={{ maxWidth: 420, margin: "4rem auto", padding: 32, background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px #e0e7ef", textAlign: "center" }}>
          <h2 style={{ color: "#1976d2", fontWeight: 700, marginBottom: 24 }}>Sign in to TrainLoad</h2>
          <button
            onClick={handleStravaLogin}
            style={{
              background: "#fc4c02",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "14px 0",
              width: "100%",
              fontWeight: 700,
              fontSize: 18,
              letterSpacing: 1,
              boxShadow: "0 2px 8px #e0e7ef",
              cursor: "pointer",
              marginBottom: 12
            }}
            disabled={stravaLoading}
          >
            {stravaLoading ? "Redirecting..." : "Sign in with Strava"}
          </button>
          <div style={{ color: "#888", fontSize: 14, marginTop: 16 }}>
            You must connect Strava to use TrainLoad.
          </div>
        </div>
      ) : !onboarded ? (
        <OnboardingForm 
          userId={user.user_id} 
          stravaData={user} 
          onComplete={handleOnboardingComplete} 
        />
      ) : (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}
