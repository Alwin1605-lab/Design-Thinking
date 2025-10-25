import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [mode, setMode] = useState("password"); // 'password' | 'totp'
  const [identifier, setIdentifier] = useState(""); // email or phone
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (response.ok) {
        // Store user data and authentication token
        localStorage.setItem("user", JSON.stringify(data.user));
        localStorage.setItem("token", data.token);
        localStorage.setItem("loggedIn", "true");
        
        // Redirect based on role
        if (data.user.role === "admin" || data.user.role === "officer") {
          navigate("/admin");
        } else {
          navigate("/profile");
        }
      } else {
        setError(data.detail || "Invalid credentials");
      }
    } catch (error) {
      console.error("Error logging in:", error);
      setError("Error connecting to server");
    } finally {
      setLoading(false);
    }
  };

  const loginWithTotp = async () => {
    setError("");
    if (!identifier || !code) {
      setError("Enter your email/phone and the 6-digit code from your Authenticator app.");
      return;
    }
    try {
      setLoading(true);
      const res = await fetch("http://localhost:8000/api/auth/totp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: identifier, phone: identifier, code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Verification failed");
      localStorage.setItem("user", JSON.stringify(data.user));
      localStorage.setItem("token", data.token);
      localStorage.setItem("loggedIn", "true");
      if (data.user.role === "admin" || data.user.role === "officer") {
        navigate("/admin");
      } else {
        navigate("/profile");
      }
    } catch (err) {
      console.error(err);
      setError(err?.message || "Invalid code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>🔐 Welcome Back</h2>
        <p className="auth-subtitle">Login to GramaFix</p>

        {error && <div className="error-banner">{error}</div>}

        <div className="auth-tabs" style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          <button
            className={`auth-tab ${mode === "password" ? "active" : ""}`}
            onClick={() => setMode("password")}
          >
            Password Login
          </button>
          <button
            className={`auth-tab ${mode === "totp" ? "active" : ""}`}
            onClick={() => setMode("totp")}
          >
            Authenticator (TOTP)
          </button>
        </div>

        {mode === "password" ? (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="your.email@example.com"
                required
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                type="password"
                id="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? "Logging in..." : "🔐 Login"}
            </button>
          </form>
        ) : (
          <div className="auth-form">
            <div className="form-group">
              <label>Email or Phone *</label>
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="your.email@example.com or +919876543210"
                required
              />
            </div>
            <div className="form-group">
              <label>Authenticator Code *</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="6-digit code"
                required
              />
            </div>
            <button onClick={loginWithTotp} className="auth-btn" disabled={loading}>
              {loading ? "Verifying..." : "Verify & Login"}
            </button>
            <small style={{opacity:0.8}}>
              Tip: Enable Authenticator in your Profile to use TOTP login.
            </small>
          </div>
        )}

        <p className="auth-link">
          Don't have an account? <a href="/register">Register here</a>
        </p>
      </div>
    </div>
  );
}