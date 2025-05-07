
# Flask VM Dashboard

A simple Flask-based web application that provides a dashboard for monitoring and managing virtual machines. This project includes SSL support via Nginx reverse proxy.

## Features

- Flask-based web dashboard for virtual machine management
- Reverse proxy using Nginx
- SSL encryption with Let's Encrypt or custom SSL certificates
- Basic HTTP authentication (optional)

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
├── .venv/                        # Virtual environment (gitignored)
├── certs/                        # SSL certificates (not included in repo)
├── templates/                    # HTML templates
│   └── index.html                # Main index page
├── static/                       # Static files (optional: CSS, JS, fonts, etc.)
├── flask_vm_dashboard.service    # Systemd service for running Flask app
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore file
└── README.md                     # Project overview and instructions
```

## Setup

1. **Install Dependencies**

First, install the Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

2. **Configure Nginx for Reverse Proxy**

Ensure that Nginx is set up to forward requests to your Flask app running on port 5000. Modify your Nginx configuration in `/etc/nginx/conf.d/flask_vm_dashboard.conf`.

Example configuration:

```
server {
    listen 80;
    server_name your_domain_or_ip;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain_or_ip;

    # SSL certificate paths
    ssl_certificate /opt/flask-vm-dashboard/certs/fullchain.pem;
    ssl_certificate_key /opt/flask-vm-dashboard/certs/privkey.pem;

    # Reverse proxy to Flask app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Start Flask Application**

To run the Flask app, you can use Gunicorn or the built-in Flask development server:

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

Alternatively, if you have a systemd service for Flask (e.g., `flask_vm_dashboard.service`), you can start it with:

```bash
sudo systemctl start flask_vm_dashboard
```

4. **Restart Nginx**

After configuring Nginx, restart it to apply the changes:

```bash
sudo systemctl restart nginx
```

5. **Access the Dashboard**

Navigate to your domain (or IP address) in a web browser. You should be able to access the Flask dashboard over HTTPS.

## Optional: Set Up Basic Authentication

If you'd like to enable basic authentication for your Flask app, you can configure `.htpasswd` files in Nginx and use it as follows:

```
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
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
