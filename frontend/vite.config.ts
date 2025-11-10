import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    allowedHosts: [
      '.ngrok-free.dev', // Allow all ngrok domains
      '.ngrok.io',
      '.loca.lt',
      'uj9kgbuwz0.eu.loclx.io', // Added your loclx.io host
      ''
       // If you use localtunnel
    ]
  },
})