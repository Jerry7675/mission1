import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      // Proxy API routes to FastAPI
      '/api': 'http://localhost:8000',
      // Proxy WebSocket route
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
  },
})