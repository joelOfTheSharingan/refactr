import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ✅ Builds directly into /docs for GitHub Pages
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'serve' ? '/' : '/refactr/',
  build: {
    outDir: '.', // output build into current (docs) folder
    emptyOutDir: false // don't delete source files
  }
}))
