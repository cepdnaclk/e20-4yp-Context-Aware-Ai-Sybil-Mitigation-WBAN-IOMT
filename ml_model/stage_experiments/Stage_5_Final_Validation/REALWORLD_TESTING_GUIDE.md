# 🚀 Real-World WBAN Sybil Detection Testing Guide

## Overview
You now have a complete notebook to test your trained Random Forest model on your real-world WBAN dataset (both labeled and unlabeled).

---

## 📋 File Location
```
Stage_5_Final_Validation/REALWORLD_TEST_DEPLOYMENT.ipynb
```

---

## 🎯 What This Notebook Does

1. ✅ **Loads Trained Model** - Random Forest from Stage 2 (99.9% F1-Score)
2. ✅ **Loads Your Real Dataset** - Your WBAN test data
3. ✅ **Preprocesses Data** - Uses same scaler from training
4. ✅ **Makes Predictions** - Classifies each node as Normal or Sybil
5. ✅ **Shows Results** - Lists all Sybil nodes with confidence scores
6. ✅ **Calculates Percentage** - % of Sybil nodes detected
7. ✅ **Generates Reports** - CSV, text summary, and visualizations

---

## 📝 Step-by-Step Running Instructions

### Step 1: Prepare Your Dataset
Your dataset should have:
- **19 features** (same as training data)
- **Optional**: 'label' or 'target' column (for validation)
- **Optional**: 'node_id' or 'mac' column (to identify nodes)

Current notebook loads: `test4.csv` (change this in Section 3!)

### Step 2: Update Dataset Path (Line ~68)
```python
# Change this line to YOUR dataset:
df_test = pd.read_csv('YOUR_DATASET.csv')  # ← Update this!
```

Options:
```python
# Option A: CSV file in same directory
df_test = pd.read_csv('your_real_data.csv')

# Option B: CSV file in parent directory
df_test = pd.read_csv('../your_real_data.csv')

# Option C: Full file path
df_test = pd.read_csv('D:\path\to\your\data.csv')
```

### Step 3: Run the Notebook
1. Open: `REALWORLD_TEST_DEPLOYMENT.ipynb`
2. Run all cells (Shift+Enter or Ctrl+Shift+Enter)
3. Wait for results

---

## 📊 What You'll Get

### Console Output (Section 6):
```
===============================================================
SYBIL DETECTION RESULTS - REAL-WORLD WBAN DATA
===============================================================

Total Nodes Tested: 1000
📊 DETECTION SUMMARY:
  ✓ Normal Nodes:    890 (89.00%)
  ⚠ Sybil Nodes:     110 (11.00%)

Average Confidence: 0.9876
Min Confidence:     0.7234
Max Confidence:     0.9999
===============================================================
```

### Files Generated:
1. **sybil_detection_results.csv** - Node-by-node detailed report
2. **sybil_detection_summary.txt** - Text summary
3. **realworld_sybil_detection_results.png** - 4 visualization charts

---

## 🔍 Understanding the Results

### CSV Output Columns:
```
Sample_ID           → Node number (0, 1, 2, ...)
Prediction          → "Normal" or "Sybil"
Sybil_Probability   → 0.0 to 1.0 (higher = more likely Sybil)
Confidence          → 0.0 to 1.0 (how sure the model is)
True_Label          → "Normal" or "Sybil" (if you provided labels)
Correct             → True/False (if you provided labels)
Node_ID / MAC       → Node identifier (if you provided it)
```

### Example Results:
```
Sample_ID  Prediction  Sybil_Probability  Confidence  Node_ID  True_Label  Correct
0          Normal      0.0234             0.9766      node_01  Normal      True
1          Sybil       0.9876             0.9876      node_02  Sybil       True
2          Normal      0.1234             0.8766      node_03  Normal      True
...
```

### Performance Metrics (Section 10):
If you have labeled data:
- **Accuracy** - Overall correctness (%)
- **Precision** - Of predicted Sybils, how many are actually Sybil
- **Recall** - Of actual Sybils, how many did we find
- **F1-Score** - Balance between Precision and Recall

---

## ⚙️ Feature Checklist

The notebook expects these 19 features from your dataset:
```
1. PPS (Packets Per Second)
2. UDP_PPS
3. ICMP_PPS
4. TCP_PPS
5. Max_PPS
6. Min_PPS
7. StdDev_PPS
8. Avg_Packet_Size
9. WiFi_Channel
10. Signal_Strength
11. Retransmission_Rate
12. Reset_Rate
13. DNS_Query_Rate
14. ARP_Query_Rate
15. DHCP_Request_Rate
16. Connection_Rate
17. Protocol_Diversity
18. Anomaly_Heuristics
19. Anomaly_Score
```

**If your dataset has different column names**, update the feature mapping in Section 4!

---

## 🐛 Troubleshooting

### Issue: "File not found" error
**Solution**: Check your file path in Section 3
```python
# Debug: Print available files in current directory
import os
print(os.listdir('.'))
```

### Issue: "Feature mismatch" error
**Solution**: Your dataset has different features than training data
- Rename your columns to match the expected 19 features
- Or modify feature_names list to match your data

### Issue: All nodes detected as Sybil (or all Normal)
**Solution**: Check if preprocessing is correct
- Run Section 4 and verify: "Data prepared for prediction"
- Check if features are in correct scale (0-100 or 0-1)

### Issue: Very low confidence scores
**Solution**: This might indicate:
- Data distribution different from training
- Features need rescaling
- Model needs fine-tuning on new data

---

## 📈 Next Steps

### If Accuracy is Good (>95%):
✅ **Deploy to Production!**
- Use sybil_detector_deployment.py (in Stage_5)
- Follow DEPLOYMENT_GUIDE.md
- Set up monitoring dashboard

### If Accuracy is Okay (85-95%):
🔄 **Fine-tune the Model**
- Retrain with your real data mixed with training data
- Adjust decision threshold in your deployment
- Increase monitoring frequency

### If Accuracy is Low (<85%):
⚠️ **Debug & Analyze**
- Check if your data matches training distribution
- Visualize feature distributions: `df_test.describe()`
- Consider collecting more training data from similar WBAN

---

## 💾 Output Files Explained

### sybil_detection_results.csv
All nodes with predictions and confidence scores. Use this to:
- Create allowlists of confirmed normal nodes
- Flag suspicious nodes for manual review
- Integrate with your network management system

### sybil_detection_summary.txt
Quick summary report for documentation.

### realworld_sybil_detection_results.png
4 visualizations:
1. **Pie chart** - Normal vs Sybil percentage
2. **Confidence histogram** - Model certainty distribution
3. **Sybil probability histogram** - Threshold analysis
4. **Performance metrics** - If labels provided

---

## 🎓 Model Information

- **Model Type**: Random Forest Classifier
- **Trees**: 300
- **Max Depth**: 15
- **Training F1-Score**: 99.59% (on Stage 2 test data)
- **Perfect For**: Real-time WBAN Sybil detection
- **Inference Speed**: 0.003259ms per sample (~307,000 nodes/second)

---

## 📞 Questions or Issues?

1. Check the notebook comments for detailed explanations
2. Review the performance metrics in Section 10
3. Visualizations in Section 11 show detection patterns
4. Exported CSV shows all details for manual analysis

---

**Status**: ✅ Ready to Test Your Real Data!
**Next Action**: Update dataset path and run the notebook
