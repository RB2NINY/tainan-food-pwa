/* ============================================================
 * sw.js - 府城尋味 PWA Service Worker
 *
 * 快取策略：
 *   1. App Shell（HTML / manifest / icons）採用 "Cache First，
 *      失敗時回退到網路" 策略，確保離線也能開啟基本頁面。
 *   2. 外部資源（Tailwind CDN、Google Fonts、Unsplash 圖片等）
 *      採用 "Stale-While-Revalidate"：先回應快取，同時在背景
 *      更新快取，兼顧速度與新鮮度。
 *   3. 版本升級時，透過修改 CACHE_VERSION 讓舊快取自動清除。
 * ============================================================ */

const CACHE_VERSION = "v1.0.0";
const APP_SHELL_CACHE = `fucheng-app-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `fucheng-runtime-${CACHE_VERSION}`;

// 需要在安裝階段預先快取的核心檔案（App Shell）
const APP_SHELL_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-72x72.png",
  "./icons/icon-96x96.png",
  "./icons/icon-128x128.png",
  "./icons/icon-144x144.png",
  "./icons/icon-152x152.png",
  "./icons/icon-192x192.png",
  "./icons/icon-384x384.png",
  "./icons/icon-512x512.png",
  "./icons/icon-maskable-192x192.png",
  "./icons/icon-maskable-512x512.png",
  "./icons/apple-touch-icon.png"
];

/* ----------------------------------------------------------
 * install：預先快取 App Shell
 * -------------------------------------------------------- */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(APP_SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

/* ----------------------------------------------------------
 * activate：清除舊版本快取
 * -------------------------------------------------------- */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter(
              (name) =>
                name.startsWith("fucheng-") &&
                name !== APP_SHELL_CACHE &&
                name !== RUNTIME_CACHE
            )
            .map((name) => caches.delete(name))
        )
      )
      .then(() => self.clients.claim())
  );
});

/* ----------------------------------------------------------
 * fetch：依請求類型分派快取策略
 * -------------------------------------------------------- */
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // 只處理 GET 請求，避免影響 POST 等非快取請求
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;

  if (isSameOrigin) {
    // 同源請求（HTML / manifest / icons）：Cache First
    event.respondWith(cacheFirst(request));
  } else {
    // 跨網域資源（CDN / 字型 / 圖床）：Stale-While-Revalidate
    event.respondWith(staleWhileRevalidate(request));
  }
});

/**
 * Cache First 策略：
 * 先查快取，找不到才發出網路請求；網路請求成功後同步寫回快取。
 * 若連網路都失敗，且請求為導覽（頁面）請求，則退回快取中的 index.html。
 */
async function cacheFirst(request) {
  const cache = await caches.open(APP_SHELL_CACHE);
  const cached = await cache.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    if (request.mode === "navigate") {
      const fallback = await cache.match("./index.html");
      if (fallback) return fallback;
    }
    return new Response("目前處於離線狀態，且找不到快取內容。", {
      status: 503,
      statusText: "Service Unavailable",
      headers: { "Content-Type": "text/plain; charset=utf-8" }
    });
  }
}

/**
 * Stale-While-Revalidate 策略：
 * 立即回應快取內容（若有），同時在背景發出網路請求更新快取，
 * 讓下一次造訪能拿到最新版本。
 */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);

  const networkFetch = fetch(request)
    .then((response) => {
      if (response && response.status === 200) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);

  return cached || networkFetch;
}

/* ----------------------------------------------------------
 * message：支援頁面主動要求 Service Worker 立即接管（版本更新提示用）
 * -------------------------------------------------------- */
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
