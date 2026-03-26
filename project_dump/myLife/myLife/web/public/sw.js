const CACHE = 'mylife-cache-v2'
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest'
]

const IS_DEV_HOST = self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1'

if (IS_DEV_HOST) {
  self.addEventListener('install', () => {
    self.skipWaiting()
  })

  self.addEventListener('activate', (event) => {
    event.waitUntil(
      caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k)))).then(() => self.registration.unregister())
    )
  })
} else {
  self.addEventListener('install', (event) => {
    event.waitUntil(
      caches.open(CACHE).then((cache) => cache.addAll(ASSETS))
    )
  })

  self.addEventListener('activate', (event) => {
    event.waitUntil(
      caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    )
  })
}

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return
  if (IS_DEV_HOST) return
  const url = new URL(request.url)
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return
  if (url.origin !== self.location.origin) return
  event.respondWith(
    caches.match(request).then((cached) =>
      cached || fetch(request).then((response) => {
        const clone = response.clone()
        caches.open(CACHE).then((cache) => cache.put(request, clone)).catch(() => {})
        return response
      })
    )
  )
})

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? JSON.parse(event.data.text()) : {}
  } catch (e) {
    data = { title: 'myLife', body: 'Keep the streak alive!' }
  }
  const title = data.title || 'myLife'
  const options = {
    body: data.body || 'Keep the streak alive!',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data,
  }
  event.waitUntil(self.registration.showNotification(title, options))
})
