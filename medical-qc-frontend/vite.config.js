// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // 👇 必须添加 server.proxy 配置
  server: {
    port: 5173, // 前端端口 (禁止修改)
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000', // FastAPI 后端地址 (禁止修改)
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://localhost:8000', // FastAPI 后端地址 (禁止修改)
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
