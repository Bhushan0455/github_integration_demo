/**
 * pages/InstallCallback.jsx — GitHub App Installation Callback
 * =============================================================
 * Handles the redirect after a user installs our GitHub App.
 *
 * Flow:
 * 1. User clicks "Install GitHub App" on our dashboard.
 * 2. They are taken to GitHub, choose repositories, and authorize.
 * 3. GitHub redirects them here to: /callback/install?installation_id=123
 * 4. We grab the installation_id and send it to our backend.
 * 5. The backend uses it to fetch and save the selected repositories.
 * 6. We redirect the user back to the dashboard.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { saveInstallation } from "../api/github";

export default function InstallCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { token, loading } = useAuth();
  const [status, setStatus] = useState("Saving installation...");

  useEffect(() => {
    // If auth state is still loading, wait.
    if (loading) return;
    
    // If there's no auth token, the user isn't logged in. Redirect home.
    if (!token) {
      navigate("/");
      return;
    }

    const installationId = searchParams.get("installation_id");
    
    // If no installation_id is found in the URL, something went wrong.
    if (!installationId) {
      setStatus("Error: No installation_id found in URL.");
      setTimeout(() => navigate("/dashboard"), 3000);
      return;
    }

    async function handleInstall() {
      try {
        await saveInstallation(token, parseInt(installationId));
        setStatus("Installation saved! Redirecting to dashboard...");
        // Delay redirect slightly so the user sees the success message
        setTimeout(() => navigate("/dashboard"), 1500);
      } catch (error) {
        console.error("Failed to save installation:", error);
        setStatus("Failed to save installation. Please try again.");
      }
    }

    handleInstall();
  }, [searchParams, navigate, token, loading]);

  return (
    <div className="page-container">
      <div className="section-card" style={{ textAlign: "center" }}>
        <h2 style={{ marginBottom: "1rem" }}>GitHub App Installation</h2>
        <div className="loading-spinner" style={{ margin: "0 auto 1.5rem auto" }} />
        <p className="section-desc">{status}</p>
      </div>
    </div>
  );
}
