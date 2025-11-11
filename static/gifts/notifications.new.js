// Notification WebSocket handling
function initNotificationWebSocket() {
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socketUrl = `${wsProtocol}://${window.location.host}/ws/notifications/`;
    let notificationSocket = null;
    let notificationsDropdown = null;

    function setupNotificationUI() {
        const bell = document.getElementById('notification-bell');
        if (bell) {
            // Create dropdown container if it doesn't exist
            if (!notificationsDropdown) {
                notificationsDropdown = document.createElement('div');
                notificationsDropdown.className = 'dropdown-menu dropdown-menu-end p-0 shadow-sm';
                notificationsDropdown.style.width = '320px';
                notificationsDropdown.style.maxHeight = '400px';
                notificationsDropdown.style.overflowY = 'auto';
                
                // Add header
                const header = document.createElement('div');
                header.className = 'p-3 border-bottom d-flex align-items-center';
                header.innerHTML = `
                    <h6 class="mb-0">Сповіщення</h6>
                    <button class="btn btn-link btn-sm ms-auto" onclick="markAllRead()">
                        Позначити як прочитані
                    </button>
                `;
                notificationsDropdown.appendChild(header);
                
                // Add notifications container
                const container = document.createElement('div');
                container.id = 'notifications-list';
                container.className = 'list-group list-group-flush';
                notificationsDropdown.appendChild(container);
                
                bell.parentNode.style.position = 'relative';
                bell.parentNode.appendChild(notificationsDropdown);
            }

            // Toggle dropdown on bell click
            bell.addEventListener('click', (e) => {
                e.stopPropagation();
                notificationsDropdown.classList.toggle('show');
                if (notificationsDropdown.classList.contains('show')) {
                    markNotificationsRead();
                }
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!notificationsDropdown.contains(e.target) && !bell.contains(e.target)) {
                    notificationsDropdown.classList.remove('show');
                }
            });
        }
    }

    function addNotificationToDropdown(data) {
        const container = document.getElementById('notifications-list');
        if (!container) return;
        
        // Remove empty state if exists
        const emptyState = container.querySelector('.text-center');
        if (emptyState) {
            emptyState.remove();
        }
        
        const notification = document.createElement('a');
        notification.href = data.link || (data.conversation_id ? `/chat/conversation/${data.conversation_id}/` : '#');
        notification.className = 'list-group-item list-group-item-action';
        
        let icon = 'envelope';
        if (data.type === 'friend_request') icon = 'user-plus';
        else if (data.photo_included) icon = 'image';
        
        let preview = data.message_preview;
        if (data.photo_included) {
            preview = 'Надіслано фото' + (data.message_preview ? `: ${data.message_preview}` : '');
        }
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                    <i class="fas fa-${icon} text-primary"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${data.from}</h6>
                        <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                    </div>
                    <p class="mb-1 small text-truncate">${preview || 'Нове повідомлення'}</p>
                </div>
            </div>
        `;
        
        container.insertBefore(notification, container.firstChild);
        
        // Limit the number of notifications shown
        if (container.children.length > 10) {
            container.lastChild.remove();
        }
    }

    function updateNotificationBadge(count) {
        const badge = document.getElementById('notification-count');
        if (badge) {
            if (typeof count === 'number') {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'block' : 'none';
            } else {
                let currentCount = parseInt(badge.textContent || '0');
                currentCount += 1;
                badge.textContent = currentCount;
                badge.style.display = 'block';
            }
        }
    }

    function markNotificationsRead() {
        if (notificationSocket && notificationSocket.readyState === WebSocket.OPEN) {
            notificationSocket.send(JSON.stringify({
                type: 'mark_read'
            }));
            updateNotificationBadge(0);
        }
    }

    function showNotification(data) {
        // Create toast notification
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
        const link = data.link || (data.conversation_id ? `/chat/conversation/${data.conversation_id}/` : null);
        if (link) {
            notification.style.cursor = 'pointer';
            notification.onclick = () => window.location.href = link;
        }
        
        // Add to notifications container and dropdown
        const container = document.getElementById('global-toast');
        if (container) {
            container.appendChild(notification);
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
        
        // Add to dropdown list
        addNotificationToDropdown(data);
        
        // Play sound
        playNotificationSound();
        
        // Update badge
        updateNotificationBadge();
    }

    function playNotificationSound() {
        const audio = new Audio('/static/gifts/notification.mp3');
        audio.play().catch(() => {}); // Ignore errors
    }

    function connect() {
        try {
            notificationSocket = new WebSocket(socketUrl);

            notificationSocket.onopen = () => {
                console.log("✅ Notification WebSocket connected");
            };

            notificationSocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'notification_count') {
                        updateNotificationBadge(data.count);
                    } else {
                        showNotification(data);
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

    // Initialize
    setupNotificationUI();
    connect();

    // Return cleanup function
    return () => {
        if (notificationSocket) {
            notificationSocket.close();
        }
    };
}

// Add styles
const style = document.createElement('style');
style.textContent = `
.notification-toast {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

.notification-toast:hover {
    background: #f8f9fa;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.notification-content {
    display: flex;
    align-items: center;
}

.notification-content i {
    font-size: 1.25rem;
    color: #0d6efd;
}

.list-group-item-action:hover {
    background-color: #f8f9fa;
}

.fade-in {
    animation: fadeIn 0.3s ease-in;
}

.fade-out {
    animation: fadeOut 0.3s ease-out;
    opacity: 0;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOut {
    from { opacity: 1; transform: translateY(0); }
    to { opacity: 0; transform: translateY(-10px); }
}
`;
document.head.appendChild(style);

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.IS_AUTHENTICATED) {
        window.notificationHandler = initNotificationWebSocket();
    }
});