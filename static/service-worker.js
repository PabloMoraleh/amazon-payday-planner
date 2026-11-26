self.addEventListener("push", (event) => {
    let data = {};

    if (event.data) {
        try {
            data = event.data.json();
        } catch {
            data = { body: event.data.text() };
        }
    }

    event.waitUntil(
        self.registration.showNotification(data.title || "Payday Planner", {
            body: data.body || "",
            tag: "monthly-wishlist-reminder",
            data: { url: data.url || "/wishes" }
        })
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    const destination = new URL(event.notification.data?.url || "/wishes", self.location.origin).href;

    event.waitUntil(
        clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
            for (const windowClient of windows) {
                if (windowClient.url === destination && "focus" in windowClient) {
                    return windowClient.focus();
                }
            }
            return clients.openWindow(destination);
        })
    );
});
