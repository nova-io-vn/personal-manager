import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  // Capacitor WebView on older Android tablets can lag behind desktop Chromium.
  build: { target: 'chrome74' },
  plugins: [react(), tailwindcss()],
  server: { watch: { ignored: ['**/android/**', '**/.gradle-user/**'] } },
})
