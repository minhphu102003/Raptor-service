import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import tailwindcss from '@tailwindcss/vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Nếu truy cập qua proxy / VM mà HMR không bắt được,
    // mở dòng dưới để ép client dùng đúng cổng host:
    // hmr: { clientPort: 5173 },
    // watch: { usePolling: true }, // tuỳ môi trường
  },
  plugins: [
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
    tsconfigPaths(),
    tailwindcss(),
  ],
})
