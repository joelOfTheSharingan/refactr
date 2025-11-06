import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',     // Ensures relative paths for GitHub Pages
  build: {
    outDir: 'docs',  // So build goes directly into docs/
  },
})

