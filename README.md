
# Flask VM Dashboard

A simple Flask-based web application that provides a dashboard for monitoring and managing virtual machines. This project includes SSL support via Nginx reverse proxy.

## Recent Updates (v1.1.0)

The dashboard has been significantly improved with:

- Enhanced mobile responsiveness with card-style layout on small screens
- Modern UI with skeleton loading animations and toast notifications
- Improved error handling with retry mechanism for API requests
- Better accessibility with proper ARIA attributes and keyboard navigation
- See [CHANGELOG.md](CHANGELOG.md) for complete details

## Features

- Flask-based web dashboard for virtual machine management
- Responsive design with mobile-friendly interface
- Dark/light theme toggle
- Real-time VM status monitoring
- Toast notification system for user feedback
- Skeleton loading animations for better UX
- Search functionality for quick VM access
- Reverse proxy using Nginx
- SSL encryption with Let's Encrypt or custom SSL certificates
- Basic HTTP authentication (optional)
- Optimized caching and error handling
- Environment-based configuration
- Input validation and security enhancements

## Requirements

### Python Dependencies

Ensure that you have all the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### System Dependencies

- Python 3.7 or higher
- Nginx (for reverse proxy)
- Gunicorn (WSGI server)
- SSL certificates (for HTTPS)
- Firewall permissions for ports 80 (HTTP) and 443 (HTTPS)

## Project Structure

```
flask-vm-dashboard/
├── app.py                        # Flask application entry point
├── config.py                     # Configuration management
├── monitor.py                    # Monitoring utilities
├── start.sh                      # Development startup script
├── deploy.sh                     # Production deployment script
├── .env                          # Environment variables
├── .venv/                        # Virtual environment (gitignored)
├── certs/                        # SSL certificates directory
│   ├── fullchain.pem            # SSL certificate
│   └── privkey.pem              # SSL private key
├── templates/                    # HTML templates
│   ├── index.html               # Main dashboard page
│   ├── login.html               # Login page
│   ├── 404.html                 # 404 error page
│   └── 500.html                 # 500 error page
├── static/                       # Static files
│   ├── styles.css               # Main stylesheet
│   ├── app.js                   # JavaScript functionality
│   ├── favicon.svg              # Site favicon
│   └── nutanix_logo.png         # Logo image
├── etc/                          # Configuration templates
│   └── nginx/
│       └── conf.d/
│           └── flask_vm_dashboard.conf  # Nginx configuration template
├── flask_vm_dashboard.service    # Systemd service file
├── requirements.txt              # Python dependencies
├── DEPLOYMENT.md                 # Detailed deployment guide
├── CHANGELOG.md                  # Version history
├── .gitignore                    # Git ignore file
└── README.md                     # Project overview and instructions
```

### Repository Files for Complete Reproduction

This repository contains **ALL** necessary files to reproduce the application:

**Core Application:**
- `app.py` - Main Flask application
- `config.py` - Environment-based configuration
- `monitor.py` - Health monitoring utilities
- `.env` - Environment variables (configure for your setup)

**Web Assets:**
- `templates/` - All HTML templates
- `static/` - CSS, JavaScript, images, and favicon

**Deployment Configuration:**
- `flask_vm_dashboard.service` - Systemd service configuration
- `etc/nginx/conf.d/flask_vm_dashboard.conf` - Nginx reverse proxy configuration
- `certs/` - SSL certificate directory (add your certificates here)

**Automation Scripts:**
- `start.sh` - Development startup with validation
- `deploy.sh` - Complete production deployment automation

**Documentation:**
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `CHANGELOG.md` - Version history and updates
- `README.md` - This file

## Quick Deployment

For automated deployment, use the included deployment script:

```bash
# Clone the repository
git clone <your-repo-url> /opt/flask-vm-dashboard
cd /opt/flask-vm-dashboard

# Run automated deployment
chmod +x deploy.sh
./deploy.sh
```

This will automatically:
- Set up Python virtual environment
- Install all dependencies
- Configure systemd service
- Set up Nginx with SSL
- Start all services

For detailed manual setup instructions, see below.

## Manual Setup

1. **Install Dependencies**

First, install the Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

2. **Configure Nginx for Reverse Proxy**

Nginx can be used as a reverse proxy to serve your Flask application with improved performance, security, and SSL support. Follow these steps to configure Nginx:

### Install Nginx

If Nginx is not already installed, install it using your system's package manager:

**For Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install nginx
```

**For CentOS/RHEL:**
```bash
sudo yum install epel-release
sudo yum install nginx
```

### Create Nginx Configuration

**Option 1: Use the repository template (Recommended)**

Copy the included Nginx configuration from the repository:

```bash
sudo cp /opt/flask-vm-dashboard/etc/nginx/conf.d/flask_vm_dashboard.conf /etc/nginx/conf.d/
```

**Option 2: Create manually**

Create a new configuration file:

```bash
sudo nano /etc/nginx/conf.d/flask_vm_dashboard.conf
```

### Production SSL Configuration (Working Setup)

Use this configuration (included in the repository at `etc/nginx/conf.d/flask_vm_dashboard.conf`):

```nginx
server {
    listen 80;
    server_name ntnxlab.ddns.net;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ntnxlab.ddns.net;

    ssl_certificate /opt/flask-vm-dashboard/certs/fullchain.pem;
    ssl_certificate_key /opt/flask-vm-dashboard/certs/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Important:** Replace `ntnxlab.ddns.net` with your actual domain name or IP address.

### Setting Up HTTP Basic Authentication

To set up HTTP Basic Authentication:

1. **Install the htpasswd utility** (if not already installed):

   ```bash
   # For Debian/Ubuntu
   sudo apt install apache2-utils
   
   # For CentOS/RHEL
   sudo yum install httpd-tools
   ```

2. **Create a password file**:

   ```bash
   sudo htpasswd -c /etc/nginx/.htpasswd your_username
   ```

   You'll be prompted to enter a password. To add more users later (without the `-c` flag):

   ```bash
   sudo htpasswd /etc/nginx/.htpasswd another_user
   ```

3. **Set proper permissions**:

   ```bash
   sudo chmod 640 /etc/nginx/.htpasswd
   sudo chown nginx:nginx /etc/nginx/.htpasswd
   ```

### Enhanced SSL Configuration (Optional)

For improved security, you can enhance the SSL configuration:

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain_or_ip;

    access_log /var/log/nginx/flask_vm_dashboard_access.log;
    error_log /var/log/nginx/flask_vm_dashboard_error.log;

    # SSL certificate paths
    ssl_certificate /opt/flask-vm-dashboard/certs/fullchain.pem;
    ssl_certificate_key /opt/flask-vm-dashboard/certs/privkey.pem;

    # Enhanced SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # HSTS (optional, but recommended)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Basic Authentication
    auth_basic "Restricted Content";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # Reverse proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files directly through Nginx for better performance
    location /static/ {
        alias /opt/flask-vm-dashboard/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        
        # No authentication for static files (optional)
        auth_basic off;
    }
}
```

### Obtaining SSL Certificates

You can obtain SSL certificates in several ways:

1. **Let's Encrypt (Free):**
   ```bash
   sudo apt install certbot python3-certbot-nginx  # For Debian/Ubuntu
   # OR
   sudo yum install certbot python3-certbot-nginx  # For CentOS/RHEL
   
   sudo certbot --nginx -d your_domain.com
   ```

2. **Self-signed certificates (for testing):**
   ```bash
   sudo mkdir -p /opt/flask-vm-dashboard/certs
   sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /opt/flask-vm-dashboard/certs/privkey.pem \
     -out /opt/flask-vm-dashboard/certs/fullchain.pem
   ```

3. **Using existing certificates:**
   Copy your certificate files to `/opt/flask-vm-dashboard/certs/`:
   ```bash
   sudo cp /path/to/your/fullchain.pem /opt/flask-vm-dashboard/certs/
   sudo cp /path/to/your/privkey.pem /opt/flask-vm-dashboard/certs/
   ```

### Set Proper Permissions

Ensure Nginx can read the certificate files:

```bash
sudo chown -R root:root /opt/flask-vm-dashboard/certs
sudo chmod -R 644 /opt/flask-vm-dashboard/certs
sudo chmod 600 /opt/flask-vm-dashboard/certs/privkey.pem
```

3. **Set Up and Start Flask Application**

There are several ways to run your Flask application. The current setup uses a systemd service to run the Flask app directly with Python.

### Option 1: Run Flask Directly (Development Only)

You can run the Flask app directly for development purposes:

```bash
cd /opt/flask-vm-dashboard
source .venv/bin/activate
python app.py
```

This is useful for testing but not ideal for production.

### Option 2: Create a Systemd Service (Current Setup)

For a production setup, use a systemd service to manage your Flask application:

1. **Create a systemd service file:**

   The repository includes a sample service file (`flask_vm_dashboard.service`). Copy it to the systemd directory:

   ```bash
   sudo cp /opt/flask-vm-dashboard/flask_vm_dashboard.service /etc/systemd/system/
   sudo nano /etc/systemd/system/flask_vm_dashboard.service
   ```

   Here's what the service file contains:

   ```ini
   [Unit]
   Description=Flask VM Dashboard
   After=network.target

   [Service]
   User=nutanix
   Group=nutanix
   WorkingDirectory=/opt/flask-vm-dashboard
   Environment="PATH=/opt/flask-vm-dashboard/.venv/bin"
   ExecStart=/opt/flask-vm-dashboard/.venv/bin/python /opt/flask-vm-dashboard/app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Replace `nutanix` with your username and group if different.

2. **Enable and start the service:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable flask_vm_dashboard
   sudo systemctl start flask_vm_dashboard
   ```

3. **Check the service status:**

   ```bash
   sudo systemctl status flask_vm_dashboard
   ```

4. **View service logs:**

   ```bash
   sudo journalctl -u flask_vm_dashboard
   ```

### Option 3: Using Gunicorn (Alternative)

For better performance and resource management, you can use Gunicorn instead of the built-in Flask server:

1. **Install Gunicorn:**

   ```bash
   pip install gunicorn
   ```

2. **Modify the systemd service file:**

   ```bash
   sudo nano /etc/systemd/system/flask_vm_dashboard.service
   ```

   Update the ExecStart line:

   ```ini
   ExecStart=/opt/flask-vm-dashboard/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
   ```

3. **Reload and restart the service:**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart flask_vm_dashboard
   ```

### Option 4: Using Supervisor (Alternative)

If you prefer using Supervisor instead of systemd:

1. **Install Supervisor:**

   ```bash
   sudo apt install supervisor  # For Debian/Ubuntu
   # OR
   sudo yum install supervisor  # For CentOS/RHEL
   ```

2. **Create a configuration file:**

   ```bash
   sudo nano /etc/supervisor/conf.d/flask_vm_dashboard.conf
   ```

   Add the following content:

   ```ini
   [program:flask_vm_dashboard]
   directory=/opt/flask-vm-dashboard
   command=/opt/flask-vm-dashboard/.venv/bin/python /opt/flask-vm-dashboard/app.py
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/supervisor/flask_vm_dashboard.err.log
   stdout_logfile=/var/log/supervisor/flask_vm_dashboard.out.log
   user=nutanix
   ```

3. **Update Supervisor and start the application:**

   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start flask_vm_dashboard
   ```

4. **Test and Restart Nginx**

After configuring Nginx, test the configuration for syntax errors:

```bash
sudo nginx -t
```

If the test is successful, restart Nginx to apply the changes:

```bash
sudo systemctl restart nginx
```

You can check the status of Nginx to ensure it's running properly:

```bash
sudo systemctl status nginx
```

### Troubleshooting Nginx Configuration

If you encounter issues with your Nginx configuration:

1. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Check application-specific logs:**
   ```bash
   sudo tail -f /var/log/nginx/flask_vm_dashboard_error.log
   ```

3. **Verify that Nginx can connect to your Flask application:**
   ```bash
   # Make sure Flask is running
   curl http://127.0.0.1:5000
   
   # Check if Nginx is listening on the correct ports
   sudo ss -tulpn | grep nginx
   ```

4. **Common issues and solutions:**

   - **403 Forbidden errors:** Check file permissions for your application files
   - **502 Bad Gateway:** Ensure Flask is running and accessible on port 5000
   - **SSL certificate issues:** Verify certificate paths and permissions
   - **Connection refused:** Check if Flask is running and firewall settings

5. **SELinux considerations (for CentOS/RHEL):**

   If you're running SELinux in enforcing mode, you may need to allow Nginx to connect to the network:
   
   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

5. **Access the Dashboard**

Navigate to your domain (or IP address) in a web browser. You should be able to access the Flask dashboard over HTTPS.

## Managing HTTP Basic Authentication

The application is currently configured with HTTP Basic Authentication for security. Here's how to manage it:

### Adding or Changing Users

To add a new user or change an existing user's password:

```bash
# Add a new user
sudo htpasswd /etc/nginx/.htpasswd new_username

# Change password for existing user
sudo htpasswd /etc/nginx/.htpasswd existing_username
```

### Removing Users

To remove a user from the authentication file:

```bash
sudo htpasswd -D /etc/nginx/.htpasswd username_to_remove
```

### Disabling Authentication

If you want to temporarily disable authentication:

1. Edit the Nginx configuration:
   ```bash
   sudo nano /etc/nginx/conf.d/flask_vm_dashboard.conf
   ```

2. Comment out or remove the auth_basic lines:
   ```nginx
   location / {
       # auth_basic "Restricted Content";
       # auth_basic_user_file /etc/nginx/.htpasswd;
       
       proxy_pass http://127.0.0.1:5000;
       # ... other proxy settings ...
   }
   ```

3. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

## Backup and Restore

### Creating a Backup

To create a backup of your Flask VM Dashboard application, follow these steps:

1. **Create a backup directory**:
   ```bash
   mkdir -p ~/flask-vm-dashboard-backup
   ```

2. **Copy all files to the backup directory**:
   ```bash
   cp -r /opt/flask-vm-dashboard/* ~/flask-vm-dashboard-backup/
   ```

3. **Create a compressed archive** (optional but recommended):
   ```bash
   cd ~ && tar -czvf flask-vm-dashboard-backup.tar.gz flask-vm-dashboard-backup/
   ```

The backup will include:
- All Python code files (app.py)
- HTML templates (index.html, 404.html, 500.html)
- CSS files (styles.css)
- Static assets (images, etc.)
- SSL certificates in the certs directory
- Configuration files (flask_vm_dashboard.service)
- Requirements file (requirements.txt)
- Documentation (README.md)

### Restoring from Backup

To restore your application from a backup:

1. **If you have a compressed archive**:
   ```bash
   tar -xzvf ~/flask-vm-dashboard-backup.tar.gz
   ```

2. **Copy files back to the application directory**:
   ```bash
   # Stop the Flask service first
   sudo systemctl stop flask_vm_dashboard
   
   # Copy files (use sudo if necessary)
   sudo cp -r ~/flask-vm-dashboard-backup/* /opt/flask-vm-dashboard/
   
   # Fix permissions if needed
   sudo chown -R your_user:your_group /opt/flask-vm-dashboard/
   
   # Restart the Flask service
   sudo systemctl start flask_vm_dashboard
   ```

3. **Verify the application is working**:
   ```bash
   # Check service status
   sudo systemctl status flask_vm_dashboard
   
   # Check application logs
   sudo journalctl -u flask_vm_dashboard
   ```

## Troubleshooting

- If you encounter a `502 Bad Gateway`, ensure that Flask is running and listening on port 5000. Check your logs for errors.
- If Nginx isn't working properly, run `sudo nginx -t` to check for configuration errors.
- Disable SELinux enforcement
```bash
sudo setenforce 0
```
- To make this permanent, you would modify the SELinux configuration file at /etc/selinux/config and set:
```bash
SELINUX=permissive
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
