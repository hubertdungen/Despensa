const CACHE = "despensa-shell-v5.1";
const SHELL = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/static/features.js",
  "/logo.svg",
  "/icon-192.png",
  "/icon-512.png",
  "/manifest.webmanifest",
];
self.addEventListener("install", (event) =>
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL))),
);
self.addEventListener("activate", (event) =>
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  ),
);
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (
    event.request.method !== "GET" ||
    url.origin !== self.location.origin ||
    url.pathname.startsWith("/api/")
  )
    return;
  if (!SHELL.includes(url.pathname)) return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Never cache an authentication portal redirect as the application shell.
        if (
          response.ok &&
          !response.redirected &&
          new URL(response.url).origin === self.location.origin
        ) {
          const copy = response.clone();
          caches.open(CACHE).then((c) => c.put(event.request, copy));
        }
        return response;
      })
      .catch(() => caches.match(event.request)),
  );
});
