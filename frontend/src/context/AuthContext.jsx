/**
 * context/AuthContext.jsx — Authentication State Manager
 * ========================================================
 * This file manages the "who is logged in?" state across the entire app.
 *
 * WHY DO WE NEED THIS?
 * When the user logs in via GitHub OAuth, the backend redirects them back
 * to our frontend with the token in the URL. We need to:
 * 1. Read the token from the URL
 * 2. Save it somewhere persistent (localStorage) so it survives page refreshes
 * 3. Make it available to ALL components (Dashboard, etc.) without prop drilling
 *
 * React Context solves #3 — it's like a "global variable" that any component
 * can access without passing props down through every level.
 *
 * ⚠️ SECURITY NOTE:
 * We store the token in localStorage for demo simplicity.
 * In a production app, use secure HTTP-only cookies instead, because:
 * - localStorage is accessible to any JavaScript on the page (XSS risk)
 * - HTTP-only cookies are NOT accessible to JavaScript (much safer)
 */

import { createContext, useContext, useState, useEffect } from "react";
import { fetchCurrentUser } from "../api/github";

// ── Create the Context ────────────────────────────────────────────
// Think of this as creating a "container" that holds auth data.
// Any component wrapped in <AuthProvider> can access this data.
const AuthContext = createContext(null);

/**
 * AuthProvider — Wraps the entire app to provide auth state.
 *
 * Usage in App.jsx:
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 */
export function AuthProvider({ children }) {
  // ── State variables ──────────────────────────────────────────
  const [token, setToken] = useState(localStorage.getItem("github_token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── Effect: Load user data when the app starts ───────────────
  // This runs once when the component mounts (page load/refresh).
  // If we have a token saved, we fetch the user's profile from the backend.
  useEffect(() => {
    async function loadUser() {
      // If there's a token in localStorage, try to fetch the user profile
      if (token) {
        try {
          const userData = await fetchCurrentUser(token);
          setUser(userData);
        } catch (error) {
          // Token is invalid — clear everything
          console.error("Failed to load user:", error);
          localStorage.removeItem("github_token");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    }

    loadUser();
  }, [token]);

  // ── Login function ───────────────────────────────────────────
  // Called after the OAuth callback redirects to the dashboard with
  // the token in the URL query parameters.
  function login(newToken, userData) {
    // ⚠️ localStorage is used for demo simplicity.
    //    Production apps should use secure HTTP-only cookies.
    localStorage.setItem("github_token", newToken);
    setToken(newToken);
    setUser(userData);
  }

  // ── Logout function ──────────────────────────────────────────
  // Clears the token from localStorage and resets user state.
  function logout() {
    localStorage.removeItem("github_token");
    setToken(null);
    setUser(null);
  }

  // ── Provide the auth state to all child components ───────────
  // Any component can now call useAuth() to get token, user, login, logout
  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth — Custom hook to access auth state from any component.
 *
 * Usage in any component:
 *   const { user, token, login, logout } = useAuth();
 *
 *   if (user) {
 *     return <p>Hello, {user.username}!</p>;
 *   }
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return context;
}
