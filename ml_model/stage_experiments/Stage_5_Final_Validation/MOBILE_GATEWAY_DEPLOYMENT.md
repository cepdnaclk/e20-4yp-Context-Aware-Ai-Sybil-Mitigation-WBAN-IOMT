# 📱 Mobile Gateway Sybil Detection Deployment Guide

## Overview

This guide shows how to deploy your trained Random Forest model on a mobile phone gateway (smartphone) to detect Sybil attacks in real-time.

---

## 🎯 Deployment Options

### Option 1: **Python Server on Mobile** (Easiest for Development)
- Run Python directly on Android/iOS using Kivy or Python for Android
- Suitable for: Testing, development, proof-of-concept
- Cost: Free
- Setup time: 1-2 hours

### Option 2: **Flask REST API Service** (Best for Integration)
- Run as background service on mobile
- Other apps communicate via HTTP requests
- Suitable for: Production, integration with other apps
- Cost: Free
- Setup time: 2-3 hours

### Option 3: **Native Mobile App** (Professional Deployment)
- Android/iOS native app with model embedded
- Best performance and battery efficiency
- Suitable for: Commercial deployment
- Cost: $500-2000 (development)
- Setup time: 1-2 weeks

### Option 4: **Edge Server** (Recommended)
- Deploy on Raspberry Pi or small Linux server on the network
- Process all WiFi traffic for the entire network
- Suitable for: Home/office networks
- Cost: $50-200 (hardware)
- Setup time: 1-2 hours

---

## 🚀 Quick Deployment (Option 2: Flask Server - Recommended)

### Step 1: Install Python on Mobile

**For Android (Using Termux):**
```bash
# Install Termux from Google Play Store
# Open Termux and run:
apt update
apt install python pip
pip install flask numpy scikit-learn pandas joblib
```

**For Linux Server (Raspberry Pi, etc.):**
```bash
sudo apt update
sudo apt install python3 python3-pip
sudo pip3 install flask numpy scikit-learn pandas
```

---

### Step 2: Create Deployment Package

Create file: `gateway_sybil_service.py`

```python
"""
WBAN Sybil Detection Gateway Service
=====================================
Runs on mobile phone/edge device as a background service
Provides REST API for real-time Sybil detection
"""

from flask import Flask, request, jsonify
import pickle
import numpy as np
import json
from datetime import datetime
import threading

# Create Flask app
app = Flask(__name__)

# Global detector instance
detector = None
detection_history = []
MAX_HISTORY = 1000

def load_detector():
    """Load trained model and preprocessing tools"""
    global detector
    try:
        # Load model from Stage 2
        with open('../Stage_2_Fast_Models/stage2_random_forest_model.pkl', 'rb') as f:
            model = pickle.load(f)
        
        # Load preprocessing tools from Stage 1
        with open('../Stage_1_Data_Prep/stage1_preprocessed_data.pkl', 'rb') as f:
            stage1_data = pickle.load(f)
            scaler = stage1_data['scaler']
            feature_names = stage1_data['X_columns']
        
        detector = {
            'model': model,
            'scaler': scaler,
            'features': feature_names,
            'loaded_at': datetime.now().isoformat()
        }
        print("✓ Model loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return False


@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if service is running"""
    return jsonify({
        'status': 'running',
        'model_loaded': detector is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/detect', methods=['POST'])
def detect_sybil():
    """
    Detect Sybil attack on a single node
    
    Request JSON:
    {
        "mac_address": "00:11:22:33:44:55",
        "node_id": "sensor_01",
        "features": [45.2, 78.5, 5.3, ..., 12.1]  # 19 features
    }
    
    Response:
    {
        "node_id": "sensor_01",
        "prediction": "SYBIL" or "NORMAL",
        "confidence": 0.9876,
        "sybil_probability": 0.9876,
        "timestamp": "2026-03-17T10:30:45.123Z",
        "inference_time_ms": 1.23
    }
    """
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.json
        mac_address = data.get('mac_address', 'unknown')
        node_id = data.get('node_id', mac_address)
        features = np.array(data.get('features', []), dtype=float)
        
        # Validate features
        if len(features) != len(detector['features']):
            return jsonify({
                'error': f'Expected {len(detector["features"])} features, got {len(features)}'
            }), 400
        
        # Scale features
        features_scaled = detector['scaler'].transform([features])
        
        # Make prediction
        import time
        start = time.time()
        prediction = detector['model'].predict(features_scaled)[0]
        probability = detector['model'].predict_proba(features_scaled)[0]
        inference_time = (time.time() - start) * 1000  # ms
        
        # Prepare response
        result = {
            'node_id': node_id,
            'mac_address': mac_address,
            'prediction': 'SYBIL' if prediction == 1 else 'NORMAL',
            'confidence': float(max(probability)),
            'sybil_probability': float(probability[1]),
            'normal_probability': float(probability[0]),
            'timestamp': datetime.now().isoformat(),
            'inference_time_ms': round(inference_time, 3)
        }
        
        # Store in history
        detection_history.append(result)
        if len(detection_history) > MAX_HISTORY:
            detection_history.pop(0)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/detect_batch', methods=['POST'])
def detect_batch():
    """
    Detect Sybil attack on multiple nodes (batch mode)
    
    Request JSON:
    {
        "nodes": [
            {
                "node_id": "sensor_01",
                "features": [45.2, 78.5, ...] 
            },
            ...
        ]
    }
    
    Response: Array of detection results
    """
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.json
        nodes = data.get('nodes', [])
        
        results = []
        for node in nodes:
            node_id = node.get('node_id', f'node_{len(results)}')
            features = np.array(node.get('features', []), dtype=float)
            
            if len(features) != len(detector['features']):
                continue
            
            # Scale and predict
            features_scaled = detector['scaler'].transform([features])
            prediction = detector['model'].predict(features_scaled)[0]
            probability = detector['model'].predict_proba(features_scaled)[0]
            
            result = {
                'node_id': node_id,
                'prediction': 'SYBIL' if prediction == 1 else 'NORMAL',
                'sybil_probability': float(probability[1])
            }
            results.append(result)
        
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/network_status', methods=['GET'])
def network_status():
    """Get network-wide Sybil detection statistics"""
    if not detection_history:
        return jsonify({'total': 0, 'sybil': 0, 'normal': 0, 'percentage': 0})
    
    sybil_count = sum(1 for d in detection_history if d['prediction'] == 'SYBIL')
    normal_count = len(detection_history) - sybil_count
    
    return jsonify({
        'total_nodes_detected': len(detection_history),
        'sybil_nodes': sybil_count,
        'normal_nodes': normal_count,
        'sybil_percentage': round(100 * sybil_count / len(detection_history), 2),
        'last_updated': datetime.now().isoformat()
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get detection history (last N detections)"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(detection_history[-limit:])


@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear detection history"""
    global detection_history
    detection_history = []
    return jsonify({'status': 'history cleared'})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("WBAN SYBIL DETECTION GATEWAY SERVICE")
    print("="*60)
    
    # Load model
    if not load_detector():
        print("Failed to load model. Exiting.")
        exit(1)
    
    print("\n📱 Starting Flask server...")
    print("   API endpoint: http://0.0.0.0:5000")
    print("   Test detection: POST /api/detect")
    print("   Network status: GET /api/network_status")
    print("\n" + "="*60)
    
    # Start server
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=False,
        threaded=True
    )
```

---

### Step 3: Run the Service

**On Terminal/Termux:**
```bash
# Make sure you're in the Stage_5 directory
cd stage_experiments/Stage_5_Final_Validation

# Run the service
python gateway_sybil_service.py
```

**You should see:**
```
============================================================
WBAN SYBIL DETECTION GATEWAY SERVICE
============================================================
✓ Model loaded successfully

📱 Starting Flask server...
   API endpoint: http://0.0.0.0:5000
   Test detection: POST /api/detect
   Network status: GET /api/network_status

============================================================
```

---

## 🔗 Using the Gateway Service

### Example 1: Test Detection (Single Node)

**Using curl:**
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "00:11:22:33:44:55",
    "node_id": "sensor_01",
    "features": [45.2, 78.5, 5.3, 12.1, 2.1, 0.05, 0.08, 0.02, 0.0, 0.01, 0.05, 234.5, -65.2, 8.5, -70.1, -60.5, 145, 0, 35000]
  }'
```

**Response:**
```json
{
  "node_id": "sensor_01",
  "mac_address": "00:11:22:33:44:55",
  "prediction": "NORMAL",
  "confidence": 0.9876,
  "sybil_probability": 0.0124,
  "timestamp": "2026-03-17T10:30:45.123Z",
  "inference_time_ms": 0.86
}
```

### Example 2: Batch Detection (Multiple Nodes)

```bash
curl -X POST http://localhost:5000/api/detect_batch \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {"node_id": "sensor_01", "features": [45.2, 78.5, ...]},
      {"node_id": "sensor_02", "features": [230.5, 45.2, ...]},
      {"node_id": "sensor_03", "features": [12.1, 5.3, ...]}
    ]
  }'
```

### Example 3: Check Network Status

```bash
curl http://localhost:5000/api/network_status
```

**Response:**
```json
{
  "total_nodes_detected": 150,
  "sybil_nodes": 8,
  "normal_nodes": 142,
  "sybil_percentage": 5.33,
  "last_updated": "2026-03-17T10:35:20.123Z"
}
```

---

## 📊 Option 4: Simple Standalone Script

If you just want to run detections from command line:

**File: `detect_from_csv.py`**

```python
"""
Simple script to detect Sybils from CSV file on mobile/gateway
"""
import pandas as pd
import pickle
import numpy as np
from pathlib import Path

# Load model
print("Loading model...")
model = pickle.load(open('../Stage_2_Fast_Models/stage2_random_forest_model.pkl', 'rb'))
stage1_data = pickle.load(open('../Stage_1_Data_Prep/stage1_preprocessed_data.pkl', 'rb'))
scaler = stage1_data['scaler']
features = stage1_data['X_columns']

# Load test data
print("Loading test data...")
df = pd.read_csv('your_wban_data.csv')

# Get features
X = df[features].fillna(0)
X_scaled = scaler.transform(X)

# Predict
print("Running detection...")
predictions = model.predict(X_scaled)
probabilities = model.predict_proba(X_scaled)

# Show results
df['Prediction'] = ['SYBIL' if p == 1 else 'NORMAL' for p in predictions]
df['Sybil_Prob'] = probabilities[:, 1]

print("\n" + "="*70)
print("SYBIL DETECTION RESULTS")
print("="*70)
print(df[['node_id', 'Prediction', 'Sybil_Prob']].to_string(index=False))

# Summary
sybil_count = (predictions == 1).sum()
print(f"\n✓ Total nodes: {len(df)}")
print(f"✗ Sybil nodes: {sybil_count} ({100*sybil_count/len(df):.1f}%)")
print(f"✓ Normal nodes: {len(df)-sybil_count} ({100*(len(df)-sybil_count)/len(df):.1f}%)")

# Save results
df.to_csv('sybil_detection_results.csv', index=False)
print(f"\n✓ Results saved to: sybil_detection_results.csv")
```

**Run it:**
```bash
python detect_from_csv.py
```

---

## ⚙️ System Requirements

### Minimum (Mobile Phone):
- **OS**: Android 6+ or iOS 12+
- **RAM**: 512 MB
- **Storage**: 50 MB
- **CPU**: Any modern mobile processor
- **Network**: WiFi adapter for packet capture

### Recommended (Better Performance):
- **RAM**: 2+ GB
- **Storage**: 100 MB
- **CPU**: Quad-core or better

### For Raspberry Pi Gateway:
- **Model**: Raspberry Pi 4B or higher
- **RAM**: 2-4 GB
- **Storage**: microSD 32+ GB
- **Power**: USB-C 3A
- **Network**: Ethernet or WiFi

---

## 🔐 Security Considerations

1. **Model Protection**: Keep your model file private
2. **API Security**: Add authentication if deploying on network
3. **Data Privacy**: Don't log sensitive node IDs
4. **Updates**: Regularly update with new training data

**Add Authentication (Optional):**
```python
from flask import request
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != 'your_secret_key':
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/detect', methods=['POST'])
@require_api_key
def detect_sybil():
    # ... your code
```

---

## 📊 Monitoring on Mobile

Create dashboard: `monitor_dashboard.py`

```python
"""
Simple web dashboard for monitoring Sybil detections
Access at: http://localhost:8000
"""
from flask import Flask, render_template_string
import requests
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WBAN Sybil Detection Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; margin: 20px; }
        .stat { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; }
        .sybil { color: red; font-weight: bold; }
        .normal { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🛡️ WBAN Sybil Detection Dashboard</h1>
    <div id="status"></div>
    <script>
        fetch('http://localhost:5000/api/network_status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = `
                    <div class="stat">Total Nodes: ${data.total_nodes_detected}</div>
                    <div class="stat">
                        <span class="normal">Normal: ${data.normal_nodes}</span>
                    </div>
                    <div class="stat">
                        <span class="sybil">Sybil: ${data.sybil_nodes}</span>
                    </div>
                    <div class="stat">
                        <span class="sybil">Sybil %: ${data.sybil_percentage}%</span>
                    </div>
                `;
            });
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
```

---

## 📝 Deployment Checklist

- [ ] Model file copied to mobile/gateway device
- [ ] Python and dependencies installed
- [ ] Test API endpoint with curl
- [ ] Configure auto-start on device boot
- [ ] Set up logging/monitoring
- [ ] Test with real WBAN data
- [ ] Document API endpoints for integration
- [ ] Set up alerts for Sybil detections
- [ ] Monitor performance (CPU, memory, latency)
- [ ] Plan for model updates

---

## ❓ Troubleshooting

### "Module not found" Error
```bash
pip install flask numpy scikit-learn
```

### Model file not found
```bash
# Make sure file is in correct path:
ls -la ../Stage_2_Fast_Models/stage2_random_forest_model.pkl
```

### Port already in use
```bash
# Use different port:
app.run(port=5001)  # Or any available port
```

### Performance issues (slow inference)
- Reduce batch size
- Upgrade device RAM
- Consider edge server (Raspberry Pi)

---

## 🎓 Next Steps

1. **Test on localhost**: Run the Flask server locally
2. **Test on mobile**: Transfer to actual mobile device
3. **Integrate network capture**: Add WiFi packet capture
4. **Set up alerts**: Configure email/SMS for Sybil detection
5. **Production deployment**: Deploy to actual network

**Ready to deploy!** Choose your option and follow the steps above. 🚀
