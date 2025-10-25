// Firebase Messaging Service Worker
// This file must be in the root of the domain or under /public for Vite

// Deprecated Firebase messaging service worker.
// FCM and related service worker logic were removed from the project.
// This minimal file is left as a placeholder to avoid broken references.

self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => { self.clients.claim(); });
