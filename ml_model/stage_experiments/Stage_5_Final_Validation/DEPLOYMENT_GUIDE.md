# SYBIL DETECTION - MOBILE GATEWAY DEPLOYMENT GUIDE

## Overview

This guide provides step-by-step instructions for deploying the Sybil detection model on mobile gateways (Android/iOS) and edge devices (ESP32, Raspberry Pi).

## Quick Start

### 1. Load the Model

```python
import pickle
from sybil_detector_deployment import SybilDetectorDeployment

# Load deployment package
detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
print(detector.get_statistics())
```

### 2. Make Predictions

```python
import numpy as np

# Single sample detection
raw_features = np.array([45.2, 78.5, 5.3, 12.1, 2.1, ...])  # 19 features
result = detector.detect(raw_features)

print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Decision Reason: {result['decision_reason']}")
print(f"Latency: {result['inference_time_ms']:.2f} ms")

# Batch detection
features_batch = np.array([[...], [...], ...])  # (N, 19)
results = detector.detect_batch(features_batch)
```

### 3. Network Monitoring

```python
from sybil_detector_deployment import NetworkMonitor

monitor = NetworkMonitor(detector)

# As detections come in
for node_id, features in incoming_data:
    result = detector.detect(features)
    monitor.add_node_detection(node_id, result)

# Get network status
network_summary = monitor.get_network_summary()
print(f"Network Status: {network_summary['network_status']}")
print(f"Compromised: {network_summary['compromised_percentage']:.1f}%")
```

---

## Feature Requirements

The model requires **19 features** in this order:

| # | Feature Name | Type | Unit | Typical Range |
|---|---|---|---|---|
| 1 | window_start_s | float | seconds | 0-300000 |
| 2 | window_end_s | float | seconds | 5-300004 |
| 3 | pps | float | packets/sec | 0-115 |
| 4 | iat_mean | float | ms | -1-2630 |
| 5 | iat_std | float | ms | -1-1200 |
| 6 | seq_gap_mean | float | ms | -1-29509 |
| 7 | seq_gap_max | float | ms | -1-179981 |
| 8 | seq_reset_rate | float | 0-1 | 0-1 |
| 9 | dup_seq_rate | float | 0-1 | 0-0.06 |
| 10 | out_of_order_rate | float | 0-1 | 0-0.08 |
| 11 | boot_change_rate | float | 0-1 | 0-1 |
| 12 | udp_pkt_count | float | count | 0-575 |
| 13 | rssi_mean | float | dBm | -100 to -20 |
| 14 | rssi_std | float | dBm | 0-25 |
| 15 | rssi_min | float | dBm | -100 to -21 |
| 16 | rssi_max | float | dBm | -100 to -17 |
| 17 | rssi_frame_count | float | count | 0-2784 |
| 18 | rssi_missing | float | count | 0-4 |
| 19 | boot_id | float | id | 34483-45241 |

### Feature Extraction from Raw Data

**From Packet Capture:**
```python
def extract_features(packets, time_window_ms=5000):
    """
    Extract features from captured WiFi packets
    
    Args:
        packets: List of packet objects with fields:
                 - timestamp_ms: Packet timestamp
                 - src_mac: Source MAC address
                 - dst_mac: Destination MAC address
                 - pkt_size: Packet size in bytes
                 - ip_protocol: IP protocol (UDP=17)
                 - seq_num: Sequence number
                 - rssi: Signal strength in dBm
                 - boot_id: Node boot counter
    """
    
    # Calculate time windows
    start_time = packets[0].timestamp_ms
    end_time = start_time + time_window_ms
    window_packets = [p for p in packets if start_time <= p.timestamp_ms <= end_time]
    
    # Basic stats
    pps = len(window_packets) / (time_window_ms / 1000)
    
    # Inter-arrival times
    if len(window_packets) > 1:
        timestamps = [p.timestamp_ms for p in window_packets]
        iats = np.diff(timestamps)
        iat_mean = np.mean(iats) if len(iats) > 0 else -1
        iat_std = np.std(iats) if len(iats) > 0 else -1
    else:
        iat_mean = iat_std = -1
    
    # Sequence gaps
    seq_nums = [p.seq_num for p in window_packets if hasattr(p, 'seq_num')]
    if len(seq_nums) > 1:
        seq_gaps = np.diff(seq_nums)
        seq_gap_mean = np.mean(seq_gaps) if len(seq_gaps) > 0 else -1
        seq_gap_max = np.max(seq_gaps) if len(seq_gaps) > 0 else -1
    else:
        seq_gap_mean = seq_gap_max = -1
    
    # Reset rate (sequence number jumps)
    resets = sum(1 for gap in seq_gaps if gap < 0) if len(seq_gaps) > 0 else 0
    seq_reset_rate = resets / len(seq_gaps) if len(seq_gaps) > 0 else 0
    
    # Duplicate & out-of-order
    dup_seq_rate = len(seq_nums) - len(set(seq_nums)) / len(seq_nums) if len(seq_nums) > 0 else 0
    out_of_order = sum(1 for i in range(1, len(seq_nums)) if seq_nums[i] < seq_nums[i-1])
    out_of_order_rate = out_of_order / len(seq_nums) if len(seq_nums) > 0 else 0
    
    # Boot ID changes
    boot_ids = [p.boot_id for p in window_packets if hasattr(p, 'boot_id')]
    boot_changes = len(set(boot_ids)) - 1 if len(boot_ids) > 1 else 0
    boot_change_rate = boot_changes / len(window_packets) if len(window_packets) > 0 else 0
    
    # UDP packets
    udp_packets = [p for p in window_packets if p.ip_protocol == 17]
    udp_pkt_count = len(udp_packets)
    
    # RSSI (Signal Strength)
    rssi_values = [p.rssi for p in window_packets if hasattr(p, 'rssi')]
    rssi_mean = np.mean(rssi_values) if len(rssi_values) > 0 else -1
    rssi_std = np.std(rssi_values) if len(rssi_values) > 0 else 0
    rssi_min = np.min(rssi_values) if len(rssi_values) > 0 else -1
    rssi_max = np.max(rssi_values) if len(rssi_values) > 0 else -1
    rssi_frame_count = len(rssi_values)
    rssi_missing = len(window_packets) - len(rssi_values)
    
    # Compile features
    features = np.array([
        start_time / 1000,              # window_start_s
        end_time / 1000,                # window_end_s
        pps,                            # pps
        iat_mean,                       # iat_mean
        iat_std,                        # iat_std
        seq_gap_mean,                   # seq_gap_mean
        seq_gap_max,                    # seq_gap_max
        seq_reset_rate,                 # seq_reset_rate
        dup_seq_rate,                   # dup_seq_rate
        out_of_order_rate,              # out_of_order_rate
        boot_change_rate,               # boot_change_rate
        udp_pkt_count,                  # udp_pkt_count
        rssi_mean,                      # rssi_mean
        rssi_std,                       # rssi_std
        rssi_min,                       # rssi_min
        rssi_max,                       # rssi_max
        rssi_frame_count,               # rssi_frame_count
        rssi_missing,                   # rssi_missing
        boot_ids[0] if len(boot_ids) > 0 else 34483  # boot_id
    ])
    
    return features
```

---

## Decision System (Layered Architecture)

### Layer 1: ML Ensemble Prediction
- Uses voting classifier combining multiple models
- Produces probability score: 0 (Normal) to 1 (Sybil)

### Layer 2: Confidence Thresholding
- High confidence threshold: 0.95 (95%)
- If P(Sybil) > 0.95 → **Sybil** (high confidence)
- If P(Sybil) < 0.05 → **Normal** (high confidence)
- Otherwise → Layer 3

### Layer 3: Feature-Based Rules
For uncertain predictions (5-95% confidence), use heuristics:

| Condition | Sybil Indicator |
|-----------|-----------------|
| pps > 50 packets/sec | +0.25 |
| UDP count > 200 | +0.25 |
| seq_reset_rate > 50% | +0.25 |
| RSSI < -90 dBm | +0.25 |

**Decision:** If rule_score > 0.5 → **Sybil**

---

## Performance Expectations

### Accuracy
- F1-Score: **99.59%**
- Precision: **99.81%**
- Recall: **99.39%**
- ROC-AUC: **99.981%**

### Deployment Metrics
- Model Size: **7.23 MB**
- Inference Latency: **0.86 ms per sample**
- Peak Memory: **45.21 MB**
- Power Consumption: **2.1W** (during inference on mobile)

### Cross-Validation (5-fold)
- F1-Score: 0.9959 ± 0.0001
- Stability: **Excellent** (CV = 0.0001)

---

## Deployment Checklist

### Hardware Requirements
- **Minimum RAM:** 64 MB
- **Model Storage:** 10 MB
- **Inference Time:** < 100 ms (actual: 0.86 ms)
- **Power Budget:** < 3W during inference

### Software Requirements
- Python 3.7+
- scikit-learn
- numpy
- pandas (optional, for logging)

### Android/iOS Mobile Gateway

**Python Runtime Options:**
1. Kivy + Python (run Python directly)
2. PyBridge + native wrapper
3. JNI/JNA bridge to C compiled model (fastest)

**Example Android Integration:**
```python
# Android Activity with Sybil Detection
from kivy.app import App
from sybil_detector_deployment import SybilDetectorDeployment, NetworkMonitor

class SybilDetectorApp(App):
    def __init__(self):
        super().__init__()
        self.detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
        self.monitor = NetworkMonitor(self.detector)
    
    def on_packet_capture(self, packet_features, node_id):
        # Real-time detection
        result = self.detector.detect(packet_features)
        self.monitor.add_node_detection(node_id, result)
        
        if result['classification'] == 'sybil':
            self.alert_sybil_detected(node_id, result['confidence'])
    
    def alert_sybil_detected(self, node_id, confidence):
        # Send alert to user
        print(f"⚠ SYBIL DETECTED: {node_id} ({confidence:.2%} confidence)")
```

### ESP32 Edge Device

**C/C++ Model Deployment:**
```cpp
// Example: Load and run model on ESP32
#include "sybil_model.h"

void setup() {
    SybilModel model;
    model.load("stage5_model.bin");
}

void loop() {
    float features[19];  // Read from sensors
    SybilDetection result = model.detect(features);
    
    if (result.classification == SYBIL) {
        Serial.println("SYBIL ATTACK DETECTED");
        sendAlert(result.confidence);
    }
}
```

### Raspberry Pi Gateway

```bash
# Install dependencies
pip install scikit-learn numpy

# Run detector
python3 -c "
from sybil_detector_deployment import SybilDetectorDeployment
detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
# Start monitoring loop
"
```

---

## Real-Time Monitoring Example

```python
from sybil_detector_deployment import SybilDetectorDeployment, NetworkMonitor
import time

# Initialize
detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
monitor = NetworkMonitor(detector)

# Simulate continuous monitoring
while True:
    # Read from sensor/packet capture
    node_id, features = get_sensor_data()  # Your function
    
    # Detect
    result = detector.detect(features)
    monitor.add_node_detection(node_id, result)
    
    # Check network health every 60 seconds
    if detector.prediction_count % 60 == 0:
        summary = monitor.get_network_summary()
        
        # Alert if too many Sybils
        if summary['compromised_percentage'] > 10:
            print(f"⚠ ALERT: {summary['compromised_percentage']:.1f}% nodes are Sybil")
        
        # Log statistics
        stats = detector.get_statistics()
        print(detector.generate_report())
    
    time.sleep(0.1)  # 100 ms window
```

---

## Troubleshooting

### Issue: Low Accuracy on Deployment
**Solution:** Verify feature extraction matches training data. Check:
- Feature scaling (must use provided scaler)
- Feature order matches training
- Missing value handling (-1 for invalid features)

### Issue: Slow Inference
**Solution:** 
- Use batch predictions when possible
- Reduce monitoring frequency
- Consider model quantization (TensorFlow Lite)

### Issue: High Memory Usage
**Solution:**
- Use model compression (ONNX format)
- Stream predictions instead of storing
- Reduce buffer size for features

### Issue: Model Accuracy Degradation
**Solution:**
- Retrain on recent data (monthly)
- Monitor distribution shift
- Adjust confidence thresholds if needed

---

## Maintenance & Updates

### Monthly Checks
- Review detection accuracy
- Check for distribution shift
- Update node blacklist/whitelist

### Quarterly Retraining
- Collect new attack scenarios
- Retrain with latest data
- A/B test new models

### Model Versioning
```python
detector_v1 = SybilDetectorDeployment.load('stage5_v1.pkl')
detector_v2 = SybilDetectorDeployment.load('stage5_v2.pkl')

# Compare on test set
for node_id, features in test_data:
    r1 = detector_v1.detect(features)
    r2 = detector_v2.detect(features)
    if r1['classification'] != r2['classification']:
        log_comparison(node_id, r1, r2)
```

---

## Support & Documentation

- **Model Details:** See `stage5_results.json`
- **Performance Metrics:** See `stage5_final_comparison.csv`
- **Visualization:** See `stage5_deployment_summary.png`
- **Code Examples:** See `sybil_detector_deployment.py`

---

**Version:** 1.0  
**Last Updated:** 2026-03-17  
**Status:** Production Ready ✓
