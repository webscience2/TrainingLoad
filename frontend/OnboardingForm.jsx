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

  const containerStyle = { maxWidth: 420, margin: "4rem auto", padding: 32, background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px #e0e7ef", fontFamily: "Inter, sans-serif" };
  const headerStyle = { display: "flex", alignItems: "center", justifyContent: "center", gap: 16, marginBottom: 24 };
  const titleStyle = { fontSize: 32, fontWeight: 800, color: "#1976d2", letterSpacing: 2 };
  const formTitleStyle = { textAlign: "center", marginBottom: 28, color: "#1976d2", fontWeight: 700, letterSpacing: 1 };
  const labelStyle = { display: "block", marginBottom: 18, fontWeight: 500, color: "#333" };
  const inputStyle = { width: "100%", padding: "10px 12px", borderRadius: 6, border: "1px solid #cfd8dc", marginTop: 6, fontSize: 16, outline: "none" };
  const selectStyle = { ...inputStyle, background: "#fff" };
  const checkboxStyle = { marginRight: 10, accentColor: "#1976d2", width: 18, height: 18 };
  const buttonStyle = { width: "100%", padding: "12px 0", background: "linear-gradient(90deg,#1976d2 60%,#42a5f5 100%)", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: 18, marginTop: 10, boxShadow: "0 2px 8px #e0e7ef", cursor: "pointer", letterSpacing: 1 };
  const messageStyle = { marginTop: 18, color: message.includes("error") ? "#d32f2f" : "#388e3c", textAlign: "center", fontWeight: 600, fontSize: 16, letterSpacing: 0.5 };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.match(/^[^@\s]+@[^@\s]+\.[^@\s]+$/)) {
      setEmailError("Please enter a valid email address.");
      return;
    } else {
      setEmailError("");
    }
    const payload = {
      user_id: userId,
      name,
      dob,
      demographics: { gender, weight },
      injury_history: { injury: injuryHistory }
    };
    try {
      const response = await fetch("http://localhost:8000/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage("Onboarding complete!");
        if (onComplete) onComplete();
      } else {
        setMessage(data.error || "An error occurred.");
      }
    } catch (err) {
      setMessage("Network error.");
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
          <input type="text" name="name" value={name} onChange={e => setName(e.target.value)} style={inputStyle} required disabled={Boolean(stravaData && stravaData.name)} />
        </label>
        <label style={labelStyle}>
          Email<br />
          <input type="email" name="email" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} required disabled={Boolean(stravaData && stravaData.email)} />
        </label>
        {emailError && (<div style={{ color: "#d32f2f", marginBottom: 12, textAlign: "center", fontWeight: 500 }}>{emailError}</div>)}
        <label style={labelStyle}>
          Date of Birth<br />
          <input type="date" name="dob" value={dob} onChange={e => setDob(e.target.value)} style={inputStyle} required />
        </label>
        <label style={labelStyle}>
          Gender<br />
          <select name="gender" value={gender} onChange={e => setGender(e.target.value)} style={selectStyle}>
            <option value="">Select</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label style={labelStyle}>
          Weight (kg)<br />
          <input name="weight" type="text" value={weight} onChange={e => setWeight(e.target.value)} style={inputStyle} />
        </label>
        <label style={{ display: "flex", alignItems: "center", marginBottom: 18, fontWeight: 500, color: "#333" }}>
          <input type="checkbox" name="injury" checked={injuryHistory} onChange={e => setInjuryHistory(e.target.checked)} style={checkboxStyle} />
          History of injury
        </label>
        <button type="submit" style={buttonStyle}>Submit</button>
        {message && (<div style={messageStyle}>{message}</div>)}
      </form>
    </div>
  );
}

