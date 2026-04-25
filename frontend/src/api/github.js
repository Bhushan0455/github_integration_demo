/**
 * api/github.js — Backend API Helper Functions
 * ==============================================
 * This file contains all the functions that call our FastAPI backend.
 * Think of it as a centralized place for all API calls — instead of
 * writing fetch() in every component, we write it once here.
 *
 * Every function follows the same pattern:
 * 1. Build the URL to our backend
 * 2. Add the Authorization header (if the user is logged in)
 * 3. Make the request
 * 4. Return the JSON response
 */

// Read the backend URL from environment variables
// In Vite, env vars must start with VITE_ to be accessible in the browser
const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

/**
 * Get the current user's profile.
 *
 * Calls: GET /auth/me
 * Requires: Authorization header with the user's access token
 *
 * This is called when the Dashboard loads to verify the user is logged in
 * and to fetch their latest profile info (username, avatar).
 *
 * @param {string} token - The GitHub OAuth access token
 * @returns {Object} User profile: { id, github_id, username, avatar_url }
 */
export async function fetchCurrentUser(token) {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      // The "Bearer" prefix is a standard way to send tokens in HTTP headers
      // Format: "Bearer <your-token-here>"
      Authorization: `Bearer ${token}`,
    },
  });

  // If the token is invalid or expired, the backend returns 401
  if (!response.ok) {
    throw new Error("Failed to fetch user profile — token may be invalid");
  }

  return response.json();
}

/**
 * Get the URL to start the GitHub OAuth login flow.
 *
 * This doesn't make an API call — it just builds the URL that the browser
 * should navigate to. The backend will then redirect to GitHub.
 *
 * Flow: Browser navigates to this URL → Backend → GitHub Login Page
 *
 * @returns {string} The backend OAuth start URL
 */
export function getGitHubLoginUrl() {
  return `${API_BASE}/auth/github`;
}

/**
 * Save a new GitHub App installation and its selected repositories.
 * 
 * Calls: POST /github/installations/save
 * Requires: Authorization header
 * 
 * @param {string} token - The user's OAuth access token
 * @param {number} installationId - The installation_id from GitHub's callback URL
 */
export async function saveInstallation(token, installationId) {
  const response = await fetch(`${API_BASE}/github/installations/save`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ installation_id: installationId }),
  });

  if (!response.ok) {
    throw new Error("Failed to save installation");
  }

  return response.json();
}

/**
 * Get all tracked GitHub App installations for the current user.
 * 
 * Calls: GET /github/installations
 * Requires: Authorization header
 * 
 * @param {string} token - The user's OAuth access token
 * @returns {Array} List of installations and their selected repos
 */
export async function fetchInstallations(token) {
  const response = await fetch(`${API_BASE}/github/installations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch installations");
  }

  return response.json();
}

/**
 * Get recent webhook events received by the backend.
 * 
 * Calls: GET /webhook/recent
 * Requires: Authorization header
 * 
 * @param {string} token - The user's OAuth access token
 * @returns {Array} List of recent webhook events
 */
export async function fetchRecentWebhooks(token) {
  const response = await fetch(`${API_BASE}/webhook/recent`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch recent webhooks");
  }

  return response.json();
}
