from flask import Flask, render_template, jsonify
import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Prism Central Configuration
PRISM_IP = "pc33.ntnxlab.local"
PRISM_USERNAME = "admin"
PRISM_PASSWORD = "Nutanix/4u!"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/vms')
def get_vms():
    url = f"https://{PRISM_IP}:9440/api/nutanix/v3/vms/list"
    payload = {
        "kind": "vm",
        "length": 1000  # get up to 1000 VMs
    }

    try:
        response = requests.post(
            url,
            auth=HTTPBasicAuth(PRISM_USERNAME, PRISM_PASSWORD),
            json=payload,
            verify=False
        )
        response.raise_for_status()
        vms_data = response.json()

        vms = []
        for vm in vms_data.get("entities", []):
            name = vm.get("status", {}).get("name")
            uuid = vm.get("metadata", {}).get("uuid")
            power_state = vm.get("status", {}).get("resources", {}).get("power_state")

            # Only show powered on VMs
            if power_state == "ON":
                console_url = f"https://ntnxlab.ddns.net/console/vnc_auto.html?path=proxy/{uuid}"
                vms.append({
                    "name": name,
                    "uuid": uuid,
                    "console_url": console_url
                })

        # Sort VMs alphabetically by name
        vms.sort(key=lambda x: x["name"].lower())

        return jsonify(vms)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
