import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

const apiFallbackPlugin = () => ({
  name: 'api-fallback',
  configureServer(server) {
    return () => {
      server.middlewares.use((req, res, next) => {
        if (req.url && (req.url.startsWith('/api/') || req.url === '/api')) {
          if (!res.headersSent) {
            res.statusCode = 503;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({
              detail: 'THULIR backend server is offline or unreachable at http://127.0.0.1:8000. Please ensure the FastAPI backend is running.'
            }));
            return;
          }
        }
        next();
      });
    };
  },
  configurePreviewServer(server) {
    return () => {
      server.middlewares.use((req, res, next) => {
        if (req.url && (req.url.startsWith('/api/') || req.url === '/api')) {
          if (!res.headersSent) {
            res.statusCode = 503;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({
              detail: 'THULIR backend server is offline or unreachable at http://127.0.0.1:8000. Please ensure the FastAPI backend is running.'
            }));
            return;
          }
        }
        next();
      });
    };
  }
});

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const pwaEnabled = env.VITE_PWA_ENABLED !== 'false';

  return {
    plugins: [
      react(),
      apiFallbackPlugin(),
      pwaEnabled && VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'robots.txt'],
        manifest: {
          name: 'THULIR - Student Support System',
          short_name: 'THULIR',
          description: 'Early-Warning and Student Decision Support Platform',
          theme_color: '#0F172A',
          background_color: '#F8FAFC',
          display: 'standalone',
          icons: [
            {
              src: '/favicon.ico',
              sizes: '64x64 32x32 24x24 16x16',
              type: 'image/x-icon'
            }
          ]
        },
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/^\/api/],
          runtimeCaching: [
            {
              urlPattern: /^\/api\/.*/i,
              handler: 'NetworkOnly',
              options: {
                cacheName: 'api-disabled-cache',
              }
            }
          ]
        }
      })
    ].filter(Boolean),
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, res) => {
              if (res && !res.headersSent) {
                res.writeHead(503, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                  detail: 'THULIR backend server is unreachable at http://127.0.0.1:8000. Please start the backend service.'
                }));
              }
            });
          },
        },
      },
    },
    preview: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            'vendor-i18n': ['i18next', 'react-i18next'],
          },
        },
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.js',
    },
  };
});

