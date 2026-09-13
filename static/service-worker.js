self.addEventListener("push", (event) => {
    let data = {
        title: "DisasterShield AI",
        body: "New safety alert received.",
        data: {}
    };

    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (error) {
        console.error("Push payload error:", error);
    }

    const title = data.title || "DisasterShield AI";

    const options = {
        body: data.body || "New safety alert received.",
        icon: "/static/images/icon-192.png",
        badge: "/static/images/icon-192.png",
        data: data.data || {},
        requireInteraction: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then((clientList) => {
            for (const client of clientList) {
                if ("focus" in client) {
                    return client.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow("/");
            }
        })
    );
});
