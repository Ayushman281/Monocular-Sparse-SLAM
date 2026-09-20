import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: false,
  },
};

export default defineConfig(({mode}) => ({
  plugins: [react()],
  publicDir: mode === 'hosted' ? 'public-hosted' : 'public',
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: apiProxy,
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // Lightning assigns the public hostname after the port is exposed. Preview
    // serves built assets only; accepting that generated Host is intentional.
    allowedHosts: true,
    proxy: apiProxy,
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'same-origin',
      'X-Frame-Options': 'SAMEORIGIN',
    },
  },
}));
