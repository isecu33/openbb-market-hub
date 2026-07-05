import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// En dev, el frontend corre en :5173 y proxya /api al backend FastAPI (:8000).
// En build, genera frontend/dist que el backend sirve directamente.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
        },
      },
    },
  },
});
