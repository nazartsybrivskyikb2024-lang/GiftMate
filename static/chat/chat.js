function initWebSocket(roomName, username) {
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socketUrl = `${wsProtocol}://${window.location.host}/ws/chat/${roomName}/`;
  const notifUrl = `${wsProtocol}://${window.location.host}/ws/notifications/`;
  let chatSocket = null;
  let notifSocket = null;
  let wsAvailable = false;
  const messagesContainer = document.getElementById("messages");
  let lastMessageId = 0;
  let pollInterval = null;

  if (!messagesContainer) {
    console.warn('No #messages container found. Chat UI will not render messages.');
  }

  function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (m) => (
      {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"}[m]
    ));
  }

  function updateNotificationBadge(count) {
    const badge = document.getElementById('notification-count');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'block' : 'none';
    }
  }

  function appendMessage(user, text, isMe = false, forwarded = null, id = null, photoUrl = null) {
    if (!messagesContainer) return;

    if (id) {
      const existing = messagesContainer.querySelector(`[data-message-id="${id}"]`);
      if (existing) return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${isMe ? "me" : "them"}`;

    let forwardedHtml = '';
    if (forwarded) {
      const img = forwarded.image ? `<img src="${forwarded.image}" class="gift-thumb" alt="" loading="lazy">` : '';
      const link = forwarded.id ? `<a href="/gift/${forwarded.id}/">Переглянути</a>` : '';
      forwardedHtml = `
        <div class="forwarded">
          ${img}
          <div>
            <div class="fw-bold">🎁 ${escapeHtml(forwarded.title || '')}</div>
            ${link}
          </div>
        </div>
      `;
    }

    let photoHtml = '';
    if (photoUrl) {
      photoHtml = `<div class="photo-container">
        <img src="${photoUrl}" class="chat-photo" alt="" loading="lazy"
             onclick="window.open('${photoUrl}', '_blank')">
      </div>`;
    }

    wrapper.innerHTML = `
      <div class="bubble">
        <div class="meta">
          <span class="username">${escapeHtml(user)}</span>
          <span class="time">${new Date().toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}</span>
        </div>
        ${text ? `<div class="text">${escapeHtml(text)}</div>` : ''}
        ${photoHtml}
        ${forwardedHtml}
      </div>
    `;

    if (id) wrapper.setAttribute('data-message-id', id);
    messagesContainer.appendChild(wrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function setLastIdFromElements() {
    const elems = messagesContainer.querySelectorAll('[data-message-id]');
    if (elems.length) {
      const last = elems[elems.length - 1];
      const id = parseInt(last.getAttribute('data-message-id')) || 0;
      lastMessageId = Math.max(lastMessageId, id);
    }
  }

  async function startPolling() {
    if (pollInterval) return;
    console.log('ℹ️ WebSocket not available, starting AJAX polling fallback');
    setLastIdFromElements();
    
    pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/chat/conversation/${roomName}/messages/?since_id=${lastMessageId}`, 
          { credentials: 'same-origin' }
        );
        if (res.ok) {
          const json = await res.json();
          (json.messages || []).forEach(m => {
            if (m.id && m.id <= lastMessageId) return;
            appendMessage(
              m.sender,
              m.text,
              m.sender === username,
              m.forwarded || null,
              m.id,
              m.photo_url || null
            );
            if (m.id) lastMessageId = Math.max(lastMessageId, m.id);
          });
        }
      } catch (e) {
        console.error('Polling failed:', e);
      }
    }, 2000);
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  }

  function showNotification(username, message) {
    // Desktop notification
    if ("Notification" in window) {
      if (Notification.permission === "granted") {
        new Notification(`Нове повідомлення від ${username}`, {
          body: message,
          icon: '/static/chat/notification-icon.png',
          tag: 'chat-message'  // Prevents duplicate notifications
        });
      } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
          if (permission === "granted") {
            new Notification(`Нове повідомлення від ${username}`, {
              body: message,
              icon: '/static/chat/notification-icon.png',
              tag: 'chat-message'
            });
          }
        });
      }
    }

    // Visual notification
    const toast = document.createElement('div');
    toast.className = 'notification-toast';
    toast.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-envelope"></i>
        <div>
          <div class="fw-bold">${escapeHtml(username)}</div>
          <div class="small">${escapeHtml(message)}</div>
        </div>
      </div>
    `;

    const container = document.getElementById('global-toast');
    if (container) {
      container.appendChild(toast);
      setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
      }, 5000);
    }
  }

  async function handlePhotoUpload(file) {
    if (file.size > 5 * 1024 * 1024) {
      alert('Файл занадто великий. Максимальний розмір 5MB');
      return null;
    }

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        // Create preview
        const previewContainer = document.getElementById('photo-preview');
        if (previewContainer) {
          const preview = document.createElement('img');
          preview.src = e.target.result;
          preview.style.maxWidth = '200px';
          preview.style.maxHeight = '200px';
          preview.style.display = 'block';
          preview.style.marginTop = '10px';
          previewContainer.innerHTML = '';
          previewContainer.appendChild(preview);
        }

        // Compress image if needed
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;

          // Scale down if too large
          if (width > 1200 || height > 1200) {
            const ratio = Math.min(1200 / width, 1200 / height);
            width *= ratio;
            height *= ratio;
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // Convert to JPEG with quality 0.8
          const compressedData = canvas.toDataURL('image/jpeg', 0.8);
          resolve(compressedData);
        };
        
        img.onerror = () => {
          reject(new Error('Failed to load image'));
        };
        
        img.src = e.target.result;
      };
      
      reader.onerror = () => {
        reject(reader.error);
      };
      
      reader.readAsDataURL(file);
    });
  }

  function initNotificationsWS() {
    try {
      notifSocket = new WebSocket(notifUrl);
      notifSocket.onopen = () => {
        console.log("✅ Notifications WebSocket connected");
      };
      notifSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'notification_count') {
            updateNotificationBadge(data.count);
          }
        } catch (err) {
          console.error('Failed to parse notifications WS message', err);
        }
      };
      notifSocket.onclose = () => {
        console.warn("⚠️ Notifications WebSocket closed. Reconnecting in 5s...");
        setTimeout(initNotificationsWS, 5000);
      };
      notifSocket.onerror = (e) => {
        console.warn('Notifications WebSocket error', e);
      };
    } catch (e) {
      console.error('Notifications WS connection failed:', e);
    }
  }

  function tryWebSocket() {
    try {
      chatSocket = new WebSocket(socketUrl);

      chatSocket.onopen = () => {
        wsAvailable = true;
        console.log("✅ WebSocket connected");
        stopPolling();
      };

      chatSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.message !== undefined || data.photo_url) {
            const isMe = data.username === username;
            appendMessage(
              data.username, 
              data.message, 
              isMe, 
              data.forwarded || null, 
              data.id || null,
              data.photo_url || null
            );
            if (data.id) lastMessageId = Math.max(lastMessageId, data.id);

            if (!isMe && document.hidden) {
              showNotification(
                data.username,
                data.photo_url ? 'Надіслано нове фото' : data.message || ''
              );
            }
          }
        } catch (err) {
          console.error('Failed to parse WS message', err);
        }
      };

      chatSocket.onclose = () => {
        wsAvailable = false;
        console.warn("⚠️ WebSocket closed. Falling back to polling and reconnecting in 3s...");
        startPolling();
        setTimeout(() => tryWebSocket(), 3000);
      };

      chatSocket.onerror = (e) => {
        console.warn('WebSocket error', e);
      };
    } catch (e) {
      console.error('WebSocket connection failed:', e);
      wsAvailable = false;
      startPolling();
    }
  }

  async function sendMessageAJAX(text) {
    const csrftoken = getCookie('csrftoken');
    try {
      const res = await fetch(`/chat/conversation/${roomName}/send/`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'X-CSRFToken': csrftoken,
        },
        body: new URLSearchParams({ text }),
      });

      if (res.ok) {
        const j = await res.json();
        if (j.id) lastMessageId = Math.max(lastMessageId, j.id);
        appendMessage(j.sender, j.text, true, j.forwarded || null, j.id, j.photo_url || null);
      }
    } catch (e) {
      console.error('AJAX send failed:', e);
      alert('Не вдалося надіслати повідомлення. Спробуйте ще раз.');
    }
  }

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  // Setup form and photo input handling
  const form = document.getElementById("msg-form");
  const photoInput = document.getElementById("photo-input");
  
  if (photoInput) {
    photoInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      if (file.type.startsWith('image/')) {
        try {
          const photoData = await handlePhotoUpload(file);
          if (photoData) {
            if (wsAvailable && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
              chatSocket.send(JSON.stringify({
                type: 'photo',
                photo: photoData,
                message: ''
              }));
              const previewContainer = document.getElementById('photo-preview');
              if (previewContainer) {
                previewContainer.innerHTML = '';
              }
            } else {
              alert('З\'єднання з сервером втрачено. Спробуйте пізніше.');
              const previewContainer = document.getElementById('photo-preview');
              if (previewContainer) {
                previewContainer.innerHTML = '';
              }
            }
          }
        } catch (err) {
          console.error('Failed to handle photo:', err);
          alert('Помилка при обробці фото. Спробуйте ще раз.');
        }
      } else {
        alert('Будь ласка, виберіть файл зображення');
      }
      photoInput.value = '';
    });
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("message-input");
      const message = input.value.trim();
      if (!message) return;
      
      if (wsAvailable && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        try {
          chatSocket.send(JSON.stringify({ 
            type: 'text',
            message
          }));
          input.value = "";
          input.focus();
        } catch (err) {
          console.error('WS send failed:', err);
          sendMessageAJAX(message);
          input.value = "";
        }
      } else {
        sendMessageAJAX(message);
        input.value = "";
      }
    });
  }

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      if (notifSocket && notifSocket.readyState === WebSocket.OPEN) {
        notifSocket.send(JSON.stringify({ type: 'mark_read' }));
      }
    }
  });

  initNotificationsWS();
  tryWebSocket();
  setTimeout(() => { if (!wsAvailable) startPolling(); }, 800);

  return {
    stop: () => { 
      if (chatSocket) chatSocket.close();
      if (notifSocket) notifSocket.close();
      stopPolling();
    }
  };
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
  if (typeof CHAT_ROOM_NAME !== "undefined" && typeof CURRENT_USERNAME !== "undefined") {
    window.chatInstance = initWebSocket(CHAT_ROOM_NAME, CURRENT_USERNAME);
  }
});