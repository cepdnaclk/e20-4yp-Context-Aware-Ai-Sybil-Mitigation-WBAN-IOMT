"""
Sybil Detector - Deployment Module for Mobile/Gateway
======================================================

This module provides a lightweight, production-ready Sybil detection system
for WiFi/BLE WBAN sensor networks deployed on mobile gateways or edge devices.

Features:
- Layered decision-making (ML + Confidence Thresholding + Feature Rules)
- Real-time inference with minimal latency
- Low power consumption optimized for mobile devices
- Node-level and network-level reporting

Usage:
    from sybil_detector_deployment import SybilDetectorDeployment
    
    detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
    result = detector.detect(raw_features)
    
    print(f"Node Classification: {result['classification']}")  # 'normal' or 'sybil'
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Decision Reason: {result['decision_reason']}")
"""

import numpy as np
import pickle
import time
from typing import Dict, List, Tuple, Any
from datetime import datetime


class SybilDetectorDeployment:
    """
    Production-ready Sybil detection system for mobile/gateway deployment.
    
    Architecture:
    - Layer 1: ML Ensemble prediction
    - Layer 2: Confidence-based thresholding (95%)
    - Layer 3: Feature-based rules for uncertain cases
    """
    
    def __init__(self, model, scaler, feature_names: List[str],
                 high_confidence_threshold: float = 0.95,
                 rule_threshold: float = 0.5):
        """
        Initialize the Sybil detector.
        
        Args:
            model: Trained ensemble model
            scaler: StandardScaler from training
            feature_names: List of feature names in order
            high_confidence_threshold: Confidence threshold for high-confidence decisions
            rule_threshold: Threshold for rule-based decisions
        """
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names
        self.high_confidence_threshold = high_confidence_threshold
        self.rule_threshold = rule_threshold
        
        # Performance tracking
        self.inference_times = []
        self.prediction_count = 0
        self.sybil_count = 0
        self.normal_count = 0
    
    @classmethod
    def load(cls, package_path: str) -> 'SybilDetectorDeployment':
        """
        Load a pre-trained detector from a deployment package.
        
        Args:
            package_path: Path to stage5_deployment_package.pkl
            
        Returns:
            SybilDetectorDeployment instance
        """
        with open(package_path, 'rb') as f:
            package = pickle.load(f)
        
        detector = cls(
            model=package['model'],
            scaler=package['scaler'],
            feature_names=package['feature_names'],
            high_confidence_threshold=package['config']['high_confidence_threshold'],
            rule_threshold=package['config']['rule_threshold']
        )
        return detector
    
    def detect(self, raw_features: np.ndarray) -> Dict[str, Any]:
        """
        Detect Sybil attack on a single sample.
        
        Args:
            raw_features: Raw feature vector (should match training features)
            
        Returns:
            Dictionary with:
            - classification: 'sybil' or 'normal'
            - confidence: Confidence score (0-1)
            - ml_probability: Raw ML model probability
            - decision_layer: Which layer made the decision
            - decision_reason: Explanation of decision
            - inference_time_ms: How long inference took
        """
        start_time = time.time()
        
        # Reshape if single sample
        if raw_features.ndim == 1:
            raw_features = raw_features.reshape(1, -1)
        
        # Scale features
        X_scaled = self.scaler.transform(raw_features)
        
        # Layer 1: ML Prediction
        ml_prob = self.model.predict_proba(X_scaled)[0, 1]  # Probability of Sybil
        ml_pred = self.model.predict(X_scaled)[0]
        
        # Layer 2: Confidence-based decision
        if ml_prob > self.high_confidence_threshold:
            classification = 'sybil'
            confidence = ml_prob
            decision_layer = 2
            decision_reason = f"High confidence Sybil (ML prob: {ml_prob:.2%})"
        elif ml_prob < (1 - self.high_confidence_threshold):
            classification = 'normal'
            confidence = 1 - ml_prob
            decision_layer = 2
            decision_reason = f"High confidence Normal (ML prob: {ml_prob:.2%})"
        else:
            # Layer 3: Feature-based rules
            rule_score = self._feature_rules(raw_features[0])
            if rule_score > self.rule_threshold:
                classification = 'sybil'
                confidence = rule_score
            else:
                classification = 'normal'
                confidence = 1 - rule_score
            decision_layer = 3
            decision_reason = f"Rule-based {classification} (rule score: {rule_score:.2%})"
        
        # Update statistics
        self.prediction_count += 1
        if classification == 'sybil':
            self.sybil_count += 1
        else:
            self.normal_count += 1
        
        inference_time = (time.time() - start_time) * 1000  # ms
        self.inference_times.append(inference_time)
        
        return {
            'classification': classification,
            'confidence': confidence,
            'ml_probability': ml_prob,
            'decision_layer': decision_layer,
            'decision_reason': decision_reason,
            'inference_time_ms': inference_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_batch(self, raw_features: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect Sybil attacks on multiple samples.
        
        Args:
            raw_features: Feature matrix (N x M)
            
        Returns:
            List of detection results
        """
        results = []
        for i in range(len(raw_features)):
            result = self.detect(raw_features[i])
            results.append(result)
        return results
    
    def _feature_rules(self, features: np.ndarray) -> float:
        """
        Rule-based check for uncertain cases using feature heuristics.
        
        Returns:
            Sybil probability (0-1)
        """
        sybil_score = 0
        num_checks = 0
        
        feature_dict = {name: value for name, value in zip(self.feature_names, features)}
        
        # Rule 1: High packets per second (typical of Sybil)
        if 'pps' in feature_dict and feature_dict['pps'] > 50:
            sybil_score += 0.25
        num_checks += 1
        
        # Rule 2: High UDP packet count
        if 'udp_pkt_count' in feature_dict and feature_dict['udp_pkt_count'] > 200:
            sybil_score += 0.25
        num_checks += 1
        
        # Rule 3: High sequence reset rate (anomalous behavior)
        if 'seq_reset_rate' in feature_dict and feature_dict['seq_reset_rate'] > 0.5:
            sybil_score += 0.25
        num_checks += 1
        
        # Rule 4: Poor signal strength (impossible for legitimate node)
        if 'rssi_mean' in feature_dict and feature_dict['rssi_mean'] < -90:
            sybil_score += 0.25
        num_checks += 1
        
        return sybil_score / num_checks if num_checks > 0 else 0.5
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get inference statistics.
        
        Returns:
            Dictionary with:
            - total_predictions: Number of predictions made
            - sybil_detected: Number of Sybil nodes detected
            - normal_detected: Number of normal nodes detected
            - sybil_percentage: Percentage of detected Sybils
            - avg_inference_time_ms: Average inference latency
            - min_inference_time_ms: Minimum inference latency
            - max_inference_time_ms: Maximum inference latency
        """
        if self.prediction_count == 0:
            return {
                'total_predictions': 0,
                'sybil_detected': 0,
                'normal_detected': 0,
                'sybil_percentage': 0,
                'avg_inference_time_ms': 0,
                'min_inference_time_ms': 0,
                'max_inference_time_ms': 0
            }
        
        return {
            'total_predictions': self.prediction_count,
            'sybil_detected': self.sybil_count,
            'normal_detected': self.normal_count,
            'sybil_percentage': (self.sybil_count / self.prediction_count) * 100,
            'avg_inference_time_ms': np.mean(self.inference_times),
            'min_inference_time_ms': np.min(self.inference_times),
            'max_inference_time_ms': np.max(self.inference_times)
        }
    
    def generate_report(self) -> str:
        """
        Generate a human-readable report of detection statistics.
        """
        stats = self.get_statistics()
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║         SYBIL DETECTION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}               ║
╚══════════════════════════════════════════════════════════════════════╝

DETECTION SUMMARY
─────────────────
Total Predictions:    {stats['total_predictions']:,}
Sybil Detected:       {stats['sybil_detected']:,} ({stats['sybil_percentage']:.1f}%)
Normal Detected:      {stats['normal_detected']:,}

PERFORMANCE METRICS
──────────────────
Avg Inference Time:   {stats['avg_inference_time_ms']:.3f} ms
Min Inference Time:   {stats['min_inference_time_ms']:.3f} ms
Max Inference Time:   {stats['max_inference_time_ms']:.3f} ms

DEPLOYMENT STATUS
────────────────
✓ Model loaded and ready
✓ Real-time inference operating
✓ Statistics tracking active

"""
        return report


class NetworkMonitor:
    """Monitor Sybil activity at the network level."""
    
    def __init__(self, detector: SybilDetectorDeployment):
        self.detector = detector
        self.node_history = {}  # Track per-node detection history
    
    def add_node_detection(self, node_id: str, detection_result: Dict) -> None:
        """
        Record detection result for a node.
        
        Args:
            node_id: Identifier for the node
            detection_result: Result from detector.detect()
        """
        if node_id not in self.node_history:
            self.node_history[node_id] = {
                'detections': [],
                'sybil_count': 0,
                'normal_count': 0,
                'confidence_scores': []
            }
        
        history = self.node_history[node_id]
        history['detections'].append(detection_result)
        
        if detection_result['classification'] == 'sybil':
            history['sybil_count'] += 1
        else:
            history['normal_count'] += 1
        
        history['confidence_scores'].append(detection_result['confidence'])
    
    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """
        Get detailed status for a specific node.
        
        Returns:
            Dictionary with node classification, confidence, and trend
        """
        if node_id not in self.node_history:
            return None
        
        history = self.node_history[node_id]
        total = len(history['detections'])
        sybil_pct = (history['sybil_count'] / total * 100) if total > 0 else 0
        avg_confidence = np.mean(history['confidence_scores'])
        
        # Classify node based on majority voting
        if sybil_pct > 50:
            classification = 'SYBIL'
        else:
            classification = 'NORMAL'
        
        return {
            'node_id': node_id,
            'classification': classification,
            'sybil_percentage': sybil_pct,
            'total_detections': total,
            'avg_confidence': avg_confidence,
            'trend': self._calculate_trend(history['confidence_scores'])
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend in confidence scores."""
        if len(scores) < 2:
            return 'insufficient_data'
        
        recent = np.mean(scores[-5:])
        older = np.mean(scores[:-5]) if len(scores) > 5 else np.mean(scores[0:1])
        
        if recent > older + 0.05:
            return 'increasing_sybil_risk'
        elif recent < older - 0.05:
            return 'decreasing_sybil_risk'
        else:
            return 'stable'
    
    def get_network_summary(self) -> Dict[str, Any]:
        """Get overall network health summary."""
        total_nodes = len(self.node_history)
        sybil_nodes = sum(1 for node_id in self.node_history 
                         if self.get_node_status(node_id)['classification'] == 'SYBIL')
        normal_nodes = total_nodes - sybil_nodes
        
        return {
            'total_nodes': total_nodes,
            'sybil_nodes': sybil_nodes,
            'normal_nodes': normal_nodes,
            'compromised_percentage': (sybil_nodes / total_nodes * 100) if total_nodes > 0 else 0,
            'network_status': 'SECURE' if sybil_nodes / total_nodes < 0.1 else 'COMPROMISED'
        }


# Example usage
if __name__ == '__main__':
    print("Sybil Detector Deployment Module")
    print("================================")
    print("\nUsage:")
    print("  from sybil_detector_deployment import SybilDetectorDeployment")
    print("  detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')")
    print("  result = detector.detect(raw_features)")
    print("\nFor network monitoring:")
    print("  from sybil_detector_deployment import SybilDetectorDeployment, NetworkMonitor")
    print("  monitor = NetworkMonitor(detector)")
    print("  monitor.add_node_detection('node1', result)")
    print("  summary = monitor.get_network_summary()")
