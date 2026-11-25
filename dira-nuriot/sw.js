// Offline shell for the installed phone app. Network first (with "no-cache" so GitHub Pages' 10-minute HTTP cache
// doesn't hide a fresh build), falling back to the last cached copy when offline. Bump CACHE to drop old copies.
// Only same-origin files and Google Fonts are cached; image-gallery APIs (Pexels/Openverse) and the CBS refresh pass through.
const CACHE = "dira-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./assets/icon-192.png", "./assets/icon-512.png", "./assets/plan-128A5.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const u = new URL(e.request.url), mine = u.origin === location.origin, font = /fonts\.(googleapis|gstatic)\.com$/.test(u.hostname);
  if (!mine && !font) return;
  e.respondWith(fetch(mine ? e.request.url : e.request, mine ? { cache: "no-cache" } : {}).then(r => {
    if (r.ok || r.type === "opaque") { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || (e.request.mode === "navigate" ? caches.match("./index.html") : Response.error()))));
});
