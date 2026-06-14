(function () {
    const POLL_INTERVAL_MS = 15000;
    const STORAGE_KEY = "shown_notification_ids";

    const pushButton = document.querySelector("[data-push-enable]");
    const notifLink = document.querySelector("[data-notifications-link]");

    if (!notifLink) {
        return;
    }

    function getShownIds() {
        try {
            return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"));
        } catch {
            return new Set();
        }
    }

    function saveShownIds(ids) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(ids).slice(-100)));
    }

    function updateBadge(count) {
        let badge = notifLink.querySelector(".badge");

        if (count > 0) {
            if (!badge) {
                badge = document.createElement("span");
                badge.className = "badge";
                notifLink.appendChild(badge);
            }
            badge.textContent = count;
            return;
        }

        if (badge) {
            badge.remove();
        }
    }

    function updatePushButton() {
        if (!pushButton || !("Notification" in window)) {
            return;
        }

        pushButton.hidden = Notification.permission !== "default";
    }

    async function enablePushNotifications() {
        if (!("Notification" in window)) {
            return;
        }

        await Notification.requestPermission();
        updatePushButton();
    }

    function showBrowserNotification(notification) {
        if (!("Notification" in window) || Notification.permission !== "granted") {
            return;
        }

        const browserNotification = new Notification("Заметки", {
            body: notification.message,
            tag: notification.id,
        });

        browserNotification.onclick = function () {
            window.focus();
            window.location.href = notification.note_id
                ? `/notes/${notification.note_id}/edit`
                : "/notifications/";
        };
    }

    async function pollUnreadNotifications() {
        try {
            const response = await fetch("/notifications/unread", {
                headers: { "Accept": "application/json" },
            });

            if (!response.ok) {
                return;
            }

            const data = await response.json();
            const shownIds = getShownIds();

            updateBadge(data.unread_count || 0);

            for (const notification of data.notifications || []) {
                if (shownIds.has(notification.id)) {
                    continue;
                }

                shownIds.add(notification.id);
                showBrowserNotification(notification);
            }

            saveShownIds(shownIds);
        } catch {
            // Network hiccups are fine; the next poll will try again.
        }
    }

    if (pushButton) {
        pushButton.addEventListener("click", enablePushNotifications);
    }

    updatePushButton();
    pollUnreadNotifications();
    setInterval(pollUnreadNotifications, POLL_INTERVAL_MS);
})();
