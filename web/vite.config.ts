import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The backend base URL. Override with VITE_API_BASE_URL.
const apiBase = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiBase,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})