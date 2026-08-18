import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In Docker Compose, the frontend container must reach the backend by its
// service name ("backend"), not "localhost" -- set VITE_API_TARGET to
// override. Defaults to localhost for running `npm run dev` directly.
const apiTarget = process.env.VITE_API_TARGET || "http://localhost:8000";
const wsTarget = apiTarget.replace(/^http/, "ws");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": apiTarget,
      "/ws": {
        target: wsTarget,
        ws: true,
      },
    },
  },
});
