# Real-Time Notification System

## Overview

This notification system provides real-time notifications to users via WebSocket connections. When a new user registers, all super admins automatically receive a notification in real-time.

## Features

- ✅ Real-time WebSocket notifications using Django Channels
- ✅ Automatic notifications to super admins when new users register
- ✅ Support for multiple notification types (INFO, SUCCESS, WARNING, ERROR, COURSE, ENROLLMENT, SESSION, LIBRARY, SYSTEM, USER_REGISTRATION)
- ✅ Notification metadata and action URLs
- ✅ Mark notifications as read/unread
- ✅ Filter notifications by type or read status

## Architecture

### Components

1. **Models** (`notifications/models.py`)
   - `Notification`: Stores notification data
   - `NotificationType`: Defines notification types
   - `NotificationStatus`: Tracks notification status (QUEUED, SENT, FAILED)
   - `NotificationChannels`: Defines delivery channels (IN_APP, EMAIL, PUSH, SMS)

2. **WebSocket Consumer** (`notifications/consumers.py`)
   - `NotificationConsumer`: Handles WebSocket connections for real-time notifications
   - Each user has their own notification channel: `notifications_{user_id}`

3. **Utility Functions** (`notifications/utils.py`)
   - `send_notification()`: Send notification to a single user
   - `send_notification_to_multiple_users()`: Send notification to multiple users

4. **Signals** (`accounts/signals.py`)
   - `notify_super_admins_on_new_user`: Automatically notifies super admins when a new user registers

## How It Works

### User Registration Flow

1. A new user registers via the API
2. Django's `post_save` signal is triggered for the `CustomUser` model
3. The `notify_super_admins_on_new_user` signal handler:
   - Fetches all super admin users
   - Creates a notification for each super admin
   - Sends the notification via WebSocket to each connected super admin

### WebSocket Connection

1. Client connects to `ws://your-domain/ws/notifications/`
2. Authentication is handled via JWT token in the WebSocket URL or headers
3. Client is added to their personal notification channel: `notifications_{user_id}`
4. When a notification is created, it's pushed to all connected clients in that channel

## API Endpoints

### List Notifications
```http
GET /api/notifications/
```

Query Parameters:
- `is_read`: Filter by read status (true/false)
- `type`: Filter by notification type

### Get Single Notification
```http
GET /api/notifications/{id}/
```

### Mark as Read
```http
POST /api/notifications/{id}/mark-as-read/
```

### Mark as Unread
```http
POST /api/notifications/{id}/mark-as-unread/
```

### Mark All as Read
```http
POST /api/notifications/mark-all-as-read/
```

### Get Unread Count
```http
GET /api/notifications/unread-count/
```

### Delete All Notifications
```http
DELETE /api/notifications/delete-all/
```

## WebSocket Usage

### Frontend Implementation Example

```javascript
// Connect to WebSocket
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

// Handle connection
ws.onopen = () => {
  console.log("Connected to notification service");
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'connection_established') {
    console.log("Connection established:", data.message);
  } else if (data.type === 'new_notification') {
    console.log("New notification received:", data.notification);
    // Display notification to user
    showNotification(data.notification);
  } else if (data.type === 'notification_updated') {
    console.log("Notification updated:", data);
    // Update notification UI
  }
};

// Send ping to keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000); // Every 30 seconds
```

## Notification Types

| Type | Description | Use Case |
|------|-------------|----------|
| INFO | General information | General updates |
| SUCCESS | Success messages | Successful operations |
| WARNING | Warning messages | Important alerts |
| ERROR | Error messages | Failed operations |
| COURSE | Course updates | Course-related notifications |
| ENROLLMENT | Enrollment updates | Student enrollment notifications |
| SESSION | Session updates | Live session notifications |
| LIBRARY | Library updates | Library resource notifications |
| SYSTEM | System notifications | System-wide announcements |
| USER_REGISTRATION | New user registration | When a new user registers |

## Creating Custom Notifications

### From Views or Code

```python
from notifications.utils import send_notification
from notifications.models import NotificationType

# Send to a single user
send_notification(
    user=user,
    title="Welcome!",
    body="Welcome to our platform!",
    notification_type=NotificationType.SUCCESS,
    action_url="/dashboard/",
    metadata={'welcome_bonus': 100}
)

# Send to multiple users
from notifications.utils import send_notification_to_multiple_users

send_notification_to_multiple_users(
    users=User.objects.filter(role='teacher'),
    title="New Course Available",
    body="A new course has been published!",
    notification_type=NotificationType.COURSE,
    action_url="/courses/123/"
)
```

### From Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.utils import send_notification
from notifications.models import NotificationType

@receiver(post_save, sender=YourModel)
def notify_on_model_save(sender, instance, created, **kwargs):
    if created:
        send_notification(
            user=instance.user,
            title="New Item Created",
            body=f"Your {instance.name} has been created!",
            notification_type=NotificationType.SUCCESS
        )
```

## Testing

### Manual Testing

1. **Create a Super Admin User**
   ```bash
   python manage.py createsuperuser
   ```

2. **Start Django Channels Server**
   ```bash
   python manage.py runserver
   # or with Daphne
   daphne -b 0.0.0.0 -p 8000 backend.asgi:application
   ```

3. **Connect to WebSocket** (as super admin)
   - Open browser console
   - Connect to `ws://localhost:8000/ws/notifications/`

4. **Register a New User**
   - Use the registration API endpoint
   - Super admin should receive a notification in real-time

### Expected Notification Format

```json
{
  "type": "new_notification",
  "notification": {
    "id": 1,
    "type": "user_registration",
    "title": "New User Registration",
    "body": "A new Student has registered: John Doe (john@example.com)",
    "action_url": "/admin/accounts/customuser/123/change/",
    "is_read": false,
    "time_ago": "Just now",
    "created_at": "2025-10-24T12:00:00Z"
  }
}
```

## Notification Metadata

The user registration notification includes the following metadata:

```json
{
  "user_id": 123,
  "user_email": "john@example.com",
  "user_full_name": "John Doe",
  "user_role": "student"
}
```

This metadata can be used to provide additional context or filtering on the frontend.

## Troubleshooting

### WebSocket Connection Fails
- Ensure Django Channels is properly configured in `settings.py`
- Check that Redis or your channel layer is running
- Verify JWT authentication is working

### Notifications Not Appearing
- Check if the WebSocket connection is active
- Verify the user is a super admin
- Check Django logs for errors
- Ensure the signal is registered in `accounts/apps.py`

### Multiple Notifications
- This is expected if you have multiple super admins
- Each super admin receives their own notification

## Configuration

### Settings Required

In `backend/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'channels',
    'notifications',
    'accounts',
]

ASGI_APPLICATION = 'backend.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### ASGI Configuration

In `backend/asgi.py`:

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi_app = get_asgi_application()

from notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

## Future Enhancements

- [ ] Email notifications for critical alerts
- [ ] SMS notifications
- [ ] Push notifications for mobile apps
- [ ] Notification preferences/settings per user
- [ ] Bulk notification management
- [ ] Notification templates
- [ ] Scheduled notifications
- [ ] Notification analytics

## License

This notification system is part of the Deen Bridge project.

