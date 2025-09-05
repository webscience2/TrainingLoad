import React, { useState } from "react";

export default function OnboardingForm({ userId, stravaData, onComplete }) {
  const [name, setName] = useState(stravaData?.name || "");
  const [dob, setDob] = useState("");
  const [email, setEmail] = useState(stravaData?.email || "");
  const [emailError, setEmailError] = useState("");
  const [gender, setGender] = useState(stravaData?.gender || "");
  const [weight, setWeight] = useState("");
  const [injuryHistory, setInjuryHistory] = useState(false);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [activityCount, setActivityCount] = useState(0);

  const containerStyle = { maxWidth: 420, margin: "4rem auto", padding: 32, background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px #e0e7ef", fontFamily: "Inter, sans-serif" };
  const headerStyle = { display: "flex", alignItems: "center", justifyContent: "center", gap: 16, marginBottom: 24 };
  const titleStyle = { fontSize: 32, fontWeight: 800, color: "#1976d2", letterSpacing: 2 };
  const formTitleStyle = { textAlign: "center", marginBottom: 28, color: "#1976d2", fontWeight: 700, letterSpacing: 1 };
  const labelStyle = { display: "block", marginBottom: 18, fontWeight: 500, color: "#333" };
  const inputStyle = { width: "100%", padding: "10px 12px", borderRadius: 6, border: "1px solid #cfd8dc", marginTop: 6, fontSize: 16, outline: "none" };
  const selectStyle = { ...inputStyle, background: "#fff" };
  const checkboxStyle = { marginRight: 10, accentColor: "#1976d2", width: 18, height: 18 };
  const buttonStyle = { width: "100%", padding: "12px 0", background: isLoading ? "#ccc" : "linear-gradient(90deg,#1976d2 60%,#42a5f5 100%)", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: 18, marginTop: 10, boxShadow: "0 2px 8px #e0e7ef", cursor: isLoading ? "not-allowed" : "pointer", letterSpacing: 1 };
  const messageStyle = { marginTop: 18, color: message.includes("error") ? "#d32f2f" : "#388e3c", textAlign: "center", fontWeight: 600, fontSize: 16, letterSpacing: 0.5 };
  const progressStyle = { marginTop: 12, color: "#1976d2", textAlign: "center", fontWeight: 500, fontSize: 14 };

  const pollActivityProgress = async () => {
    let attempts = 0;
    const maxAttempts = 60; // 60 * 2 seconds = 2 minutes max
    
    const checkProgress = async () => {
      try {
        const response = await fetch(`http://localhost:8000/activities/count/${userId}`);
        const data = await response.json();
        const count = data.activity_count || 0;
        
        setActivityCount(count);
        setProgress(`Imported ${count} activities...`);
        
        // If we have at least 10 activities or reached max attempts
        if (count >= 10 || attempts >= maxAttempts) {
          setIsLoading(false);
          if (count >= 10) {
            setMessage(`Great! We've imported ${count} activities and calculated your training thresholds.`);
            // Wait a moment then redirect to dashboard
            setTimeout(() => {
              if (onComplete) onComplete();
            }, 2000);
          } else {
            setMessage(`We've imported ${count} activities. You can continue to the dashboard, but more data will improve your training zones.`);
            setTimeout(() => {
              if (onComplete) onComplete();
            }, 3000);
          }
          return;
        }
        
        attempts++;
        // Continue polling
        setTimeout(checkProgress, 2000);
      } catch (err) {
        attempts++;
        if (attempts >= maxAttempts) {
          setIsLoading(false);
          setMessage("Activity import is taking longer than expected. You can continue to the dashboard.");
          setTimeout(() => {
            if (onComplete) onComplete();
          }, 2000);
        } else {
          setTimeout(checkProgress, 2000);
        }
      }
    };
    
    checkProgress();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) {
      setEmailError("Please enter a valid email address.");
      return;
    } else {
      setEmailError("");
    }
    
    setIsLoading(true);
    setProgress("Starting onboarding...");
    setMessage("");
    
    const payload = {
      user_id: userId,
      name,
      email,  // Include the user's real email
      dob,
      demographics: { gender, weight },
      injury_history: { injury: injuryHistory }
    };
    
    try {
      setProgress("Saving profile information...");
      const response = await fetch("http://localhost:8000/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (response.ok) {
        setProgress("Checking activity import status...");
        // Poll for activity count to show progress
        await pollActivityProgress();
      } else {
        setMessage(data.error || "An error occurred.");
        setIsLoading(false);
      }
    } catch (err) {
      setMessage("Network error.");
      setIsLoading(false);
    }
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="24" cy="24" r="24" fill="#1976d2" />
          <path d="M24 12L32 36H16L24 12Z" fill="#fff" />
        </svg>
        <span style={titleStyle}>TrainLoad</span>
      </div>
      <form onSubmit={handleSubmit}>
        <h2 style={formTitleStyle}>Onboarding Questionnaire</h2>
        <label style={labelStyle}>
          Name<br />
          <input type="text" name="name" value={name} onChange={e => setName(e.target.value)} style={inputStyle} required disabled={Boolean(stravaData && stravaData.name) || isLoading} />
        </label>
        <label style={labelStyle}>
          Email<br />
          <input type="email" name="email" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} required disabled={Boolean(stravaData && stravaData.email) || isLoading} />
        </label>
        {emailError && (<div style={{ color: "#d32f2f", marginBottom: 12, textAlign: "center", fontWeight: 500 }}>{emailError}</div>)}
        <label style={labelStyle}>
          Date of Birth<br />
          <input type="date" name="dob" value={dob} onChange={e => setDob(e.target.value)} style={inputStyle} required disabled={isLoading} />
        </label>
        <label style={labelStyle}>
          Gender<br />
          <select name="gender" value={gender} onChange={e => setGender(e.target.value)} style={selectStyle} disabled={isLoading}>
            <option value="">Select</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label style={labelStyle}>
          Weight (kg)<br />
          <input name="weight" type="text" value={weight} onChange={e => setWeight(e.target.value)} style={inputStyle} disabled={isLoading} />
        </label>
        <label style={{ display: "flex", alignItems: "center", marginBottom: 18, fontWeight: 500, color: "#333" }}>
          <input type="checkbox" name="injury" checked={injuryHistory} onChange={e => setInjuryHistory(e.target.checked)} style={checkboxStyle} disabled={isLoading} />
          History of injury
        </label>
        <button type="submit" style={buttonStyle} disabled={isLoading}>
          {isLoading ? "Processing..." : "Submit"}
        </button>
        {progress && (<div style={progressStyle}>{progress}</div>)}
        {message && (<div style={messageStyle}>{message}</div>)}
        {isLoading && (
          <div style={{ marginTop: 16, textAlign: "center", color: "#666", fontSize: 14 }}>
            This may take a few minutes while we import your activities and calculate your training thresholds...
          </div>
        )}
      </form>
    </div>
  );
}
