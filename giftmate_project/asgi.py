import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giftmate_project.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import chat.routing


class ScopeLoggerMiddleware:
    """ASGI middleware that logs scope type and path for debugging websocket routing."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            typ = scope.get('type')
            path = scope.get('path') or scope.get('raw_path')
            # inspect headers for websocket upgrade hints
            headers = dict((k.decode('latin1'), v.decode('latin1')) for k, v in scope.get('headers', [])) if scope.get('headers') else {}
            upgrade = headers.get('upgrade') or headers.get('Upgrade')
            swk = headers.get('sec-websocket-key')
            print(f"[ASGI LOGGER] scope type={typ} path={path} upgrade={bool(upgrade)} sec-websocket-key={'present' if swk else 'absent'}")
        except Exception as e:
            print(f"[ASGI LOGGER] failed to log scope: {e}")
        return await self.app(scope, receive, send)


app = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})

# Wrap the app with logging middleware to debug websocket connections
application = ScopeLoggerMiddleware(app)
