import React from "react";
import { Link } from "react-router-dom";

function Header() {
  // Be defensive: only treat as logged in if a parseable user exists
  let user = null;
  let isLoggedIn = false;
  try {
    const flag = localStorage.getItem("loggedIn") === "true";
    const raw = localStorage.getItem("user");
    if (flag && raw) {
      const parsed = JSON.parse(raw);
      if (parsed && (parsed._id || parsed.id)) {
        user = parsed;
        isLoggedIn = true;
      }
    }
  } catch (e) {
    isLoggedIn = false;
    user = null;
  }

  return (
    <header className="app-header">
      <div className="header-left">
        <span className="header-emoji">🌾</span>
        <div>
          <Link to="/" style={{textDecoration: 'none', color: 'inherit'}}>
            <h1 className="header-title">GramaFix</h1>
          </Link>
          <p className="header-subtitle">Smart Rural Issue Reporting</p>
        </div>
      </div>
      
      <nav className="header-nav">
        <Link to="/" className="header-nav-link">
          🏠 Home
        </Link>
        <Link to="/report" className="header-nav-link">
          📝 Report Issue
        </Link>
        <Link to="/issues" className="header-nav-link">
          📋 View Issues
        </Link>
        {user && (user.role === "admin" || user.role === "officer") && (
          <Link to="/admin" className="header-nav-link">
            📊 Dashboard
          </Link>
        )}
      </nav>

      <div className="header-profile" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>

        {isLoggedIn ? (
          <Link to="/profile" className="profile-icon">
            <div className="profile-avatar">
              {user?.name ? user.name.charAt(0).toUpperCase() : '👤'}
            </div>
            <span className="profile-name">{user?.name || 'Profile'}</span>
          </Link>
        ) : (
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link to="/login" className="login-btn">
              🔐 Login
            </Link>
            <Link to="/register" className="login-btn" style={{ background: '#4caf50' }}>
              📝 Register
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
