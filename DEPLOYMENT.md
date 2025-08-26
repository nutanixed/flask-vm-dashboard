# Deployment Guide

## Quick Deployment

### 1. Using the startup script (Recommended)
```bash
chmod +x start.sh
./start.sh
```

### 2. Manual deployment
```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the application
python3 app.py
```

## Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install Gunicorn
pip install gunicorn

# Start with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### Using systemd service
Create `/etc/systemd/system/flask-vm-dashboard.service`:
```ini
[Unit]
Description=Flask VM Dashboard
After=network.target

[Service]
Type=simple
User=nutanix
WorkingDirectory=/opt/flask-vm-dashboard
Environment=PATH=/opt/flask-vm-dashboard/.venv/bin
ExecStart=/opt/flask-vm-dashboard/.venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-vm-dashboard
sudo systemctl start flask-vm-dashboard
```

## Environment Variables

Required:
- `DASHBOARD_USERNAME` - Dashboard login username
- `DASHBOARD_PASSWORD` - Dashboard login password
- `PRISM_IP` - Prism Central IP/hostname
- `PRISM_USERNAME` - Prism Central username
- `PRISM_PASSWORD` - Prism Central password
- `SECRET_KEY` - Flask secret key

Optional:
- `API_TIMEOUT=30` - API request timeout in seconds
- `CLUSTER_CACHE_TTL=300` - Cluster info cache TTL in seconds
- `CONSOLE_BASE_URL` - Base URL for console access
- `SESSION_TIMEOUT_HOURS=12` - Session timeout in hours

## Performance Optimizations Applied

1. **Caching**: Cluster information is cached for 5 minutes by default
2. **Rate Limiting**: API endpoints are rate-limited to prevent abuse
3. **Error Handling**: Comprehensive error handling with user-friendly messages
4. **Input Validation**: All user inputs are validated and sanitized
5. **Browser Cache Control**: API responses include cache-control headers
6. **Retry Logic**: Frontend includes retry logic for failed requests
7. **Loading States**: Skeleton loading animations for better UX

## Security Features

1. **Session Management**: Secure session handling with configurable timeout
2. **Rate Limiting**: Protection against brute force attacks
3. **Input Validation**: XSS and injection protection
4. **HTTPS Ready**: Production configuration includes secure cookie settings
5. **Error Logging**: Failed login attempts are logged

## Monitoring

The application includes a `/health` endpoint for monitoring:
```bash
curl http://localhost:5000/health
```

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure virtual environment is activated
2. **Permission denied**: Check file permissions and user ownership
3. **Connection refused**: Verify Prism Central connectivity
4. **Browser cache issues**: Clear browser cache and cookies

### Logs

Application logs are written to stdout. In production, redirect to a file:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app > app.log 2>&1
```