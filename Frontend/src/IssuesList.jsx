import React, { useState, useEffect } from "react";

export default function IssuesList() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    category: "",
    status: "",
    gram_panchayat: "",
  });

  useEffect(() => {
    fetchIssues();
  }, [filter]);

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.category) params.append("category", filter.category);
      if (filter.status) params.append("status", filter.status);
      if (filter.gram_panchayat) params.append("gram_panchayat", filter.gram_panchayat);

      const response = await fetch(`http://localhost:8000/api/issues?${params}`);
      const data = await response.json();
      setIssues(data.issues);
    } catch (error) {
      console.error("Error fetching issues:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (issueId, voterPhone) => {
    if (!voterPhone) {
      voterPhone = prompt("Enter your phone number to vote:");
      if (!voterPhone) return;
    }

    try {
      const formData = new FormData();
      formData.append("voter_phone", voterPhone);

      const response = await fetch(`http://localhost:8000/api/issues/${issueId}/vote`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("Vote recorded successfully!");
        fetchIssues(); // Refresh the list
      } else {
        const data = await response.json();
        alert(data.detail || "Failed to vote");
      }
    } catch (error) {
      console.error("Error voting:", error);
      alert("Error recording vote");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Received":
        return "status-received";
      case "In Progress":
        return "status-progress";
      case "Resolved":
        return "status-resolved";
      default:
        return "";
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      Roads: "🛣",
      Water: "💧",
      Electricity: "💡",
      School: "🏫",
      Farming: "🚜",
      Sanitation: "🗑",
    };
    return icons[category] || "📋";
  };

  return (
    <div className="issues-list-container">
      <h2>📋 All Reported Issues</h2>

      <div className="filters">
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="Received">Received</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
        </select>

        <select
          value={filter.category}
          onChange={(e) => setFilter({ ...filter, category: e.target.value })}
          className="filter-select"
        >
          <option value="">All Categories</option>
          <option value="Roads">🛣 Roads</option>
          <option value="Water">💧 Water</option>
          <option value="Electricity">💡 Electricity</option>
          <option value="School">🏫 School</option>
          <option value="Farming">🚜 Farming</option>
          <option value="Sanitation">🗑 Sanitation</option>
        </select>

        <input
          type="text"
          placeholder="Filter by Gram Panchayat"
          value={filter.gram_panchayat}
          onChange={(e) => setFilter({ ...filter, gram_panchayat: e.target.value })}
          className="filter-input"
        />

        <button onClick={fetchIssues} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {loading ? (
        <p>Loading issues...</p>
      ) : (
        <>
          <p className="issues-count">Showing {issues.length} issue(s)</p>
          <div className="issues-grid">
            {issues.map((issue) => (
              <div key={issue._id} className="issue-card">
                <div className="issue-header">
                  <span className="issue-category">
                    {getCategoryIcon(issue.category)} {issue.category}
                  </span>
                  <span className={`issue-status ${getStatusColor(issue.status)}`}>
                    {issue.status}
                  </span>
                </div>

                <div className="issue-body">
                  <p className="issue-description">{issue.description}</p>
                  
                  <div className="issue-location">
                    <strong>📍 Location:</strong> {issue.location.address}
                    <br />
                    <small>
                      {issue.location.latitude.toFixed(4)}, {issue.location.longitude.toFixed(4)}
                    </small>
                  </div>

                  {issue.images && issue.images.length > 0 && (
                    <div className="issue-images">
                      {issue.images.map((img, idx) => (
                        <img
                          key={idx}
                          src={`http://localhost:8000/${img}`}
                          alt="Issue"
                          className="issue-image"
                        />
                      ))}
                    </div>
                  )}

                  <div className="issue-meta">
                    <p>
                      <strong>Reported by:</strong> {issue.reporter_name}
                    </p>
                    <p>
                      <strong>Gram Panchayat:</strong> {issue.gram_panchayat}
                    </p>
                    <p>
                      <strong>Reported on:</strong>{" "}
                      {new Date(issue.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="issue-voting">
                    <button
                      onClick={() => handleVote(issue._id)}
                      className="vote-btn"
                    >
                      👍 Vote ({issue.priority_votes})
                    </button>
                    <span className="vote-info">
                      {issue.priority_votes} people prioritized this issue
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
