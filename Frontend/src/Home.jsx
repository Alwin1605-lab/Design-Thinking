import React, { useState, useEffect } from "react";

export default function Home() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/analytics");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>🌾 Welcome to GramaFix</h1>
        <p className="hero-subtitle">Smart Rural Issue Reporting System</p>
        <p>Report local issues and track their resolution in real-time</p>
        <div className="hero-buttons">
          <a href="/report" className="btn btn-primary">📢 Report an Issue</a>
          <a href="/issues" className="btn btn-secondary">📋 View All Issues</a>
        </div>
      </div>

      {loading ? (
        <p>Loading statistics...</p>
      ) : stats ? (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-number">{stats.total_issues}</div>
              <div className="stat-label">Total Issues</div>
            </div>
            <div className="stat-card pending">
              <div className="stat-icon">⏳</div>
              <div className="stat-number">{stats.status_breakdown.received}</div>
              <div className="stat-label">Pending</div>
            </div>
            <div className="stat-card progress">
              <div className="stat-icon">🔧</div>
              <div className="stat-number">{stats.status_breakdown.in_progress}</div>
              <div className="stat-label">In Progress</div>
            </div>
            <div className="stat-card resolved">
              <div className="stat-icon">✅</div>
              <div className="stat-number">{stats.status_breakdown.resolved}</div>
              <div className="stat-label">Resolved</div>
            </div>
          </div>

          <div className="categories-section">
            <h2>📑 Issues by Category</h2>
            <div className="categories-grid">
              {stats.category_breakdown.map((cat) => (
                <div key={cat.category} className="category-card">
                  <div className="category-icon">{cat.icon}</div>
                  <div className="category-name">{cat.category}</div>
                  <div className="category-count">{cat.count} issues</div>
                </div>
              ))}
            </div>
          </div>

          {stats.top_priority_issues.length > 0 && (
            <div className="priority-section">
              <h2>🔥 Top Priority Issues</h2>
              <div className="priority-list">
                {stats.top_priority_issues.map((issue) => (
                  <div key={issue.id} className="priority-item">
                    <span className="priority-category">{issue.category}</span>
                    <span className="priority-description">{issue.description}</span>
                    <span className="priority-votes">👍 {issue.votes} votes</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="resolution-rate">
            <h3>Resolution Rate: {stats.resolution_rate}%</h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${stats.resolution_rate}%` }}
              ></div>
            </div>
          </div>
        </>
      ) : (
        <p>Unable to load statistics</p>
      )}

      <div className="features-section">
        <h2>✨ Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎤</div>
            <h3>Voice Reporting</h3>
            <p>Report issues using voice in your local language</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📍</div>
            <h3>GPS Location</h3>
            <p>Automatic location tagging for precise reporting</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📸</div>
            <h3>Photo Upload</h3>
            <p>Add photos to support your complaint</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📱</div>
            <h3>SMS Updates</h3>
            <p>Get status updates via SMS</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">👥</div>
            <h3>Community Voting</h3>
            <p>Vote to prioritize important issues</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Track Progress</h3>
            <p>Monitor resolution status in real-time</p>
          </div>
        </div>
      </div>
    </div>
  );
}
