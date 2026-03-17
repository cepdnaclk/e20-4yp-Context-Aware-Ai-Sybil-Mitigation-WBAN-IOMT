"""
WBAN SYBIL DETECTION - SIMPLE MOBILE GATEWAY SERVICE
=====================================================

A lightweight Flask-based service for real-time Sybil detection on mobile gateways.
Copy this file to your mobile device/gateway and run: python gateway_sybil_service.py

Provides REST API endpoints for:
- Single node detection
- Batch node detection  
- Network-wide statistics
"""

from flask import Flask, request, jsonify
import pickle
import numpy as np
from datetime import datetime
import time
import os

# Create Flask app
app = Flask(__name__)

# Global state
detector = None
detection_history = []
MAX_HISTORY = 1000
MODEL_PATH = '../Stage_2_Fast_Models/stage2_random_forest_model.pkl'
SCALER_PATH = '../Stage_1_Data_Prep/stage1_preprocessed_data.pkl'


def load_detector():
    """Load trained model and preprocessing tools"""
    global detector
    try:
        print("Loading model...")
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        print(f"  ✓ Model loaded: {type(model).__name__}")
        
        print("Loading preprocessing tools...")
        with open(SCALER_PATH, 'rb') as f:
            stage1_data = pickle.load(f)
            scaler = stage1_data['scaler']
            feature_names = stage1_data['X_columns']
        print(f"  ✓ Scaler loaded")
        print(f"  ✓ Features: {len(feature_names)}")
        
        detector = {
            'model': model,
            'scaler': scaler,
            'features': feature_names,
            'loaded_at': datetime.now().isoformat(),
            'predictions_made': 0,
            'total_inference_time_ms': 0.0
        }
        return True
    except FileNotFoundError as e:
        print(f"  ✗ File not found: {e}")
        print(f"    Make sure model paths are correct:")
        print(f"    Model: {MODEL_PATH}")
        print(f"    Scaler: {SCALER_PATH}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'WBAN Sybil Detection Gateway',
        'model_loaded': detector is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/detect', methods=['POST'])
def detect_sybil():
    """
    Detect Sybil attack on a single node
    
    Request:
    {
        "node_id": "sensor_01",
        "mac_address": "00:11:22:33:44:55",
        "features": [45.2, 78.5, 5.3, ..., 12.1]  # 19 features
    }
    
    Response:
    {
        "success": true,
        "node_id": "sensor_01",
        "prediction": "NORMAL" or "SYBIL",
        "confidence": 0.9876,
        "sybil_probability": 0.0124,
        "inference_time_ms": 0.86,
        "timestamp": "2026-03-17T10:30:45.123Z"
    }
    """
    if detector is None:
        return jsonify({
            'success': False,
            'error': 'Model not loaded'
        }), 500
    
    try:
        data = request.json
        node_id = data.get('node_id', f'node_{len(detection_history)}')
        mac_address = data.get('mac_address', 'unknown')
        features = np.array(data.get('features', []), dtype=float)
        
        # Validate features
        if len(features) != len(detector['features']):
            return jsonify({
                'success': False,
                'error': f'Expected {len(detector["features"])} features, got {len(features)}'
            }), 400
        
        # Make prediction
        start_time = time.time()
        features_scaled = detector['scaler'].transform([features])
        prediction = detector['model'].predict(features_scaled)[0]
        probabilities = detector['model'].predict_proba(features_scaled)[0]
        inference_time_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        detector['predictions_made'] += 1
        detector['total_inference_time_ms'] += inference_time_ms
        
        # Prepare response
        result = {
            'success': True,
            'node_id': node_id,
            'mac_address': mac_address,
            'prediction': 'SYBIL' if prediction == 1 else 'NORMAL',
            'confidence': float(max(probabilities)),
            'normal_probability': float(probabilities[0]),
            'sybil_probability': float(probabilities[1]),
            'inference_time_ms': round(inference_time_ms, 3),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        detection_history.append(result)
        if len(detection_history) > MAX_HISTORY:
            detection_history.pop(0)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/detect_batch', methods=['POST'])
def detect_batch():
    """
    Batch detection for multiple nodes
    
    Request:
    {
        "nodes": [
            {"node_id": "sensor_01", "features": [45.2, 78.5, ...]},
            {"node_id": "sensor_02", "features": [230.5, 45.2, ...]},
            ...
        ]
    }
    """
    if detector is None:
        return jsonify({
            'success': False,
            'error': 'Model not loaded'
        }), 500
    
    try:
        data = request.json
        nodes = data.get('nodes', [])
        results = []
        
        for i, node in enumerate(nodes):
            try:
                node_id = node.get('node_id', f'node_{i}')
                features = np.array(node.get('features', []), dtype=float)
                
                if len(features) != len(detector['features']):
                    continue
                
                # Predict
                features_scaled = detector['scaler'].transform([features])
                prediction = detector['model'].predict(features_scaled)[0]
                probabilities = detector['model'].predict_proba(features_scaled)[0]
                
                result = {
                    'node_id': node_id,
                    'prediction': 'SYBIL' if prediction == 1 else 'NORMAL',
                    'sybil_probability': round(float(probabilities[1]), 4),
                    'confidence': round(float(max(probabilities)), 4)
                }
                results.append(result)
            except:
                continue
        
        return jsonify({
            'success': True,
            'total_nodes': len(results),
            'sybil_nodes': sum(1 for r in results if r['prediction'] == 'SYBIL'),
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/network_status', methods=['GET'])
def network_status():
    """Get network-wide Sybil statistics"""
    if not detection_history:
        return jsonify({
            'total_nodes': 0,
            'sybil_nodes': 0,
            'normal_nodes': 0,
            'sybil_percentage': 0,
            'last_updated': datetime.now().isoformat()
        })
    
    sybil_count = sum(1 for d in detection_history if d.get('prediction') == 'SYBIL')
    normal_count = len(detection_history) - sybil_count
    
    return jsonify({
        'total_nodes': len(detection_history),
        'sybil_nodes': sybil_count,
        'normal_nodes': normal_count,
        'sybil_percentage': round(100 * sybil_count / len(detection_history), 2),
        'last_updated': datetime.now().isoformat()
    })


@app.route('/api/statistics', methods=['GET'])
def statistics():
    """Get service performance statistics"""
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    predictions = detector['predictions_made']
    avg_time = detector['total_inference_time_ms'] / predictions if predictions > 0 else 0
    
    return jsonify({
        'predictions_made': predictions,
        'total_inference_time_ms': round(detector['total_inference_time_ms'], 2),
        'average_inference_time_ms': round(avg_time, 3),
        'model_loaded_at': detector['loaded_at'],
        'history_size': len(detection_history),
        'max_history': MAX_HISTORY
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent detection history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'total': len(detection_history),
        'returned': min(limit, len(detection_history)),
        'history': detection_history[-limit:]
    })


@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear detection history"""
    global detection_history
    old_size = len(detection_history)
    detection_history = []
    return jsonify({
        'success': True,
        'cleared': old_size
    })


@app.route('/api/info', methods=['GET'])
def model_info():
    """Get model and service information"""
    if detector is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    return jsonify({
        'model_type': type(detector['model']).__name__,
        'n_features': len(detector['features']),
        'feature_names': detector['features'],
        'loaded_at': detector['loaded_at'],
        'service_version': '1.0.0',
        'endpoints': {
            'health': 'GET /api/health',
            'detect': 'POST /api/detect',
            'batch': 'POST /api/detect_batch',
            'status': 'GET /api/network_status',
            'stats': 'GET /api/statistics',
            'history': 'GET /api/history',
            'info': 'GET /api/info'
        }
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'info': 'GET /api/info for available endpoints'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("WBAN SYBIL DETECTION GATEWAY SERVICE")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Load model
    print("\n[INITIALIZATION]")
    if not load_detector():
        print("\n✗ Failed to load model. Exiting.")
        exit(1)
    
    print("\n[SERVICE INFO]")
    print(f"  Listening on: http://0.0.0.0:5000")
    print(f"  Features: {len(detector['features'])}")
    print(f"  History limit: {MAX_HISTORY} detections")
    
    print("\n[ENDPOINTS]")
    print(f"  Health check: GET /api/health")
    print(f"  Single detection: POST /api/detect")
    print(f"  Batch detection: POST /api/detect_batch")
    print(f"  Network status: GET /api/network_status")
    print(f"  Statistics: GET /api/statistics")
    print(f"  Model info: GET /api/info")
    
    print("\n[READY]")
    print(f"  Type: Ctrl+C to stop")
    print("\n" + "="*70 + "\n")
    
    # Start server
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n\n✓ Service stopped")
        print(f"Total predictions: {detector['predictions_made']}")
