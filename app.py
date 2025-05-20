from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import os
import logging
from functools import lru_cache, wraps
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Print environment variables for testing
logger.info("Environment Variables:")
logger.info(f"PRISM_IP: {os.getenv('PRISM_IP')}")
logger.info(f"PRISM_USERNAME: {os.getenv('PRISM_USERNAME')}")
logger.info(f"API_TIMEOUT: {os.getenv('API_TIMEOUT')}")
logger.info(f"CLUSTER_CACHE_TTL: {os.getenv('CLUSTER_CACHE_TTL')}")

# Disable SSL warnings (for lab environments only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create Flask app, specify static folder path
app = Flask(__name__, static_folder='static')

# Set a secret key for session management
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    logger.warning("SECRET_KEY not found in environment variables, generating a random one")
    app.secret_key = secrets.token_hex(16)
    logger.warning("This will invalidate existing sessions when the server restarts")

# Set session timeout to 12 hours
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Dashboard login credentials - must be set in .env file
DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD')

# Validate that credentials are set
if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
    logger.error("DASHBOARD_USERNAME and DASHBOARD_PASSWORD must be set in .env file")
    raise ValueError("Missing dashboard credentials in environment variables")

# Prism Central Configuration from environment variables
PRISM_IP = os.getenv('PRISM_IP', 'pc33.ntnxlab.local')
PRISM_USERNAME = os.getenv('PRISM_USERNAME', 'admin')
PRISM_PASSWORD = os.getenv('PRISM_PASSWORD', 'Nutanix/4u!')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
CLUSTER_CACHE_TTL = int(os.getenv('CLUSTER_CACHE_TTL', '300'))  # 5 minutes default

# Cache for cluster info with TTL
cluster_cache = {
    'data': None,
    'timestamp': None
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_cache_valid():
    if not cluster_cache['timestamp']:
        return False
    return datetime.now() - cluster_cache['timestamp'] < timedelta(seconds=CLUSTER_CACHE_TTL)

def get_cluster_info():
    # Check cache first
    if is_cache_valid():
        logger.info("Returning cached cluster info")
        return cluster_cache['data']

    url = f"https://{PRISM_IP}:9440/api/nutanix/v3/clusters/list"
    payload = {
        "kind": "cluster",
        "length": 1000
    }
    
    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(PRISM_USERNAME, PRISM_PASSWORD),
            json=payload,
            verify=False,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        clusters_data = response.json()
        
        # Update cache
        if clusters_data.get("entities"):
            cluster_name = clusters_data["entities"][0].get("status", {}).get("name", "Unknown Cluster")
            cluster_cache['data'] = cluster_name
            cluster_cache['timestamp'] = datetime.now()
            return cluster_name
        return "Unknown Cluster"
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return "Unknown Cluster"
    except Exception as e:
        logger.error(f"Unexpected error getting cluster info: {str(e)}")
        return "Unknown Cluster"

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            session['logged_in'] = True
            session.permanent = True
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials. Please try again.'
            logger.warning(f"Failed login attempt from {request.remote_addr}")
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/health')
@limiter.exempt
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test Prism Central connection
        get_cluster_info()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/vms')
@login_required
@limiter.limit("30 per minute")
def get_vms():
    # Log request
    logger.info(f"VM list requested from {request.remote_addr}")
    
    url = f"https://{PRISM_IP}:9440/api/nutanix/v3/vms/list"
    payload = {
        "kind": "vm",
        "length": 1000
    }

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(PRISM_USERNAME, PRISM_PASSWORD),
            json=payload,
            verify=False,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        vms_data = response.json()

        # Get cluster name (now using cached version)
        cluster_name = get_cluster_info()

        vms = []
        for vm in vms_data.get("entities", []):
            try:
                status = vm.get("status", {})
                resources = status.get("resources", {})
                spec = resources.get("vm_features", {})
                
                name = status.get("name")
                uuid = vm.get("metadata", {}).get("uuid")
                power_state = resources.get("power_state")
                
                # Correct vCPU extraction (multiple possible fields)
                num_vcpus = (
                    resources.get("num_sockets", 0) * resources.get("num_cores_per_socket", 1) or
                    resources.get("num_vcpus", 0) or
                    spec.get("num_vcpus", 0)
                )
                
                # Memory handling (MiB to GB conversion)
                memory_mib = resources.get("memory_size_mib", 0)
                memory_gb = round(memory_mib / 1024, 2)  # 1024 MiB = 1 GB

                # Get IP addresses from nic_list
                ip_addresses = []
                for nic in resources.get("nic_list", []):
                    for ip_endpoint in nic.get("ip_endpoint_list", []):
                        if ip_endpoint.get("ip"):
                            ip_addresses.append(ip_endpoint["ip"])

                if power_state == "ON":
                    console_url = f"https://ntnxlab.ddns.net:8443/console/vnc_auto.html?path=proxy/{uuid}"
                    vms.append({
                        "name": name,
                        "uuid": uuid,
                        "vcpus": num_vcpus,
                        "memory_gb": memory_gb,
                        "console_url": console_url,
                        "ip_addresses": ip_addresses,
                        "cluster_name": cluster_name
                    })
            except Exception as e:
                logger.error(f"Error processing VM {vm.get('status', {}).get('name', 'Unknown')}: {str(e)}")
                continue

        vms.sort(key=lambda x: x["name"].lower())
        return jsonify(vms)

    except requests.exceptions.RequestException as e:
        logger.error(f"API connection failed: {str(e)}")
        return jsonify({"error": "Unable to connect to Prism Central API"}), 502
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
