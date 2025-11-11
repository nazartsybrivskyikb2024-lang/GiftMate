"""
Universal entrypoint for Render deployment.
- Supports both: gunicorn app:app and python run_deploy.py
- Automatically runs migrations and collectstatic on first startup
- Then exposes Django WSGI application
"""
import os
import sys
import subprocess
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giftmate_project.settings')

import django
django.setup()

# Migration lock file to prevent running migrations multiple times
MIGRATION_LOCK_FILE = PROJECT_ROOT / '.migrations_done'

def run_migrations_once():
    """Run migrations only once per deployment."""
    if MIGRATION_LOCK_FILE.exists():
        print("[INFO] Migrations already applied (lock file exists), skipping...")
        return
    
    print("=" * 70)
    print("RUNNING DJANGO MIGRATIONS (first startup)")
    print("=" * 70)
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate', '--noinput'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"[ERROR] Migrations failed with code {result.returncode}")
            sys.exit(1)
        print("[OK] Migrations completed successfully")
        MIGRATION_LOCK_FILE.touch()
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)

def collect_static_once():
    """Collect static files once."""
    if (PROJECT_ROOT / 'staticfiles' / '.collectstatic_done').exists():
        print("[INFO] Static files already collected, skipping...")
        return
    
    print("=" * 70)
    print("COLLECTING STATIC FILES")
    print("=" * 70)
    try:
        (PROJECT_ROOT / 'staticfiles').mkdir(exist_ok=True)
        result = subprocess.run(
            [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"[ERROR] Collectstatic failed with code {result.returncode}")
            # Don't exit - static files failure shouldn't crash the app
        print("[OK] Static files collected")
        (PROJECT_ROOT / 'staticfiles' / '.collectstatic_done').touch()
    except Exception as e:
        print(f"[WARNING] Collectstatic failed: {e}")

# Run migrations and collectstatic on startup
run_migrations_once()
collect_static_once()

print("=" * 70)
print("DJANGO APPLICATION READY")
print("=" * 70)

# Export the Django WSGI application for gunicorn
from giftmate_project.wsgi import application

# Alias for compatibility with 'gunicorn app:app' command
app = application

# If this file is run as a script (not imported by gunicorn),
# start gunicorn manually
if __name__ == '__main__':
    import gunicorn.app.wsgiapp
    
    port = os.environ.get('PORT', '8000')
    sys.argv = [
        'gunicorn',
        'app:application',
        '--workers', '3',
        '--bind', f'0.0.0.0:{port}',
        '--access-logfile', '-',
        '--error-logfile', '-',
    ]
    
    app = gunicorn.app.wsgiapp.WSGIApplication()
    sys.exit(app.run())
