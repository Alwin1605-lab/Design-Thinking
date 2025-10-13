import React from "react";
import { Link } from "react-router-dom";

function Header() {
  const isLoggedIn = localStorage.getItem("loggedIn") === "true";
  const user = isLoggedIn ? JSON.parse(localStorage.getItem("user") || "{}") : null;

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

      <div className="header-profile">
        {isLoggedIn ? (
          <Link to="/profile" className="profile-icon">
            <div className="profile-avatar">
              {user?.name ? user.name.charAt(0).toUpperCase() : '👤'}
            </div>
            <span className="profile-name">{user?.name || 'Profile'}</span>
          </Link>
        ) : (
          <Link to="/login" className="login-btn">
            🔐 Login
          </Link>
        )}
      </div>
    </header>
  );
}

export default Header;
