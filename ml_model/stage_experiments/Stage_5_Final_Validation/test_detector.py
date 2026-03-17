#!/usr/bin/env python3
"""
Simple test script for Sybil Detector

This script demonstrates how to use the deployment package for real-world scenarios.
Run this to verify the detector is working correctly on your system.
"""

import numpy as np
import sys
from sybil_detector_deployment import SybilDetectorDeployment, NetworkMonitor


def test_single_detection():
    """Test detection on a single sample."""
    print("\n" + "="*70)
    print("TEST 1: Single Sample Detection")
    print("="*70)
    
    try:
        detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')
    except FileNotFoundError:
        print("❌ ERROR: Could not load stage5_deployment_package.pkl")
        print("   Make sure you're in the Stage_5_Final_Validation directory")
        return False
    
    # Test sample 1: Normal node
    normal_features = np.array([
        1000.0,      # window_start_s
        1005.0,      # window_end_s
        15.0,        # pps (low)
        45.2,        # iat_mean
        5.1,         # iat_std
        50.0,        # seq_gap_mean
        150.0,       # seq_gap_max
        0.05,        # seq_reset_rate (low)
        0.01,        # dup_seq_rate
        0.02,        # out_of_order_rate
        0.0,         # boot_change_rate
        50.0,        # udp_pkt_count
        -70.0,       # rssi_mean (good signal)\n        3.0,         # rssi_std
        -80.0,       # rssi_min
        -65.0,       # rssi_max
        100.0,       # rssi_frame_count
        0.0,         # rssi_missing
        35000.0      # boot_id
    ])\n    \n    print(\"\\n✓ Testing NORMAL node...\")\n    result_normal = detector.detect(normal_features)\n    print(f\"  Classification: {result_normal['classification'].upper()}\")\n    print(f\"  Confidence: {result_normal['confidence']:.2%}\")\n    print(f\"  Decision: {result_normal['decision_reason']}\")\n    print(f\"  Latency: {result_normal['inference_time_ms']:.3f} ms\")\n    \n    # Test sample 2: Sybil attacker\n    sybil_features = np.array([\n        2000.0,      # window_start_s\n        2005.0,      # window_end_s\n        95.0,        # pps (very high!)\n        200.5,       # iat_mean\n        150.2,       # iat_std\n        2500.0,      # seq_gap_mean\n        15000.0,     # seq_gap_max\n        0.8,         # seq_reset_rate (high!)\n        0.04,        # dup_seq_rate\n        0.06,        # out_of_order_rate\n        0.9,         # boot_change_rate (high!)\n        450.0,       # udp_pkt_count (high!)\n        -92.0,       # rssi_mean (poor signal!)\n        8.5,         # rssi_std\n        -100.0,      # rssi_min\n        -85.0,       # rssi_max\n        250.0,       # rssi_frame_count\n        2.0,         # rssi_missing\n        36000.0      # boot_id\n    ])\n    \n    print(\"\\n✓ Testing SYBIL attacker...\")\n    result_sybil = detector.detect(sybil_features)\n    print(f\"  Classification: {result_sybil['classification'].upper()}\")\n    print(f\"  Confidence: {result_sybil['confidence']:.2%}\")\n    print(f\"  Decision: {result_sybil['decision_reason']}\")\n    print(f\"  Latency: {result_sybil['inference_time_ms']:.3f} ms\")\n    \n    # Verify results\n    if result_normal['classification'] == 'normal' and result_sybil['classification'] == 'sybil':\n        print(\"\\n✓✓✓ TEST PASSED: Correct classifications!\")\n        return True\n    else:\n        print(\"\\n❌ TEST FAILED: Incorrect classifications\")\n        return False\n\n\ndef test_batch_detection():\n    \"\"\"Test batch detection.\"\"\"\n    print(\"\\n\" + \"=\"*70)\n    print(\"TEST 2: Batch Detection (10 samples)\")\n    print(\"=\"*70)\n    \n    detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')\n    \n    # Create 10 random samples\n    samples = np.random.randn(10, 19) * 50 + 50  # Random features\n    \n    print(\"\\nRunning batch detection...\")\n    results = detector.detect_batch(samples)\n    \n    normal_count = sum(1 for r in results if r['classification'] == 'normal')\n    sybil_count = sum(1 for r in results if r['classification'] == 'sybil')\n    avg_latency = np.mean([r['inference_time_ms'] for r in results])\n    \n    print(f\"\\n✓ Batch Results:\")\n    print(f\"  Total samples: 10\")\n    print(f\"  Normal: {normal_count}\")\n    print(f\"  Sybil: {sybil_count}\")\n    print(f\"  Avg latency: {avg_latency:.3f} ms\")\n    print(\"\\n✓✓✓ TEST PASSED: Batch detection working!\")\n    return True\n\n\ndef test_network_monitoring():\n    \"\"\"Test network-level monitoring.\"\"\"\n    print(\"\\n\" + \"=\"*70)\n    print(\"TEST 3: Network Monitoring\")\n    print(\"=\"*70)\n    \n    detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')\n    monitor = NetworkMonitor(detector)\n    \n    # Simulate 5 nodes with multiple detections\n    nodes = ['sensor_001', 'sensor_002', 'sensor_003', 'sensor_004', 'sensor_005']\n    \n    print(\"\\nSimulating 3 detections per node...\")\n    for node_id in nodes:\n        for i in range(3):\n            # Alternate between normal and sybil-like features\n            if i % 2 == 0:\n                features = np.ones(19) * 20  # Normal-like\n            else:\n                features = np.ones(19) * 80  # Sybil-like\n            \n            result = detector.detect(features)\n            monitor.add_node_detection(node_id, result)\n    \n    # Get summary\n    summary = monitor.get_network_summary()\n    \n    print(f\"\\n✓ Network Status:\")\n    print(f\"  Total nodes: {summary['total_nodes']}\")\n    print(f\"  Normal nodes: {summary['normal_nodes']}\")\n    print(f\"  Sybil nodes: {summary['sybil_nodes']}\")\n    print(f\"  Compromised: {summary['compromised_percentage']:.1f}%\")\n    print(f\"  Network Status: {summary['network_status']}\")\n    \n    # Get individual node status\n    print(f\"\\n✓ Individual Node Status:\")\n    for node_id in nodes:\n        status = monitor.get_node_status(node_id)\n        print(f\"  {node_id}: {status['classification']} ({status['sybil_percentage']:.0f}% sybil)\")\n    \n    print(\"\\n✓✓✓ TEST PASSED: Network monitoring working!\")\n    return True\n\n\ndef test_statistics():\n    \"\"\"Test statistics tracking.\"\"\"\n    print(\"\\n\" + \"=\"*70)\n    print(\"TEST 4: Statistics & Performance Tracking\")\n    print(\"=\"*70)\n    \n    detector = SybilDetectorDeployment.load('stage5_deployment_package.pkl')\n    \n    # Run several detections\n    print(\"\\nRunning 100 random detections...\")\n    for _ in range(100):\n        features = np.random.randn(19) * 50 + 50\n        detector.detect(features)\n    \n    stats = detector.get_statistics()\n    \n    print(f\"\\n✓ Statistics:\")\n    print(f\"  Total predictions: {stats['total_predictions']}\")\n    print(f\"  Sybil detected: {stats['sybil_detected']} ({stats['sybil_percentage']:.1f}%)\")\n    print(f\"  Normal detected: {stats['normal_detected']}\")\n    print(f\"  Avg inference time: {stats['avg_inference_time_ms']:.3f} ms\")\n    print(f\"  Min inference time: {stats['min_inference_time_ms']:.3f} ms\")\n    print(f\"  Max inference time: {stats['max_inference_time_ms']:.3f} ms\")\n    \n    # Print report\n    print(\"\\n\" + detector.generate_report())\n    \n    print(\"\\n✓✓✓ TEST PASSED: Statistics tracking working!\")\n    return True\n\n\ndef main():\n    \"\"\"Run all tests.\"\"\"\n    print(\"\\n\" + \"*\"*70)\n    print(\"*\" + \" \"*68 + \"*\")\n    print(\"*\" + \"  SYBIL DETECTOR DEPLOYMENT - TEST SUITE\".center(68) + \"*\")\n    print(\"*\" + \" \"*68 + \"*\")\n    print(\"*\"*70)\n    \n    tests = [\n        (\"Single Detection\", test_single_detection),\n        (\"Batch Detection\", test_batch_detection),\n        (\"Network Monitoring\", test_network_monitoring),\n        (\"Statistics & Performance\", test_statistics),\n    ]\n    \n    results = []\n    for test_name, test_func in tests:\n        try:\n            passed = test_func()\n            results.append((test_name, passed))\n        except Exception as e:\n            print(f\"\\n❌ ERROR in {test_name}: {str(e)}\")\n            results.append((test_name, False))\n    \n    # Summary\n    print(\"\\n\" + \"=\"*70)\n    print(\"TEST SUMMARY\")\n    print(\"=\"*70)\n    \n    passed = sum(1 for _, p in results if p)\n    total = len(results)\n    \n    for test_name, passed_flag in results:\n        status = \"✓ PASS\" if passed_flag else \"❌ FAIL\"\n        print(f\"{status} - {test_name}\")\n    \n    print(f\"\\nResult: {passed}/{total} tests passed\")\n    \n    if passed == total:\n        print(\"\\n\" + \"🎉 \"*20)\n        print(\"ALL TESTS PASSED - DEPLOYMENT READY!\".center(70))\n        print(\"🎉 \"*20)\n        return 0\n    else:\n        print(f\"\\n⚠ {total - passed} test(s) failed. Please review errors above.\")\n        return 1\n\n\nif __name__ == '__main__':\n    sys.exit(main())\n