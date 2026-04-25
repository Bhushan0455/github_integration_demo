/**
 * pages/Dashboard.jsx — User Dashboard (after login)
 * ====================================================
 * This page shows after the user logs in via GitHub OAuth.
 * It displays:
 * - The user's GitHub avatar and username
 * - An "Install GitHub App" button (Phase 3)
 * - List of installations and repos (Phase 3)
 * - Recent webhook events (Phase 4)
 *
 * IMPORTANT: This page reads the token from URL query params on first load.
 * After the OAuth callback, the backend redirects here with:
 *   /dashboard?token=xxx&username=xxx&avatar_url=xxx
 * We save the token and user info into AuthContext + localStorage.
 */

import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user, token, loading, login, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // ── Effect: Capture OAuth callback params from URL ───────────
  // When the user comes back from GitHub OAuth, the URL looks like:
  //   /dashboard?token=gho_xxx&username=bhushan&avatar_url=https://...
  // We extract these params, save them via login(), and clean the URL.
  useEffect(() => {
    const tokenFromUrl = searchParams.get("token");
    const usernameFromUrl = searchParams.get("username");
    const avatarFromUrl = searchParams.get("avatar_url");

    if (tokenFromUrl && usernameFromUrl) {
      // Save the token and user info into AuthContext + localStorage
      login(tokenFromUrl, {
        username: usernameFromUrl,
        avatar_url: avatarFromUrl,
      });

      // Clean the URL — remove the query params so the token isn't visible
      // in the browser address bar (basic security hygiene)
      navigate("/dashboard", { replace: true });
    }
  }, [searchParams, login, navigate]);

  // ── Effect: Redirect to login if not authenticated ───────────
  useEffect(() => {
    if (!loading && !user && !searchParams.get("token")) {
      navigate("/");
    }
  }, [user, loading, navigate, searchParams]);

  // ── Handle logout ────────────────────────────────────────────
  function handleLogout() {
    logout();
    navigate("/");
  }

  // ── Handle GitHub App installation ───────────────────────────
  // Redirects the user to GitHub's App installation page.
  // The user will select repos, then GitHub redirects back to /callback/install
  function handleInstallApp() {
    const appSlug = import.meta.env.VITE_GITHUB_APP_SLUG;
    if (!appSlug) {
      alert("VITE_GITHUB_APP_SLUG is not set in .env file!");
      return;
    }
    // This URL takes the user to GitHub's App installation page
    window.location.href = `https://github.com/apps/${appSlug}/installations/new`;
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="page-container">
      <div className="dashboard">
        {/* ── User Profile Card ──────────────────────────────── */}
        <div className="profile-card">
          <img
            src={user.avatar_url}
            alt={`${user.username}'s avatar`}
            className="avatar"
            id="user-avatar"
          />
          <div className="profile-info">
            <h2 id="user-username">{user.username}</h2>
            <p className="profile-badge">Authenticated via GitHub OAuth</p>
          </div>
          <button onClick={handleLogout} className="btn-logout" id="logout-btn">
            Sign Out
          </button>
        </div>

        {/* ── GitHub App Installation Section ────────────────── */}
        <div className="section-card">
          <h3 className="section-title">
            <span className="section-icon">+</span>
            GitHub App
          </h3>
          <p className="section-desc">
            Install the GitHub App on your account to grant access to selected repositories.
          </p>
          <button onClick={handleInstallApp} className="btn-primary" id="install-app-btn">
            Install GitHub App
          </button>
        </div>

        {/* ── Installations & Repos (Phase 3 placeholder) ────── */}
        <div className="section-card">
          <h3 className="section-title">
            <span className="section-icon">&lt;/&gt;</span>
            Installed Repositories
          </h3>
          <p className="empty-state">
            No installations yet. Install the GitHub App above to see your repos here.
          </p>
        </div>

        {/* ── Webhook Events (Phase 4 placeholder) ───────────── */}
        <div className="section-card">
          <h3 className="section-title">
            <span className="section-icon">*</span>
            Recent Webhook Events
          </h3>
          <p className="empty-state">
            No webhook events received yet. Push code to an installed repo to trigger webhooks.
          </p>
        </div>
      </div>
    </div>
  );
}
