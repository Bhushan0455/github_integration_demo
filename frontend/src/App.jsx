/**
 * App.jsx — Main Application Component
 * ======================================
 * This is the root component that sets up:
 * 1. React Router — handles page navigation (Login, Dashboard, etc.)
 * 2. AuthProvider — wraps everything to provide auth state globally
 *
 * Route structure:
 * - /             → LoginPage (Sign in with GitHub)
 * - /dashboard    → Dashboard (shows user profile, installations, webhooks)
 * - /callback/install → InstallCallback (handles GitHub App installation - Phase 3)
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import InstallCallback from "./pages/InstallCallback";

function App() {
  return (
    // BrowserRouter enables client-side routing (no full page reloads)
    <BrowserRouter>
      {/* AuthProvider wraps everything so all pages can access auth state */}
      <AuthProvider>
        <Routes>
          {/* Landing page — Sign in with GitHub */}
          <Route path="/" element={<LoginPage />} />

          {/* Dashboard — shown after successful login */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Phase 3: GitHub App installation callback */}
          <Route path="/callback/install" element={<InstallCallback />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
