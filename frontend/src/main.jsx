/**
 * main.jsx — React App Entry Point
 * ==================================
 * This is the very first file that runs.
 * It mounts our <App /> component into the HTML page.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
