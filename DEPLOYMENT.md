# Deen Bridge Backend - Production Deployment Guide

This guide covers deploying the Deen Bridge backend in a production environment.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Configuration](#application-configuration)
5. [Deployment Options](#deployment-options)
6. [Post-Deployment](#post-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.10 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher
- Nginx (recommended for static files and reverse proxy)
- Linux server (Ubuntu 20.04+ recommended)

### Required Packages
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx
```

## Environment Setup

### 1. Create a Virtual Environment
```bash
cd /path/to/project/backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create Environment File
```bash
cp env.example .env
```

Edit `.env` with production values:
```bash
nano .env
```

### Important Environment Variables

#### Security (CRITICAL)
```bash
# Generate a new secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
```

#### Database
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/deenbridge
```

#### Redis
```bash
REDIS_URL=redis://127.0.0.1:6379/0
```

#### CORS
```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Database Setup

### 1. Create PostgreSQL Database
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE deenbridge;
CREATE USER deenbridge_user WITH PASSWORD 'your_secure_password';
ALTER ROLE deenbridge_user SET client_encoding TO 'utf8';
ALTER ROLE deenbridge_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE deenbridge_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE deenbridge TO deenbridge_user;
\q
```

### 2. Run Migrations
```bash
export DJANGO_SETTINGS_MODULE=backend.settings.production
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

## Application Configuration

### 1. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 2. Test Configuration
```bash
python manage.py check --deploy
```

## Deployment Options

### Option 1: Systemd Service (Recommended)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/deenbridge.service
```

Add the following content:

```ini
[Unit]
Description=Deen Bridge Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/project/backend
Environment="PATH=/path/to/project/backend/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=backend.settings.production"
ExecStart=/path/to/project/backend/venv/bin/gunicorn -c gunicorn_config.py backend.asgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable deenbridge
sudo systemctl start deenbridge
sudo systemctl status deenbridge
```

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings.production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn_config.py", "backend.asgi:application"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=deenbridge
      - POSTGRES_USER=deenbridge_user
      - POSTGRES_PASSWORD=your_secure_password

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  backend:
    build: .
    command: gunicorn -c gunicorn_config.py backend.asgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Nginx Configuration

Create `/etc/nginx/sites-available/deenbridge`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    client_max_body_size 100M;

    location /static/ {
        alias /path/to/project/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/project/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /health/ {
        proxy_pass http://backend;
        access_log off;
    }

    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/deenbridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Post-Deployment

### 1. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 2. Verify Deployment
```bash
# Check health endpoint
curl https://yourdomain.com/health/

# Check API root
curl https://yourdomain.com/
```

### 3. Setup Automated Backups

Create backup script `/usr/local/bin/backup-deenbridge.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/deenbridge"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U deenbridge_user deenbridge > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /path/to/project/backend/media/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-deenbridge.sh
```

## Monitoring & Maintenance

### Logs
```bash
# Application logs
tail -f /path/to/project/backend/logs/django.log

# Systemd logs
sudo journalctl -u deenbridge -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring

Install monitoring tools:
```bash
pip install django-prometheus
```

Add to settings:
```python
INSTALLED_APPS += ['django_prometheus']
```

### Health Checks

Monitor the health endpoint:
```bash
curl https://yourdomain.com/health/
```

Set up uptime monitoring with services like:
- UptimeRobot
- Pingdom
- StatusCake

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u deenbridge -n 50

# Check configuration
python manage.py check --deploy
```

### Database Connection Issues
```bash
# Test database connection
psql -U deenbridge_user -d deenbridge -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R www-data:www-data /path/to/project/backend
sudo chmod -R 755 /path/to/project/backend
```

### Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check Nginx configuration
sudo nginx -t
```

## Security Checklist

- [ ] SECRET_KEY is randomly generated and kept secret
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS is properly configured
- [ ] SSL/TLS certificate is installed and valid
- [ ] Database credentials are secure
- [ ] Firewall is configured (only ports 80, 443 open)
- [ ] Regular backups are automated
- [ ] Monitoring and alerting is set up
- [ ] Error tracking (Sentry) is configured
- [ ] Rate limiting is enabled
- [ ] CORS is properly configured
- [ ] Security headers are set

## Useful Commands

```bash
# Restart service
sudo systemctl restart deenbridge

# View logs
sudo journalctl -u deenbridge -f

# Run management commands
python manage.py <command>

# Update application
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart deenbridge
```

## Support

For issues and questions:
- Documentation: [Link to docs]
- GitHub Issues: [Link to repo]
- Email: support@yourdomain.com

