import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const loggedIn = localStorage.getItem("loggedIn");
    
    if (!loggedIn || !storedUser) {
      navigate("/login");
      return;
    }
    
    const userData = JSON.parse(storedUser);
    setUser(userData);
    setLoading(false);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("loggedIn");
    navigate("/login");
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
          <div className="detail-item">
            <span className="detail-label">📅 Member Since:</span>
            <span className="detail-value">{new Date(user.created_at).toLocaleDateString()}</span>
          </div>
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
      </div>
    </div>
  );
}