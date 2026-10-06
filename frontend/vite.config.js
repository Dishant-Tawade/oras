import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = process.env.ORAS_BACKEND || 'localhost:8080'

// Ignore the connection-reset errors a browser tab close produces on the WebSocket proxy.
const isBenign = (err) => err.code === 'ECONNRESET' || err.code === 'EPIPE'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: `http://${BACKEND}`, changeOrigin: true },
      '/ws': {
        target: `ws://${BACKEND}`,
        ws: true,
        configure: (proxy) => {
          const quiet = (label) => (err) => { if (!isBenign(err)) console.error(label, err.message) }
          proxy.on('error', quiet('[proxy error]'))
          proxy.on('proxyReqWs', (_req, _res, socket) => socket.on('error', quiet('[ws socket error]')))
          proxy.on('open', (proxySocket) => proxySocket.on('error', quiet('[ws proxy socket error]')))
        },
      },
    },
  },
})
