importScripts('https://www.gstatic.com/firebasejs/9.6.10/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.10/firebase-messaging-compat.js');
importScripts("https://www.gstatic.com/firebasejs/9.6.10/firebase-analytics-compat.js");
importScripts('https://storage.googleapis.com/workbox-cdn/releases/6.1.5/workbox-sw.js');

console.log("SERVICE WORKER")

workbox.setConfig({ debug: false });
const {clientsClaim} = workbox.core;
const {CacheableResponsePlugin} = workbox.cacheableResponse;
const {Route, registerRoute} = workbox.routing;
const {CacheFirst, NetworkFirst, StaleWhileRevalidate, NetworkOnly} = workbox.strategies;
const {ExpirationPlugin} = workbox.expiration;
const {precacheAndRoute} = workbox.precaching;
const {enable} = workbox.navigationPreload;
const {RangeRequestsPlugin} = workbox.rangeRequests;

addEventListener('install', (event) => {
  console.log("INSTALL")
});
addEventListener('activate', event => {
  console.log("ACTIVATE")
  event.waitUntil(enable())
});



async function cacheKeyWillBeUsed({request, mode}){

  let url = new URL(request.url);
  // console.log('url.origin + url.pathname ', url.origin + url.pathname)
  let raw = new URL(url.origin + url.pathname)
  // console.log('raw ', raw.href)
  return raw.href;
}
async function cachedResponseWillBeUsed({cache, request, cachedResponse}){
  console.log('cachedResponseWillBeUsed')
  if (cachedResponse) {
    return cachedResponse;
  }
  let url = new URL(request.url);
  let urlToMatch = url.origin + url.pathname;
  console.log("urlToMatch ", urlToMatch)
  return caches.match(urlToMatch);
}

registerRoute(
  ({url}) => url.origin === 'https://fonts.googleapis.com' ||
             url.origin === 'https://fonts.gstatic.com' || 
             url.origin === 'https://gstatic.com',
  new CacheFirst({
    cacheName: 'google-cache',
    plugins: [    
      new ExpirationPlugin({maxEntries: 20}),
    ],
  }),
);

registerRoute(
  ({ url }) => 
    url.origin === 'https://sgp1.digitaloceanspaces.com' ,
    new CacheFirst({
      cacheName: 'static_cache',
      fetchOptions: {
        credentials: 'same-origin',
      },
      plugins: [
        {cacheKeyWillBeUsed},
        new RangeRequestsPlugin(),
        new CacheableResponsePlugin({
          statuses: [0, 200, 403],
          headers: {
            'X-Is-Cacheable': 'true',
          },
        }),
        new ExpirationPlugin({
          maxAgeSeconds: 604800, 
          purgeOnQuotaError: true,
          maxEntries: 100,
        }),
      ],
    }),
);


registerRoute(
  ({ url }) => 
    url.pathname.startsWith('/static/'),
    new CacheFirst({
      cacheName: 'static_cache',
      plugins: [
        {cacheKeyWillBeUsed},
        new RangeRequestsPlugin(),
        new CacheableResponsePlugin({
          statuses: [0, 200, 403],
          headers: {
            'X-Is-Cacheable': 'true',
          },
        }),
        new ExpirationPlugin({
          maxAgeSeconds: 604800, 
        }),
      ],
    }),
);

    


