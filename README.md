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

### 1. Initial Django Setup & Configuration
- Installed Python 3.11 and all project dependencies
- (Django 5.1.6, Channels, Daphne, Pillow, WhiteNoise)
- Configured Django settings for Replit environment with proper ALLOWED_HOSTS and CSRF settings
- (CSRF_TRUSTED_ORIGINS configured for Replit proxy, USE_X_FORWARDED_HOST enabled)
- Users can access the application without proxy/CORS errors, application is production-ready for Replit hosting

---

### 2. Database & Migrations
- Ran all database migrations successfully and verified schema integrity
- (Django ORM with SQLite backend, all models created: User, Profile, Gift, Conversation, Message, Notification)
- Database is ready for user data, migrations can be easily replayed if needed
- Ready to migrate to PostgreSQL using Replit's built-in database

---

### 3. Real-time Chat & WebSocket Infrastructure
- Configured Daphne ASGI server for WebSocket support
- (Django Channels routing in asgi.py, ChatConsumer and NotificationConsumer implemented)
- Friends can chat in real-time with instant message delivery, notification system operational

---

### 4. Mobile Chat Responsiveness
- Added comprehensive CSS media queries for tablets, smartphones, and small devices
- (Chat input layout with proper flex/grid structure, mobile-specific emoji and gift sharing buttons)
- Users can chat comfortably on any device: desktop, tablet, or smartphone

---

### 5. Profile Avatar Management & Auto-Resizing
- Implemented automatic avatar resizing to 400×400 pixels on upload in Profile.save()
- (ImageField validation in models.py using Pillow, JPEG optimization with 85% quality)
- User avatars display consistently across the platform regardless of upload size, reducing storage and improving load times

---

### 6. JavaScript Error Fixes - IIFE Wrapper Pattern
- Fixed "redeclaration of const csrfToken" errors in friends.html, find_users.html, and view_profile.html
- (Wrapped all fetch() scripts in IIFE (Immediately Invoked Function Expression) to create local scope)
- Friend requests, user search, and profile pages no longer crash due to variable conflicts

---

### 7. Static Files & WhiteNoise Configuration
- Collected static files to staticfiles/ directory
- (WhiteNoise serving CSS, JavaScript, and assets efficiently for production)
- Static files served without extra latency, application is production-ready

---

### 8. Superuser Account Creation
- Created admin superuser account (username: admin)
- (Django admin interface accessible at /admin/)
- Platform administrators can manage users, moderate content, and access database records

---

### 9. Pending UI/UX Bug Fixes
- Avatar size constraint in navbar header (CSS max-width rules needed)
- (add max-width: 36px to navbar avatar styling)
- Avatars will display at fixed size instead of stretching based on image dimensions

---

### 10. Pending: Chat Text Color Contrast Fix
- Make username and input field text readable in chat interface
- (Add white/light text color styling to chat bubbles and input elements)
- Users with poor eyesight can read chat messages clearly

---

### 11. Pending: Notification Menu Population
- Display messages in notification dropdown that show in the badge counter
- (Sync JavaScript badge count with backend notification list via WebSocket)
- Users see actual notifications corresponding to the badge indicator

---

### 12. Pending: Mobile Chat Button Styling
- Remove odd circular shape from mobile chat buttons
- (Add media query rules to override border-radius for buttons on small screens)
- Mobile users have better-looking, properly-sized action buttons

---

### 13. Pending: Phantom Notification Badge Cleanup
- Clear the +1 notification indicator when no actual notifications exist
- (Add validation in notifications.js to only show badge if count > 0)
- Users won't see misleading notification indicators

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
