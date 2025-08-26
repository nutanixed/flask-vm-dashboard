#!/usr/bin/env python3
"""
Simple monitoring script for the Flask VM Dashboard
"""

import requests
import time
import json
from datetime import datetime

def test_endpoints():
    """Test all endpoints and measure response times"""
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test health endpoint
    try:
        start_time = time.time()
        response = session.get(f"{base_url}/health")
        end_time = time.time()
        
        results["tests"]["health"] = {
            "status_code": response.status_code,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "success": response.status_code == 200
        }
    except Exception as e:
        results["tests"]["health"] = {
            "error": str(e),
            "success": False
        }
    
    # Test login
    try:
        start_time = time.time()
        login_data = {"username": "nutanix", "password": "nx2Tech151!"}
        response = session.post(f"{base_url}/login", data=login_data)
        end_time = time.time()
        
        results["tests"]["login"] = {
            "status_code": response.status_code,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "success": response.status_code == 200
        }
    except Exception as e:
        results["tests"]["login"] = {
            "error": str(e),
            "success": False
        }
    
    # Test VM API (only if login successful)
    if results["tests"]["login"]["success"]:
        try:
            start_time = time.time()
            response = session.get(f"{base_url}/api/vms")
            end_time = time.time()
            
            vm_count = 0
            if response.status_code == 200:
                try:
                    data = response.json()
                    vm_count = len(data)
                except:
                    pass
            
            results["tests"]["api_vms"] = {
                "status_code": response.status_code,
                "response_time_ms": round((end_time - start_time) * 1000, 2),
                "vm_count": vm_count,
                "success": response.status_code == 200
            }
        except Exception as e:
            results["tests"]["api_vms"] = {
                "error": str(e),
                "success": False
            }
    
    return results

def main():
    """Run monitoring tests"""
    print("Flask VM Dashboard - Health Check")
    print("=" * 40)
    
    results = test_endpoints()
    
    print(f"Timestamp: {results['timestamp']}")
    print()
    
    for test_name, test_result in results["tests"].items():
        status = "✅ PASS" if test_result.get("success") else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
        
        if "response_time_ms" in test_result:
            print(f"  Response Time: {test_result['response_time_ms']}ms")
        
        if "vm_count" in test_result:
            print(f"  VMs Found: {test_result['vm_count']}")
        
        if "error" in test_result:
            print(f"  Error: {test_result['error']}")
        
        print()
    
    # Overall status
    all_success = all(test.get("success", False) for test in results["tests"].values())
    overall_status = "✅ ALL SYSTEMS OPERATIONAL" if all_success else "❌ ISSUES DETECTED"
    print(f"Overall Status: {overall_status}")

if __name__ == "__main__":
    main()