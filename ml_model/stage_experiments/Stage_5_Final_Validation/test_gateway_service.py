"""
QUICK TEST SCRIPT FOR MOBILE GATEWAY SERVICE
==============================================

Run this to test the gateway service with sample WBAN data.
Make sure gateway_flask_service.py is running in another terminal.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
SERVICE_URL = 'http://localhost:5000'
TIMEOUT = 5

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    try:
        response = requests.get(f"{SERVICE_URL}/api/health", timeout=TIMEOUT)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_single_detection():
    """Test single node detection"""
    print("\n" + "="*70)
    print("TEST 2: Single Node Detection")
    print("="*70)
    
    # Sample WBAN features (normal node)
    normal_features = [45.2, 78.5, 5.3, 12.1, 2.1, 0.05, 0.08, 0.02, 
                       0.0, 0.01, 0.05, 234.5, -65.2, 8.5, -70.1, -60.5, 145, 0, 35000]
    
    # Sample WBAN features (suspicious node)
    suspicious_features = [230.5, 450.2, 89.3, 156.1, 45.1, 0.45, 0.78, 0.52, 
                           0.05, 0.91, 0.85, 567.5, -85.2, 25.5, -95.1, -50.5, 892, 3, 45000]
    
    payload = {
        'node_id': 'sensor_01',
        'mac_address': '00:11:22:33:44:55',
        'features': normal_features
    }
    
    try:
        print(f"\nRequest: Single detection for {payload['node_id']}")
        response = requests.post(
            f"{SERVICE_URL}/api/detect",
            json=payload,
            timeout=TIMEOUT
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Prediction: {data.get('prediction')}")
        print(f"Confidence: {data.get('confidence'):.4f}")
        print(f"Sybil Probability: {data.get('sybil_probability'):.4f}")
        print(f"Inference Time: {data.get('inference_time_ms'):.3f} ms")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_batch_detection():
    """Test batch detection"""
    print("\n" + "="*70)
    print("TEST 3: Batch Detection (3 nodes)")
    print("="*70)
    
    # Sample features for 3 nodes
    nodes = [
        {
            'node_id': 'sensor_01',
            'features': [45.2, 78.5, 5.3, 12.1, 2.1, 0.05, 0.08, 0.02, 
                        0.0, 0.01, 0.05, 234.5, -65.2, 8.5, -70.1, -60.5, 145, 0, 35000]
        },
        {
            'node_id': 'sensor_02',
            'features': [230.5, 450.2, 89.3, 156.1, 45.1, 0.45, 0.78, 0.52, 
                        0.05, 0.91, 0.85, 567.5, -85.2, 25.5, -95.1, -50.5, 892, 3, 45000]
        },
        {
            'node_id': 'sensor_03',
            'features': [78.1, 125.3, 15.2, 34.5, 8.9, 0.12, 0.25, 0.08, 
                        0.02, 0.15, 0.18, 356.2, -72.1, 12.3, -78.5, -58.2, 289, 1, 37500]
        }
    ]
    
    payload = {'nodes': nodes}
    
    try:
        print(f"\nRequest: Batch detection for {len(nodes)} nodes")
        response = requests.post(
            f"{SERVICE_URL}/api/detect_batch",
            json=payload,
            timeout=TIMEOUT
        )
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total nodes: {data.get('total_nodes')}")
        print(f"Sybil nodes: {data.get('sybil_nodes')}")
        
        print("\nDetailed Results:")
        for result in data.get('results', []):
            print(f"  {result['node_id']}: {result['prediction']} (confidence: {result['confidence']:.4f})")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_network_status():
    """Test network status endpoint"""
    print("\n" + "="*70)
    print("TEST 4: Network Status")
    print("="*70)
    try:
        response = requests.get(f"{SERVICE_URL}/api/network_status", timeout=TIMEOUT)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total nodes detected: {data.get('total_nodes')}")
        print(f"Sybil nodes: {data.get('sybil_nodes')}")
        print(f"Normal nodes: {data.get('normal_nodes')}")
        print(f"Sybil percentage: {data.get('sybil_percentage'):.2f}%")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_statistics():
    """Test statistics endpoint"""
    print("\n" + "="*70)
    print("TEST 5: Service Statistics")
    print("="*70)
    try:
        response = requests.get(f"{SERVICE_URL}/api/statistics", timeout=TIMEOUT)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Predictions made: {data.get('predictions_made')}")
        print(f"Average inference time: {data.get('average_inference_time_ms'):.3f} ms")
        print(f"History size: {data.get('history_size')}/{data.get('max_history')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*70)
    print("TEST 6: Model Information")
    print("="*70)
    try:
        response = requests.get(f"{SERVICE_URL}/api/info", timeout=TIMEOUT)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Model type: {data.get('model_type')}")
        print(f"Number of features: {data.get('n_features')}")
        print(f"Service version: {data.get('service_version')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("GATEWAY SERVICE TEST SUITE")
    print("="*70)
    print(f"Service URL: {SERVICE_URL}")
    print(f"Test started: {datetime.now().isoformat()}")
    
    # Check connection
    print("\nConnecting to service...")
    try:
        requests.get(f"{SERVICE_URL}/api/health", timeout=TIMEOUT)
        print("✓ Connected to service")
    except:
        print("✗ Cannot connect to service")
        print(f"  Make sure gateway_flask_service.py is running on {SERVICE_URL}")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Single Detection", test_single_detection),
        ("Batch Detection", test_batch_detection),
        ("Network Status", test_network_status),
        ("Statistics", test_statistics),
        ("Model Info", test_model_info)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
