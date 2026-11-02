import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { rollupOptions: { output: { manualChunks(id) {
    if (id.includes('/node_modules/zrender/')) return 'render-engine'
    if (id.includes('/node_modules/echarts/')) return 'charts'
    if (/\/node_modules\/(d3[^/]*|internmap|delaunator|robust-predicates)\//.test(id)) return 'network'
  } } } },
})
