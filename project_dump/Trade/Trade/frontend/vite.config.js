import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    hmr: {
      host: 'localhost',
      port: 5173,
      protocol: 'ws'
    },
    port: 5173,
    strictPort: false
  }
})
