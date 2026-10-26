import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  server: {
    host: '0.0.0.0',       // Allows external devices like your phone to connect
    allowedHosts: 'all',   // 👈 This completely removes the "Invalid Host Header" error
    proxy: {
      '/api': {
        // Updated to use localhost so it routes correctly dynamically
        target: 'http://localhost:5000', 
        changeOrigin: false,
      },
    },
  },
})
