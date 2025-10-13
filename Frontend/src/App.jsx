import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./Home";
import ReportIssue from "./ReportIssue";
import IssuesList from "./IssuesList";
import AdminDashboard from "./AdminDashboard";
import Register from "./Register";
import Login from "./Login";
import Profile from "./Profile";
import Header from "./Header";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/report" element={<ReportIssue />} />
            <Route path="/issues" element={<IssuesList />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>GramaFix © 2025 - Smart Rural Issue Reporting</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;