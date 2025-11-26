// Notification WebSocket handling
function initNotificationWebSocket() {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socketUrl = `${wsProtocol}://${window.location.host}/ws/notifications/`;
    let notificationSocket = null;
    let notificationsDropdown = null;
    let notificationsList = null;

    function connect() {
        try {
            notificationSocket = new WebSocket(socketUrl);

            notificationSocket.onopen = () => {
                console.log("✅ Notification WebSocket connected");
            };

            notificationSocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📩 Notification WS received:', data);
                    
                    // Handle notification messages
                    if (data.type === 'notification' || data.from) {
                        showNotification(data);
                        if (data.from) addNotificationToMenu(data);
                        updateNotificationBadge();
                    }
                    // Handle notification count updates
                    else if (data.type === 'notification_count') {
                        const badge = document.getElementById('notification-count');
                        if (badge && data.count > 0) {
                            badge.textContent = data.count;
                            badge.style.display = 'block';
                        }
                    }
                } catch (err) {
                    console.error('Failed to parse notification', err);
                }
            };

            notificationSocket.onclose = () => {
                console.log("Notification WebSocket closed. Reconnecting in 3s...");
                setTimeout(connect, 3000);
            };

        } catch (e) {
            console.error('Failed to connect to notification socket', e);
            setTimeout(connect, 3000);
        }
    }

    function showNotification(data) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'toast-card fade-in notification-toast';
        
        let preview = data.message_preview;
        if (data.photo_included) {
            preview = 'Надіслано фото' + (data.message_preview ? ': ' + data.message_preview : '');
        }
        
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${data.photo_included ? 'image' : 'envelope'} me-2"></i>
                <div>
                    <div class="fw-bold">${data.from}</div>
                    <div class="small">${preview || 'Нове повідомлення'}</div>
                </div>
            </div>
        `;
        
        // Make notification clickable
        if (data.conversation_id) {
            notification.style.cursor = 'pointer';
            notification.onclick = () => {
                window.location.href = `/chat/conversation/${data.conversation_id}/`;
            };
        }
        
        // Add to notifications container
        const container = document.getElementById('global-toast');
        if (container) {
            container.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
        
        // Play notification sound
        playNotificationSound();
    }

    function playNotificationSound() {
        const audio = new Audio('/static/gifts/notification.mp3');
        audio.play().catch(err => console.log('Failed to play notification sound'));
    }

    function updateNotificationBadge() {
        const badge = document.getElementById('notification-count');
        if (badge) {
            let count = parseInt(badge.textContent || '0');
            count += 1;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    function addNotificationToMenu(data) {
        const notifList = document.getElementById('notifications-list');
        if (!notifList || !data.from) return;
        
        // Очистити placeholder якщо це перше повідомлення
        if (notifList.innerHTML.includes('Немає нових сповіщень')) {
            notifList.innerHTML = '';
        }
        
        const notifItem = document.createElement('div');
        notifItem.className = 'dropdown-item border-bottom p-3';
        const preview = data.message_preview || data.text || 'Нове повідомлення';
        notifItem.innerHTML = `
            <div class="d-flex gap-2">
                <div>
                    <strong class="d-block">${data.from || 'Unknown'}</strong>
                    <small class="text-muted">${preview}</small>
                </div>
            </div>
        `;
        notifItem.style.cursor = 'pointer';
        if (data.conversation_id) {
            notifItem.onclick = () => {
                window.location.href = `/chat/conversation/${data.conversation_id}/`;
            };
        }
        notifList.insertBefore(notifItem, notifList.firstChild);
    }

    // Start the connection
    connect();
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.IS_AUTHENTICATED) {
        initNotificationWebSocket();
    }
});