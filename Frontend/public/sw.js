const CACHE_NAME = 'gramafix-cache-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/src/main.jsx',
  '/src/App.jsx',
  '/src/index.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => k !== CACHE_NAME && caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Never intercept cross-origin requests (e.g., Firebase Auth Emulator, APIs)
  if (url.origin !== self.location.origin) {
    event.respondWith(
      fetch(req).catch(() => new Response('', { status: 502, statusText: 'Bad Gateway' }))
    );
    return;
  }
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).catch(() => new Response('', { status: 504, statusText: 'Gateway Timeout' }));
    })
  );
});
