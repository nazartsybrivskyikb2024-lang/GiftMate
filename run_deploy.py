#!/usr/bin/env python
"""
Deployment helper: runs migrations and collectstatic before starting Gunicorn.
This ensures the database is initialized even if Render's build phase is skipped.
"""
import os
import sys
import subprocess
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giftmate_project.settings')

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

django.setup()

# Run migrations
print("=" * 60)
print("Running Django migrations...")
print("=" * 60)
try:
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
    print("✓ Migrations completed successfully")
except subprocess.CalledProcessError as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)

# Collect static files
print("=" * 60)
print("Collecting static files...")
print("=" * 60)
try:
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
    print("✓ Static files collected successfully")
except subprocess.CalledProcessError as e:
    print(f"✗ Collectstatic failed: {e}")
    sys.exit(1)

# Start Gunicorn
print("=" * 60)
print("Starting Gunicorn...")
print("=" * 60)
port = os.environ.get('PORT', '8000')
subprocess.run([
    'gunicorn',
    'giftmate_project.wsgi:application',
    '--workers', '3',
    '--bind', f'0.0.0.0:{port}',
])
