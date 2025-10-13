import React, { useState, useEffect } from "react";

export default function AdminDashboard() {
  const [issues, setIssues] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [statusForm, setStatusForm] = useState({
    status: "",
    remarks: "",
    updated_by: "",
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [issuesRes, statsRes] = await Promise.all([
        fetch("http://localhost:8000/api/issues?limit=50"),
        fetch("http://localhost:8000/api/analytics"),
      ]);

      const issuesData = await issuesRes.json();
      const statsData = await statsRes.json();

      setIssues(issuesData.issues);
      setStats(statsData);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (e) => {
    e.preventDefault();

    if (!selectedIssue) return;

    const formData = new FormData();
    formData.append("status", statusForm.status);
    formData.append("remarks", statusForm.remarks);
    formData.append("updated_by", statusForm.updated_by);

    try {
      const response = await fetch(
        `http://localhost:8000/api/issues/${selectedIssue._id}/status`,
        {
          method: "PUT",
          body: formData,
        }
      );

      if (response.ok) {
        alert("Status updated successfully!");
        setSelectedIssue(null);
        setStatusForm({ status: "", remarks: "", updated_by: "" });
        fetchDashboardData();
      } else {
        alert("Failed to update status");
      }
    } catch (error) {
      console.error("Error updating status:", error);
      alert("Error updating status");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Received":
        return "#ff9800";
      case "In Progress":
        return "#2196f3";
      case "Resolved":
        return "#4caf50";
      default:
        return "#999";
    }
  };

  if (loading) {
    return <div className="admin-dashboard"><p>Loading dashboard...</p></div>;
  }

  return (
    <div className="admin-dashboard">
      <h2>⚙️ Admin Dashboard - Gram Panchayat</h2>

      {stats && (
        <div className="dashboard-stats">
          <div className="stat-card">
            <h3>Total Issues</h3>
            <div className="stat-number">{stats.total_issues}</div>
          </div>
          <div className="stat-card">
            <h3>Pending</h3>
            <div className="stat-number" style={{ color: "#ff9800" }}>
              {stats.status_breakdown.received}
            </div>
          </div>
          <div className="stat-card">
            <h3>In Progress</h3>
            <div className="stat-number" style={{ color: "#2196f3" }}>
              {stats.status_breakdown.in_progress}
            </div>
          </div>
          <div className="stat-card">
            <h3>Resolved</h3>
            <div className="stat-number" style={{ color: "#4caf50" }}>
              {stats.status_breakdown.resolved}
            </div>
          </div>
          <div className="stat-card">
            <h3>Resolution Rate</h3>
            <div className="stat-number">{stats.resolution_rate}%</div>
          </div>
        </div>
      )}

      <div className="dashboard-content">
        <div className="issues-panel">
          <h3>Recent Issues</h3>
          <div className="issues-table">
            <table>
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Location</th>
                  <th>Reporter</th>
                  <th>Status</th>
                  <th>Votes</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue) => (
                  <tr key={issue._id}>
                    <td>{issue.category}</td>
                    <td className="description-cell">
                      {issue.description.substring(0, 50)}...
                    </td>
                    <td>{issue.gram_panchayat}</td>
                    <td>
                      {issue.reporter_name}
                      <br />
                      <small>{issue.reporter_phone}</small>
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(issue.status) }}
                      >
                        {issue.status}
                      </span>
                    </td>
                    <td>👍 {issue.priority_votes}</td>
                    <td>
                      <button
                        onClick={() => setSelectedIssue(issue)}
                        className="action-btn"
                      >
                        Update Status
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {stats && stats.category_breakdown && (
          <div className="category-stats">
            <h3>Issues by Category</h3>
            <div className="category-chart">
              {stats.category_breakdown.map((cat) => (
                <div key={cat.category} className="category-bar">
                  <div className="category-label">
                    {cat.icon} {cat.category}
                  </div>
                  <div className="bar-container">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(cat.count / stats.total_issues) * 100}%`,
                      }}
                    ></div>
                  </div>
                  <div className="category-count">{cat.count}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selectedIssue && (
        <div className="modal-overlay" onClick={() => setSelectedIssue(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Update Issue Status</h3>
            <div className="issue-details">
              <p>
                <strong>Category:</strong> {selectedIssue.category}
              </p>
              <p>
                <strong>Description:</strong> {selectedIssue.description}
              </p>
              <p>
                <strong>Reporter:</strong> {selectedIssue.reporter_name} (
                {selectedIssue.reporter_phone})
              </p>
              <p>
                <strong>Current Status:</strong> {selectedIssue.status}
              </p>
            </div>

            <form onSubmit={handleStatusUpdate} className="status-form">
              <div className="form-group">
                <label>New Status *</label>
                <select
                  value={statusForm.status}
                  onChange={(e) =>
                    setStatusForm({ ...statusForm, status: e.target.value })
                  }
                  required
                >
                  <option value="">Select Status</option>
                  <option value="Received">Received</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div className="form-group">
                <label>Remarks</label>
                <textarea
                  value={statusForm.remarks}
                  onChange={(e) =>
                    setStatusForm({ ...statusForm, remarks: e.target.value })
                  }
                  placeholder="Add any notes or updates..."
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Updated By *</label>
                <input
                  type="text"
                  value={statusForm.updated_by}
                  onChange={(e) =>
                    setStatusForm({ ...statusForm, updated_by: e.target.value })
                  }
                  placeholder="Officer name"
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn btn-primary">
                  Update Status
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedIssue(null)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
