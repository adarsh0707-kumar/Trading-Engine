import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],\n  server: {\n    proxy: {\n      "/api": {\n        target: "http://localhost:8080",\n        changeOrigin: true,\n      },\n      "/ws": {\n        target: "ws://localhost:8080",\n        ws: true,\n      },\n    },\n  },
});
