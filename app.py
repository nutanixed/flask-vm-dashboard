from flask import Flask, render_template, jsonify
import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL warnings (for lab environments only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create Flask app, specify static folder path
app = Flask(__name__, static_folder='static')

# Prism Central Configuration
PRISM_IP = "pc33.ntnxlab.local"
PRISM_USERNAME = "admin"
PRISM_PASSWORD = "Nutanix/4u!"

def get_cluster_info():
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
            timeout=30
        )
        response.raise_for_status()
        clusters_data = response.json()
        
        # Return the first cluster's name (since we know it's CLUS13)
        if clusters_data.get("entities"):
            return clusters_data["entities"][0].get("status", {}).get("name", "Unknown Cluster")
        return "Unknown Cluster"
    except Exception as e:
        print(f"Error getting cluster info: {str(e)}")
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
            timeout=30
        )
        response.raise_for_status()
        vms_data = response.json()

        # Get cluster name once
        cluster_name = get_cluster_info()

        vms = []
        for vm in vms_data.get("entities", []):
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

        vms.sort(key=lambda x: x["name"].lower())
        return jsonify(vms)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API connection failed: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
