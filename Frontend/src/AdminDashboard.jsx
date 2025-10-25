import React, { useState, useEffect } from "react";
import MapView from "./MapView";

export default function AdminDashboard() {
  const [issues, setIssues] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [gpFilter, setGpFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [statusForm, setStatusForm] = useState({
    status: "",
    remarks: "",
    updated_by: "",
    assigned_department: "",
  });
  const [progressFiles, setProgressFiles] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      q.set("limit", "50");
      if (gpFilter) q.set("gram_panchayat", gpFilter);
      if (startDate) q.set("start_date", startDate);
      if (endDate) q.set("end_date", endDate);
      const qp = `?${q.toString()}`;
      const [issuesRes, statsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/issues${qp}`),
        fetch(`http://localhost:8000/api/analytics${gpFilter || startDate || endDate ? `?${new URLSearchParams({ ...(gpFilter?{gram_panchayat:gpFilter}:{}) , ...(startDate?{start_date:startDate}:{}) , ...(endDate?{end_date:endDate}:{}) }).toString()}` : ""}`),
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

  const exportCsv = async () => {
    const params = new URLSearchParams();
    if (gpFilter) params.set("gram_panchayat", gpFilter);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`http://localhost:8000/api/admin/export/issues.csv?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "issues.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed", e);
      alert("Failed to export CSV (are you logged in as admin/officer?)");
    }
  };

  const handleStatusUpdate = async (e) => {
    e.preventDefault();

    if (!selectedIssue) return;

    const formData = new FormData();
    formData.append("status", statusForm.status);
    formData.append("remarks", statusForm.remarks);
    formData.append("updated_by", statusForm.updated_by);
    if (statusForm.assigned_department) {
      formData.append("assigned_department", statusForm.assigned_department);
    }
    if (progressFiles && progressFiles.length) {
      for (const f of progressFiles) {
        formData.append("progress_images", f);
      }
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/api/issues/${selectedIssue._id}/status`,
        {
          method: "PUT",
          body: formData,
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        alert("Status updated successfully!");
        setSelectedIssue(null);
        setStatusForm({ status: "", remarks: "", updated_by: "", assigned_department: "" });
        setProgressFiles([]);
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

      <div className="toolbar" style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <input
          type="text"
          value={gpFilter}
          onChange={(e) => setGpFilter(e.target.value)}
          placeholder="Filter by Gram Panchayat (optional)"
          style={{ padding: 8, minWidth: 280 }}
        />
        <input type="date" value={startDate} onChange={(e)=>setStartDate(e.target.value)} />
        <input type="date" value={endDate} onChange={(e)=>setEndDate(e.target.value)} />
        <button onClick={fetchDashboardData} className="btn btn-secondary">Apply Filter</button>
        <button onClick={exportCsv} className="btn btn-primary">⬇️ Export CSV</button>
      </div>

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
            <div className="progress-bar" style={{ marginTop: 6 }}>
              <div className="progress-fill" style={{ width: `${stats.resolution_rate}%` }} />
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-content">
        <div className="map-panel">
          <h3>Issues Map</h3>
          <MapView issues={issues} />
        </div>
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
            {stats.trend && stats.trend.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>Trend (daily)</h4>
                <div style={{ display: "flex", gap: 4, alignItems: "flex-end", height: 60 }}>
                  {(() => {
                    const max = Math.max(...stats.trend.map((t) => t.count));
                    return stats.trend.map((t) => (
                      <div key={t.date} title={`${t.date}: ${t.count}`}
                           style={{ width: 8, background: "#2196f3", height: `${max? (t.count / max) * 100 : 0}%` }} />
                    ));
                  })()}
                </div>
              </div>
            )}
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

              <div className="form-group">
                <label>Assigned Department</label>
                <input
                  type="text"
                  value={statusForm.assigned_department}
                  onChange={(e) => setStatusForm({ ...statusForm, assigned_department: e.target.value })}
                  placeholder="e.g., Public Works Department"
                />
              </div>

              <div className="form-group">
                <label>Progress Images</label>
                <input type="file" multiple accept="image/*" onChange={(e) => setProgressFiles(Array.from(e.target.files || []))} />
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
