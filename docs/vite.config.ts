import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ✅ dynamic base: "/" locally, "/refactr/" on GitHub Pages
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'serve' ? '/' : '/refactr/',
}))
