/* A-4f: Custom service worker extension.
 *
 * This file is merged into the next-pwa generated service worker via
 * the `customWorkerSrc` option in next.config.ts. It adds `push` and
 * `notificationclick` handlers on top of the Workbox-managed cache
 * lifecycle.
 *
 * The payload shape is controlled server-side by PushPayload
 * (infrastructure/api/push/service.py).
 */

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (_err) {
    data = { title: "DSI", body: event.data ? event.data.text() : "" };
  }

  const title = data.title || "Digital Signal Intelligence";
  const options = {
    body: data.body || "",
    icon: "/icons/icon-192.png",
    badge: "/icons/icon-badge-72.png",
    tag: data.category || "dsi-notification",
    renotify: true,
    data: { url: data.url || "/" },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    (async () => {
      const allClients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      // Focus an existing DSI tab if one is open, else open new
      for (const client of allClients) {
        if ("focus" in client) {
          try {
            await client.focus();
            if ("navigate" in client) {
              await client.navigate(targetUrl);
            }
            return;
          } catch (_err) {
            // fall through to openWindow
          }
        }
      }
      if (self.clients.openWindow) {
        await self.clients.openWindow(targetUrl);
      }
    })(),
  );
});
