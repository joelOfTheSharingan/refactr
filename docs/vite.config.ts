import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'serve' ? '/' : '/refactr/', // 👈 your repo name exactly
  build: {
    outDir: 'docs', // 👈 output build files here for GitHub Pages
  },
}))
