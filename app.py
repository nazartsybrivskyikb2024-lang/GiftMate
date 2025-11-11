"""
Compatibility entrypoint for platforms that run `gunicorn app:app`.
It imports the Django WSGI application and exposes it as the module-level variable `app`.
This avoids "ModuleNotFoundError: No module named 'app'" when the provider has an override Start Command.
"""

# Ensure the project's settings are configured inside giftmate_project.wsgi
from giftmate_project.wsgi import application as app
