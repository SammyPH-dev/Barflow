import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],

  server: {
    proxy: {
      // Forward recommendation requests to the backend.
      "/api/v1/recommendations": {
        target: "http://127.0.0.1:8005",
        changeOrigin: true,
      },
    },
  },
});