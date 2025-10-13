import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    password: "",
    role: "citizen",
    gram_panchayat: "",
    address: "",
    id_proof_type: "",
    id_proof_number: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (response.ok) {
        alert("Registration successful! Please login.");
        navigate("/login");
      } else {
        setError(data.detail || "Registration failed");
      }
    } catch (error) {
      console.error("Error registering:", error);
      setError("Error connecting to server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>📝 Create Account</h2>
        <p className="auth-subtitle">Register for GramaFix</p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="role">Select Your Role *</label>
            <select id="role" name="role" value={form.role} onChange={handleChange} required>
              <option value="citizen">👤 Citizen</option>
              <option value="officer">👮 Gram Panchayat Officer</option>
              <option value="admin">⚙️ Government Official</option>
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input type="text" id="name" name="name" value={form.name} onChange={handleChange} placeholder="Enter your full name" required />
            </div>
            <div className="form-group">
              <label htmlFor="phone">Phone Number *</label>
              <input type="tel" id="phone" name="phone" value={form.phone} onChange={handleChange} placeholder="10-digit mobile" pattern="[0-9]{10}" required />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address *</label>
            <input type="email" id="email" name="email" value={form.email} onChange={handleChange} placeholder="your.email@example.com" required />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password *</label>
            <input type="password" id="password" name="password" value={form.password} onChange={handleChange} placeholder="Minimum 6 characters" minLength="6" required />
          </div>

          <div className="form-group">
            <label htmlFor="gram_panchayat">Gram Panchayat *</label>
            <input type="text" id="gram_panchayat" name="gram_panchayat" value={form.gram_panchayat} onChange={handleChange} placeholder="Your gram panchayat" required />
          </div>

          <div className="form-group">
            <label htmlFor="address">Address</label>
            <textarea id="address" name="address" value={form.address} onChange={handleChange} placeholder="Your full address" rows="2" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="id_proof_type">ID Proof Type</label>
              <select id="id_proof_type" name="id_proof_type" value={form.id_proof_type} onChange={handleChange}>
                <option value="">Select ID Type</option>
                <option value="Aadhaar">Aadhaar Card</option>
                <option value="Voter ID">Voter ID</option>
                <option value="Driving License">Driving License</option>
                <option value="PAN Card">PAN Card</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="id_proof_number">ID Proof Number</label>
              <input type="text" id="id_proof_number" name="id_proof_number" value={form.id_proof_number} onChange={handleChange} placeholder="Enter ID number" />
            </div>
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Registering..." : "📝 Register"}
          </button>
        </form>

        <p className="auth-link">
          Already have an account? <a href="/login">Login here</a>
        </p>
      </div>
    </div>
  );
}