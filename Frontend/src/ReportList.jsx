
import React from "react";

function ReportList({ reports }) {
  return (
    <div className="mt-6 space-y-4">
      <h2 className="text-xl font-semibold">Reported Issues</h2>
      {reports.length === 0 ? (
        <p className="text-gray-600">No issues reported yet.</p>
      ) : (
        reports.map((report) => (
          <div key={report._id || report.id} className="bg-white p-4 rounded-lg shadow-md">
            <p className="text-lg"><strong>Issue:</strong> {report.description}</p>
            <p className="text-lg"><strong>Location:</strong> {report.location}</p>
            {report.image && (
              <img
                src={report.image.startsWith("uploads/") ? `http://localhost:8000/${report.image}` : report.image}
                alt="Uploaded"
                className="mt-2 rounded-lg w-48"
              />
            )}
            <p className="text-sm text-gray-500">Status: {report.status}</p>
            <p className="text-xs text-gray-400">Reported at: {new Date(report.created_at).toLocaleString()}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default ReportList;
