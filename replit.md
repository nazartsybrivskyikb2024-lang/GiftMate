# GiftMate - Django Gift Exchange Platform

## Overview
GiftMate is a Django-based web application for managing gift exchanges with real-time chat functionality. The application helps users find gift ideas, manage friend lists, and communicate with friends through an integrated chat system.

## Project Architecture

### Technology Stack
- **Backend Framework**: Django 5.1.6
- **Real-time Communication**: Django Channels with WebSocket support
- **ASGI Server**: Daphne 4.1.2
- **Database**: SQLite (development), PostgreSQL ready
- **Static Files**: WhiteNoise for production-ready static file serving
- **Image Processing**: Pillow for photo uploads

### Project Structure
```
giftmate_project/
├── chat/                  # Real-time chat application
│   ├── consumers.py      # WebSocket consumers
│   ├── routing.py        # WebSocket URL routing
│   ├── models.py         # Chat models (Message, Conversation, Notification)
│   └── templates/        # Chat UI templates
├── gifts/                # Main gift management application
│   ├── models.py         # Gift, Profile, Friend models
│   ├── views.py          # Gift catalog and management views
│   ├── friend_views.py   # Friend request handling
│   └── templates/        # Gift UI templates
├── giftmate_project/     # Django project settings
│   ├── settings.py       # Main configuration
│   ├── asgi.py          # ASGI application with WebSocket routing
│   └── urls.py          # URL routing
├── static/              # Static assets (CSS, JavaScript)
├── media/               # User-uploaded content
└── manage.py            # Django management script
```

### Key Features
1. **User Authentication**: Registration and login system
2. **Gift Catalog**: Browse and manage gift ideas
3. **Friend System**: Send/accept friend requests, manage friend lists
4. **Real-time Chat**: WebSocket-based messaging between friends
5. **Notifications**: Real-time notification system
6. **Profile Management**: User profiles with birthdays, interests, locations
7. **Photo Uploads**: Support for gift and message photos

## Development Setup

### Environment
- Python 3.11
- Django development server on 0.0.0.0:5000
- SQLite database (db.sqlite3)

### Configuration
The application is configured for the Replit environment with:
- `ALLOWED_HOSTS` includes Replit domains
- `CSRF_TRUSTED_ORIGINS` configured for Replit proxy
- `USE_X_FORWARDED_HOST` enabled for proxy support
- WebSocket support through Channels

### Database
- Current: SQLite for development
- Migrations applied and ready
- Can be switched to PostgreSQL using Replit's built-in database

### Static Files
- Static files collected to `staticfiles/`
- WhiteNoise serves static files efficiently
- Development server also serves static files

## Running the Application

### Development Server
The Django development server runs automatically via the configured workflow:
```bash
python manage.py runserver 0.0.0.0:5000
```

### Admin Access
To create a superuser for admin access:
```bash
python manage.py createsuperuser
```

### Migrations
Database migrations are already applied. To create new migrations after model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Recent Changes (November 26, 2025)
- Installed Python 3.11 and all dependencies
- Configured Django settings for Replit environment
- Added CSRF trusted origins for Replit proxy
- Ran all database migrations successfully
- Collected static files
- Configured Django Server workflow on port 5000
- Updated .gitignore for Replit environment
- Verified application is running correctly
- **Improved mobile chat responsiveness**:
  - Added comprehensive CSS media queries for tablets, smartphones, and small devices
  - Improved chat input layout with proper flex/grid structure
  - Added back button for mobile navigation
  - Added mobile-specific emoji and gift sharing buttons
  - Enhanced inbox with better avatar placeholders and responsive design
  - Added iOS Safari and touch-friendly optimizations
  - Added dark mode support
- Created superuser account (admin)
- Fixed CSRF_TRUSTED_ORIGINS configuration

## Deployment Notes
- Application uses Daphne ASGI server for WebSocket support
- WhiteNoise configured for static file serving
- Ready for PostgreSQL migration when needed
- Environment variables configured for Replit deployment
- Language: Ukrainian (LANGUAGE_CODE = 'uk')
- Timezone: Europe/Kyiv

## User Preferences
- Clean, maintainable code structure
- Ukrainian language interface
- Real-time features for enhanced user experience
