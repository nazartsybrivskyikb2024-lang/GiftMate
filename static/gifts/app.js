document.addEventListener('click', function(e){
  if(e.target.matches('.like-btn')){
    const id = e.target.dataset.id
  fetch(`/gift/${id}/like/`, {method:'POST', headers:{'X-CSRFToken': getCookie('csrftoken')}, credentials: 'same-origin'})
      .then(r=>r.json()).then(d=>{
        const btns = document.querySelectorAll(`.like-btn[data-id="${id}"]`)
        btns.forEach(b=>{
          const span = b.querySelector('span')
          if(span) span.textContent = d.likes_count
        })
        const detailCount = document.getElementById('likes-count')
        if(detailCount) detailCount.textContent = d.likes_count
        // --- Notifications (real-time) -------------------------------------------------
        function initNotifications() {
          if (!window.IS_AUTHENTICATED || !window.CURRENT_USER_ID) return;
          const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws';
          const socketUrl = `${wsProto}://${window.location.host}/ws/notifications/`;
          let sock = null;
          const bell = document.getElementById('notification-bell');
          const badge = document.getElementById('notification-count');

          function showBadge(count) {
            if (!badge) return;
            badge.textContent = String(count);
            badge.style.display = count > 0 ? 'inline-block' : 'none';
          }

          function connect() {
            try {
              sock = new WebSocket(socketUrl);
              sock.onopen = () => {
                console.log('Notifications socket connected');
              };
              sock.onmessage = (e) => {
                try {
                  const d = JSON.parse(e.data);
                  // increment badge count (simple increment, server could send full count)
                  const cur = parseInt(badge ? badge.textContent || '0' : '0') || 0;
                  showBadge(cur + 1);
                  // show small toast
                  if (d && d.from) {
                    showToast(`${d.from}: ${d.message_preview || 'Нове повідомлення'}`, 'info', 4000);
                  }
                } catch (err) {
                  console.error('Invalid notification payload', err);
                }
              };
              sock.onclose = () => {
                console.warn('Notifications socket closed; retrying in 3s');
                setTimeout(connect, 3000);
              };
              sock.onerror = (e) => {
                console.warn('Notifications socket error', e);
              };
            } catch (e) {
              console.warn('Notifications WS not available', e);
            }
          }

          if (bell) {
            bell.addEventListener('click', () => {
              // on click, clear badge and optionally open a small notifications panel (not implemented yet)
              showBadge(0);
              showToast('Відкрийте розділ повідомлень (поки що тільки тест).', 'info', 2000);
            });
          }

          connect();
        }

        document.addEventListener('DOMContentLoaded', function() { initNotifications(); });

      })
  }
  if(e.target.matches('.save-btn')){
    const id = e.target.dataset.id
  fetch(`/gift/${id}/save/`, {method:'POST', headers:{'X-CSRFToken': getCookie('csrftoken')}, credentials: 'same-origin'})
      .then(r=>r.json()).then(d=>{
        e.target.textContent = d.status
      })
  }
})

const commentForm = document.getElementById('comment-form')
if(commentForm){
  commentForm.addEventListener('submit', function(ev){
    ev.preventDefault()
    const data = new FormData(commentForm)
    const giftId = location.pathname.split('/').filter(Boolean).pop()
  fetch(`/gift/${giftId}/comment/`, {method:'POST', body: data, headers:{'X-CSRFToken': getCookie('csrftoken')}, credentials: 'same-origin'})
      .then(r=>r.json()).then(d=>{
        if(d.status === 'ok') location.reload()
      })
  })
}

function getCookie(name){
  let v=document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');
  return v?v[2]:null
}

// Load more / infinite scroll
const loadMore = document.getElementById('load-more')
if(loadMore){
  loadMore.addEventListener('click', function(){
    const next = this.dataset.next
    fetch(`/?page=${next}`, {credentials:'same-origin'}).then(r=>r.text()).then(html=>{
      // cheaply parse returned html and append posts
      const tmp = document.createElement('div')
      tmp.innerHTML = html
      const newPosts = tmp.querySelectorAll('#feed .post')
      newPosts.forEach(n=>document.getElementById('feed').appendChild(n))
      // update next button
      const newBtn = tmp.querySelector('#load-more')
      if(newBtn) loadMore.dataset.next = newBtn.dataset.next
      else loadMore.remove()
    })
  })
}
