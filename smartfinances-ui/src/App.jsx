import { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a CSV file first");
      return;
    }
    setError("");
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/upload-statement/", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else setSummary(data);
    } catch {
      setError("Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #0f172a, #1e293b)",
        color: "#f8fafc",
        fontFamily: "Inter, system-ui, sans-serif",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          background: "rgba(255,255,255,0.05)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: "20px",
          padding: "40px",
          width: "100%",
          maxWidth: "650px",
          boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
        }}
      >
        <h1
          style={{
            fontSize: "2rem",
            marginBottom: "0.5rem",
            fontWeight: 700,
            background: "linear-gradient(90deg,#38bdf8,#818cf8)",
            WebkitBackgroundClip: "text",
            color: "transparent",
          }}
        >
          SmartFinances
        </h1>
        <h2 style={{ fontWeight: 400, marginBottom: "2rem", color: "#94a3b8" }}>
          Statement Parser
        </h2>

        <p style={{ marginBottom: "1rem", color: "#cbd5e1" }}>
          Upload a <b>3-month bank statement</b>
        </p>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            marginBottom: "1rem",
          }}
        >
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
            style={{
              background: "rgba(255,255,255,0.1)",
              padding: "8px",
              borderRadius: "6px",
              color: "#e2e8f0",
            }}
          />
          <button
            onClick={handleUpload}
            disabled={loading}
            style={{
              padding: "8px 20px",
              borderRadius: "8px",
              border: "none",
              background:
                "linear-gradient(90deg, rgba(56,189,248,1) 0%, rgba(129,140,248,1) 100%)",
              color: "white",
              fontWeight: 600,
              cursor: "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {error && (
          <p style={{ color: "#f87171", marginTop: "0.5rem" }}>{error}</p>
        )}

        {summary && !error && (
          <div
            style={{
              marginTop: "2rem",
              background: "rgba(255,255,255,0.08)",
              padding: "20px",
              borderRadius: "12px",
              border: "1px solid rgba(255,255,255,0.15)",
              lineHeight: 1.8,
            }}
          >
            <h3 style={{ fontSize: "1.25rem", marginBottom: "1rem" }}>
              Summary
            </h3>
            <p>
              <b>Bank Detected:</b> {summary.bank}
            </p>
            <p>
              <b>Total Income:</b> ${summary.total_income.toLocaleString()}
            </p>
            <p>
              <b>Total Expense:</b> ${summary.total_expense.toLocaleString()}
            </p>
            <p>
              <b>Avg Monthly Income:</b> $
              {summary.avg_monthly_income.toFixed(2)}
            </p>
            <p>
              <b>Avg Monthly Expense:</b> $
              {summary.avg_monthly_expense.toFixed(2)}
            </p>
            <p>
              <b>Risk Flag:</b>{" "}
              <span
                style={{
                  color:
                    summary.flag === "Stable"
                      ? "#4ade80"
                      : summary.flag === "High Risk"
                      ? "#f87171"
                      : "#fbbf24",
                  fontWeight: 600,
                }}
              >
                {summary.flag}
              </span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
