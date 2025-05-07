from flask import Flask, render_template, jsonify
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import os
import logging
from functools import lru_cache
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/vms')
def get_vms():
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
