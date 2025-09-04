import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/onboarding": "http://localhost:8000",
      "/register": "http://localhost:8000",
      "/api/onboarding": "http://localhost:8000"
    }
  }
});
