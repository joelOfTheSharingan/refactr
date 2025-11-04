import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ✅ Works in both localhost and GitHub Pages
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'serve' ? '/' : '/refactr/',
  build: {
    outDir: '.',       // keep using docs for GitHub Pages
    emptyOutDir: false // prevent deleting source during build
  }
}))
