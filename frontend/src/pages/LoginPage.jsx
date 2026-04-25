/**
 * pages/LoginPage.jsx — GitHub OAuth Login Page
 * ===============================================
 * This is the first page users see. It has a single button:
 * "Sign in with GitHub" that starts the OAuth flow.
 *
 * When clicked, the browser navigates to our backend's /auth/github,
 * which then redirects to GitHub's login page.
 */

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getGitHubLoginUrl } from "../api/github";

export default function LoginPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  // If the user is already logged in, redirect them to the dashboard
  useEffect(() => {
    if (!loading && user) {
      navigate("/dashboard");
    }
  }, [user, loading, navigate]);

  // ── Handle the login button click ───────────────────────────
  // We use window.location.href instead of fetch() because OAuth
  // requires a FULL PAGE REDIRECT to GitHub's login page.
  // The user needs to see GitHub's page to enter their credentials.
  function handleLogin() {
    window.location.href = getGitHubLoginUrl();
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="login-card">
        {/* Header with app icon */}
        <div className="login-header">
          <div className="app-icon">
            <svg viewBox="0 0 24 24" width="40" height="40" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </div>
          <h1>GitHub Integration Demo</h1>
          <p className="login-subtitle">
            Learn GitHub OAuth, Apps, and Webhooks
          </p>
        </div>

        {/* Login button */}
        <button onClick={handleLogin} className="btn-github" id="github-login-btn">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          Sign in with GitHub
        </button>

        {/* Explanation for learners */}
        <div className="login-info">
          <h3>What happens when you click?</h3>
          <ol>
            <li>You're redirected to GitHub's login page</li>
            <li>You authorize this app to read your profile</li>
            <li>GitHub sends you back here with your info</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
