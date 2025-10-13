import React, { useState } from "react";

function ReportForm({ onSubmit }) {
  const [issue, setIssue] = useState("");
  const [location, setLocation] = useState("");
  const [image, setImage] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (issue && location) {
      onSubmit({ issue, location, image });
      setIssue("");
      setLocation("");
      setImage(null);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white p-6 rounded-lg shadow-lg space-y-4 max-w-md mx-auto"
    >
      <h2 className="text-xl font-semibold">Report an Issue</h2>
      <input
        type="text"
        placeholder="Describe the issue (e.g., pothole, garbage)"
        value={issue}
        onChange={(e) => setIssue(e.target.value)}
        className="w-full border p-3 rounded-lg text-lg"
        required
      />
      <input
        type="text"
        placeholder="Location (Street, Area)"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
        className="w-full border p-3 rounded-lg text-lg"
        required
      />
      <input
        type="file"
        onChange={(e) => setImage(e.target.files[0])}
        className="w-full text-lg"
      />
      <button
        type="submit"
        className="w-full bg-green-600 text-white py-3 rounded-lg text-lg hover:bg-green-700"
      >
        Submit Report
      </button>
    </form>
  );
}

export default ReportForm;
