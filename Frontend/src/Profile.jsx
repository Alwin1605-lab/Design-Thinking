import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const loggedIn = localStorage.getItem("loggedIn");
    (async () => {
      try {
        if (!loggedIn || !storedUser) {
          navigate("/login");
          return;
        }
        const parsed = JSON.parse(storedUser);
        if (!parsed || !(parsed._id || parsed.id)) {
          throw new Error("Invalid user");
        }
        // Fetch latest profile from backend to get TOTP status
        try {
          const res = await fetch(`http://localhost:8000/api/auth/profile?user_id=${parsed._id || parsed.id}`);
          if (res.ok) {
            const fresh = await res.json();
            setUser(fresh);
          } else {
            setUser(parsed);
          }
        } catch {
          setUser(parsed);
        }
        setLoading(false);
      } catch {
        // Clear bad state and redirect
        localStorage.removeItem("user");
        localStorage.removeItem("token");
        localStorage.removeItem("loggedIn");
        navigate("/login");
      }
    })();
  }, [navigate]);

  const handleLogout = async () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("loggedIn");
    navigate("/login");
  };

  const [totp, setTotp] = useState({ enabled: false });
  const [qr, setQr] = useState(null);
  const [totpCode, setTotpCode] = useState("");
  useEffect(() => {
    if (user && user.totp) setTotp(user.totp);
  }, [user]);

  const startTotp = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/auth/totp/setup/start", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Failed to start setup");
      setQr(data.qr_data_url);
    } catch (e) {
      alert(e.message || "Failed to start TOTP setup");
    }
  };

  const verifyTotp = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/auth/totp/setup/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ code: totpCode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Invalid code");
      setTotp({ ...(user?.totp || {}), enabled: true });
      setQr(null);
      setTotpCode("");
      alert("Authenticator enabled!");
    } catch (e) {
      alert(e.message || "Failed to verify code");
    }
  };

  if (loading) {
    return <div className="profile-container"><p>Loading...</p></div>;
  }

  if (!user) {
    return null;
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-icon">
            {user.role === "admin" && "⚙️"}
            {user.role === "officer" && "👮"}
            {user.role === "citizen" && "👤"}
          </div>
          <h2>{user.name}</h2>
          <span className={`role-badge ${user.role}`}>
            {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
          </span>
        </div>

        <div className="profile-details">
          <div className="detail-item">
            <span className="detail-label">📧 Email:</span>
            <span className="detail-value">{user.email}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">📱 Phone:</span>
            <span className="detail-value">{user.phone}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">🏘️ Gram Panchayat:</span>
            <span className="detail-value">{user.gram_panchayat}</span>
          </div>
          {user.address && (
            <div className="detail-item">
              <span className="detail-label">📍 Address:</span>
              <span className="detail-value">{user.address}</span>
            </div>
          )}
          {user.id_proof_type && (
            <div className="detail-item">
              <span className="detail-label">🆔 ID Proof:</span>
              <span className="detail-value">{user.id_proof_type} - {user.id_proof_number}</span>
            </div>
          )}
          {user.created_at && (
            <div className="detail-item">
              <span className="detail-label">📅 Member Since:</span>
              <span className="detail-value">{new Date(user.created_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>

        <div className="profile-actions">
          <button onClick={() => navigate("/")} className="btn-secondary">
            🏠 Go to Home
          </button>
          {(user.role === "admin" || user.role === "officer") && (
            <button onClick={() => navigate("/admin")} className="btn-primary">
              📊 Admin Dashboard
            </button>
          )}
          <button onClick={() => navigate("/report")} className="btn-primary">
            📝 Report Issue
          </button>
          <button onClick={handleLogout} className="btn-logout">
            🚪 Logout
          </button>
        </div>

        <div className="profile-card" style={{ marginTop: 16 }}>
          <h3>🔒 Authenticator (TOTP)</h3>
          {totp?.enabled ? (
            <p>Authenticator is enabled for your account.</p>
          ) : (
            <div>
              {!qr ? (
                <>
                  <p>Enable an Authenticator app (Google Authenticator, Authy) for passwordless login.</p>
                  <button onClick={startTotp} className="btn-primary">Enable Authenticator</button>
                </>
              ) : (
                <div>
                  <p>Scan this QR code with your Authenticator app, then enter the 6-digit code to verify.</p>
                  <img src={qr} alt="Authenticator QR" style={{ maxWidth: 240, border: '1px solid #ddd' }} />
                  <div className="form-group" style={{ marginTop: 12 }}>
                    <label>Verification Code</label>
                    <input value={totpCode} onChange={(e) => setTotpCode(e.target.value)} placeholder="123456" />
                  </div>
                  <button onClick={verifyTotp} className="btn-primary">Verify & Enable</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}