const CACHE = 'gfc-v5';
const ASSETS = [
  '/german-flashcards/',
  '/german-flashcards/index.html',
  '/german-flashcards/manifest.json',
  '/german-flashcards/icon.svg'
];

// Install: cache all assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

// Activate: remove old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Fetch: serve from cache, update cache in background when online
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.open(CACHE).then(async cache => {
      const cached = await cache.match(e.request);
      const networkFetch = fetch(e.request).then(response => {
        if (response && response.status === 200) {
          cache.put(e.request, response.clone());
        }
        return response;
      }).catch(() => null);
      // Return cached immediately, update in background
      return cached || networkFetch;
    })
  );
});
