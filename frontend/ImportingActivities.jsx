import React from "react";

export default function ImportingActivities({ user }) {
  // Simulate progress for demo
  const [progress, setProgress] = React.useState(0);
  React.useEffect(() => {
    const timer = setInterval(() => {
      setProgress((p) => (p < 100 ? p + 10 : 100));
    }, 400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{ maxWidth: 420, margin: "4rem auto", padding: 32, background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px #e0e7ef", textAlign: "center", fontFamily: "Inter, sans-serif" }}>
      <h2 style={{ color: "#1976d2", fontWeight: 700, marginBottom: 24 }}>Importing Activities</h2>
      <div style={{ marginBottom: 18, fontSize: 18, color: "#333" }}>
        We're importing your Strava activities. This may take a moment.
      </div>
      <div style={{ width: "100%", background: "#e0e7ef", borderRadius: 8, height: 18, marginBottom: 18 }}>
        <div style={{ width: `${progress}%`, background: "linear-gradient(90deg,#1976d2 60%,#42a5f5 100%)", height: "100%", borderRadius: 8, transition: "width 0.4s" }} />
      </div>
      <div style={{ fontWeight: 600, color: progress < 100 ? "#1976d2" : "#388e3c", fontSize: 16 }}>
        {progress < 100 ? `Importing... (${progress}%)` : "Import complete!"}
      </div>
    </div>
  );
}
