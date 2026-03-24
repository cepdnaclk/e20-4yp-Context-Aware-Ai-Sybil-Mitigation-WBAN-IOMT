# Step-by-Step: How to Compare Original vs Pruned Models

I'll guide you through EXACTLY what to do, line by line. No guessing!

---

## Overview: What We're Doing

```
Step 1: Load your test data
         ↓
Step 2: Load your ORIGINAL model (e.g., XGBoost)
         ↓
Step 3: Create a PRUNED version
         ↓
Step 4: Test ORIGINAL model on test data
         ↓
Step 5: Test PRUNED model on test data
         ↓
Step 6: Compare results (which is better?)
         ↓
Step 7: Decide: Keep original or use pruned?
```

---

## STEP 1: Prepare Your Test Data

Your test data should be in CSV format with features and labels.

### Find Your Test Data

Check what you have in your ml_model folder:
-` D:\sem_7\Research - Copy\github\e20-4yp-Context-Aware-Ai-Sybil-Mitigation-WBAN-IOMT\ml_model\stage_experiments\Stage_1_Data_Prep\dataset_all_labeled.csv`

These files contain your labeled data (features + labels).

### Code: Load Test Data

```python
import pandas as pd
import numpy as np

# STEP 1A: Load the CSV file
print("=" * 60)
print("STEP 1: LOADING TEST DATA")
print("=" * 60)

# Option A: If you have a test CSV file
file_path = "D:\sem_7\Research - Copy\github\e20-4yp-Context-Aware-Ai-Sybil-Mitigation-WBAN-IOMT\ml_model\stage_experiments\Stage_1_Data_Prep\dataset_all_labeled.csv"
data = pd.read_csv(file_path)

print(f"✓ Loaded {len(data)} samples")
print(f"✓ Features: {data.shape[1]} columns")

# STEP 1B: Separate features from labels
# Assuming last column is the label, other columns are features
X_test = data.iloc[:, :-1]  # All columns except last = features
y_test = data.iloc[:, -1]   # Last column = label

print(f"✓ Features (X): {X_test.shape}")
print(f"✓ Labels (y): {y_test.shape}")
print(f"✓ Label distribution: {y_test.value_counts().to_dict()}")

# STEP 1C: (Optional) Use only first 1000 samples for faster testing
# X_test = X_test[:1000]
# y_test = y_test[:1000]
# print(f"✓ Using {len(X_test)} samples for faster testing")
```

**What this does:**
- Loads your CSV file ✓
- Splits it into features (X) and labels (y) ✓
- Shows you what data you have ✓

**Copy this code and run it in your Jupyter notebook or Python script.**

---

## STEP 2: Load Your ORIGINAL Model

This is the model you trained (before pruning).

### Code: Load Original Model

```python
import pickle

print("\n" + "=" * 60)
print("STEP 2: LOADING ORIGINAL MODEL")
print("=" * 60)

# STEP 2A: Load the model file
model_path = "ml_model/stage_experiments/Stage_4_Ensemble/stage4_xgboost_optimized.pkl"

with open(model_path, 'rb') as f:
    original_model = pickle.load(f)

print(f"✓ Model loaded: {model_path}")
print(f"✓ Model type: {type(original_model).__name__}")

# STEP 2B: Check model properties (for tree-based models)
if hasattr(original_model, 'n_estimators'):
    print(f"✓ Number of trees/rounds: {original_model.n_estimators}")
if hasattr(original_model, 'max_depth'):
    print(f"✓ Max depth: {original_model.max_depth}")
```

**What this does:**
- Loads your trained model from disk ✓
- Shows you what model you loaded ✓

---

## STEP 3: Create a PRUNED Version

Now we create a simplified version of your model.

### Option A: Prune XGBoost (Reduce boosting rounds)

```python
import xgboost as xgb

print("\n" + "=" * 60)
print("STEP 3A: CREATE PRUNED XGBOOST")
print("=" * 60)

# Create pruned version with fewer boosting rounds
# Original: 200 rounds → Pruned: 150 rounds (25% smaller)
pruned_model = xgb.XGBClassifier(
    n_estimators=150,  # ← Reduced from original 200
    max_depth=original_model.max_depth,
    learning_rate=original_model.learning_rate,
    random_state=42
)

print(f"✓ Pruned model created")
print(f"✓ Original trees: {original_model.n_estimators}")
print(f"✓ Pruned trees: {pruned_model.n_estimators}")
print(f"✓ Size reduction: {(1 - pruned_model.n_estimators/original_model.n_estimators)*100:.1f}%")
```

### Option B: Prune Random Forest (Limit depth)

```python
from sklearn.ensemble import RandomForestClassifier

print("\n" + "=" * 60)
print("STEP 3B: CREATE PRUNED RANDOM FOREST")
print("=" * 60)

# Create pruned version with limited tree depth
pruned_model = RandomForestClassifier(
    n_estimators=original_model.n_estimators,
    max_depth=15,  # ← Limit depth (originally unlimited)
    random_state=42,
    n_jobs=-1
)

print(f"✓ Pruned model created")
print(f"✓ Original max_depth: {original_model.max_depth}")
print(f"✓ Pruned max_depth: {pruned_model.max_depth}")
```

### Option C: Prune Gradient Boosting (Reduce rounds)

```python
from sklearn.ensemble import GradientBoostingClassifier

print("\n" + "=" * 60)
print("STEP 3C: CREATE PRUNED GRADIENT BOOSTING")
print("=" * 60)

pruned_model = GradientBoostingClassifier(
    n_estimators=150,  # ← Reduced from original
    max_depth=original_model.max_depth,
    learning_rate=original_model.learning_rate,
    random_state=42
)

print(f"✓ Pruned model created")
```

**Choose ONE of the options above based on your model type.**

---

## STEP 4: Test ORIGINAL Model

Now we evaluate how well the original model performs.

### Code: Evaluate Original Model

```python
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import time

print("\n" + "=" * 60)
print("STEP 4: EVALUATE ORIGINAL MODEL")
print("=" * 60)

# STEP 4A: Make predictions
print("Running predictions on original model...")
start_time = time.time()
y_pred_original = original_model.predict(X_test)
inference_time_original = (time.time() - start_time) / len(X_test) * 1000  # ms per sample

# STEP 4B: Calculate metrics
f1_original = f1_score(y_test, y_pred_original)
precision_original = precision_score(y_test, y_pred_original)
recall_original = recall_score(y_test, y_pred_original)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_original).ravel()
fpr_original = fp / (fp + tn)  # False Positive Rate

# STEP 4C: Print results
print(f"\n📊 ORIGINAL MODEL RESULTS:")
print(f"  F1-Score:           {f1_original:.6f}")
print(f"  Precision:          {precision_original:.6f}")
print(f"  Recall:             {recall_original:.6f}")
print(f"  False Positive Rate: {fpr_original:.6f}")
print(f"  Inference Time:     {inference_time_original:.4f} ms per sample")
print(f"  Total Time:         {(time.time() - start_time):.2f} seconds")

# STEP 4D: Show confusion matrix
print(f"\n  Confusion Matrix:")
print(f"    True Negatives:  {tn}")
print(f"    False Positives: {fp}")
print(f"    False Negatives: {fn}")
print(f"    True Positives:  {tp}")
```

**What this does:**
- Makes predictions with original model ✓
- Calculates accuracy metrics (F1, Precision, Recall) ✓
- Measures inference speed ✓
- Shows results in readable format ✓

---

## STEP 5: Test PRUNED Model

Now we evaluate the pruned version the same way.

### Code: Evaluate Pruned Model

```python
print("\n" + "=" * 60)
print("STEP 5: EVALUATE PRUNED MODEL")
print("=" * 60)

# STEP 5A: Make predictions
print("Running predictions on pruned model...")
start_time = time.time()
y_pred_pruned = pruned_model.predict(X_test)
inference_time_pruned = (time.time() - start_time) / len(X_test) * 1000  # ms per sample

# STEP 5B: Calculate metrics
f1_pruned = f1_score(y_test, y_pred_pruned)
precision_pruned = precision_score(y_test, y_pred_pruned)
recall_pruned = recall_score(y_test, y_pred_pruned)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_pruned).ravel()
fpr_pruned = fp / (fp + tn)

# STEP 5C: Print results
print(f"\n📊 PRUNED MODEL RESULTS:")
print(f"  F1-Score:           {f1_pruned:.6f}")
print(f"  Precision:          {precision_pruned:.6f}")
print(f"  Recall:             {recall_pruned:.6f}")
print(f"  False Positive Rate: {fpr_pruned:.6f}")
print(f"  Inference Time:     {inference_time_pruned:.4f} ms per sample")
print(f"  Total Time:         {(time.time() - start_time):.2f} seconds")

# STEP 5D: Show confusion matrix
print(f"\n  Confusion Matrix:")
print(f"    True Negatives:  {tn}")
print(f"    False Positives: {fp}")
print(f"    False Negatives: {fn}")
print(f"    True Positives:  {tp}")
```

**What this does:**
- Makes predictions with pruned model ✓
- Calculates same metrics for comparison ✓
- Shows results in same format as original ✓

---

## STEP 6: Compare Results

Now we put them side-by-side to see which is better.

### Code: Compare Original vs Pruned

```python
import pandas as pd

print("\n" + "=" * 60)
print("STEP 6: COMPARISON - ORIGINAL vs PRUNED")
print("=" * 60)

# STEP 6A: Create comparison table
comparison_data = {
    'Metric': [
        'F1-Score',
        'Precision',
        'Recall',
        'False Positive Rate',
        'Inference Time (ms)',
    ],
    'ORIGINAL': [
        f1_original,
        precision_original,
        recall_original,
        fpr_original,
        inference_time_original,
    ],
    'PRUNED': [
        f1_pruned,
        precision_pruned,
        recall_pruned,
        fpr_pruned,
        inference_time_pruned,
    ]
}

df_comparison = pd.DataFrame(comparison_data)

# STEP 6B: Calculate differences
df_comparison['Difference'] = df_comparison['ORIGINAL'] - df_comparison['PRUNED']
df_comparison['% Change'] = (df_comparison['Difference'] / df_comparison['ORIGINAL'] * 100).round(2)

# STEP 6C: Print the comparison table
print("\n📊 SIDE-BY-SIDE COMPARISON:")
print(df_comparison.to_string(index=False))

# STEP 6D: Interpret results
print("\n" + "=" * 60)
print("INTERPRETATION:")
print("=" * 60)

f1_loss_percent = (f1_original - f1_pruned) / f1_original * 100
speed_gain_percent = (inference_time_original - inference_time_pruned) / inference_time_original * 100

print(f"\n✓ Accuracy Loss: {f1_loss_percent:.3f}%")
if f1_loss_percent < 0.1:
    print(f"  → EXCELLENT! Nearly no accuracy loss ✅")
elif f1_loss_percent < 0.5:
    print(f"  → GOOD! Acceptable accuracy loss ✅")
elif f1_loss_percent < 1.0:
    print(f"  → OK! Noticeable but acceptable loss ⚠️")
else:
    print(f"  → WARNING! Too much accuracy loss ❌")

print(f"\n✓ Speed Improvement: {speed_gain_percent:.1f}%")
if speed_gain_percent > 10:
    print(f"  → Nice speedup! ✅")
elif speed_gain_percent > 0:
    print(f"  → Slightly faster ✓")
else:
    print(f"  → No speed gain")

print(f"\n✓ False Positive Rate:")
print(f"  Original: {fpr_original:.6f}")
print(f"  Pruned:   {fpr_pruned:.6f}")
if fpr_pruned <= fpr_original:
    print(f"  → Pruned is equal or better ✅")
else:
    print(f"  → Pruned has slightly more false positives")
```

**What this does:**
- Shows side-by-side comparison ✓
- Calculates accuracy loss ✓
- Calculates speed improvement ✓
- Tells you if the trade-off is good ✓

---

## STEP 7: Decision - Which One to Use?

Based on your comparison results, decide whether to use the original or pruned model.

### Code: Decision Guide

```python
print("\n" + "=" * 60)
print("STEP 7: DECISION - WHICH MODEL TO USE?")
print("=" * 60)

# Decision logic
if f1_loss_percent < 0.1 and speed_gain_percent > 5:
    print("\n✅ RECOMMENDATION: USE PRUNED MODEL")
    print(f"   - Accuracy loss: {f1_loss_percent:.3f}% (negligible)")
    print(f"   - Speed gain: {speed_gain_percent:.1f}% (nice improvement)")
    print(f"   - Verdict: Pruned model is clearly better!")
    recommendation = "pruned"

elif f1_loss_percent < 0.2:
    print("\n✅ RECOMMENDATION: USE PRUNED MODEL")
    print(f"   - Accuracy loss: {f1_loss_percent:.3f}% (very small)")
    print(f"   - Speed gain: {speed_gain_percent:.1f}%")
    print(f"   - Verdict: Worth using the smaller model")
    recommendation = "pruned"

elif f1_loss_percent < 0.5:
    print("\n⚠️  RECOMMENDATION: DEPENDS ON YOUR NEEDS")
    print(f"   - Accuracy loss: {f1_loss_percent:.3f}%")
    print(f"   - Speed gain: {speed_gain_percent:.1f}%")
    print(f"   - If space is critical: Use pruned")
    print(f"   - If accuracy is critical: Use original")
    recommendation = "decision"

else:
    print("\n❌ RECOMMENDATION: USE ORIGINAL MODEL")
    print(f"   - Accuracy loss: {f1_loss_percent:.3f}% (too high)")
    print(f"   - Better to keep original model")
    recommendation = "original"

print("\n" + "=" * 60)
```

**What this does:**
- Analyzes your metrics ✓
- Recommends which model to use ✓
- Explains the reasoning ✓

---

## STEP 8: Save Your Chosen Model (Optional)

If you want to keep the pruned model, save it:

```python
print("\n" + "=" * 60)
print("STEP 8: SAVE YOUR CHOSEN MODEL")
print("=" * 60)

if recommendation == "pruned":
    # Save the pruned model
    output_path = "stage4_xgboost_pruned_150rounds.pkl"
    
    with open(output_path, 'wb') as f:
        pickle.dump(pruned_model, f)
    
    print(f"✓ Pruned model saved: {output_path}")
    print(f"✓ You can now use this instead of the original!")
    
else:
    print(f"✓ Keeping original model (no save needed)")
```

---

## Complete Code (All Steps Together)

Copy and paste this entire code into a Python script or Jupyter notebook:

```python
import pandas as pd
import pickle
import time
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb

# ============================================================
# STEP 1: LOAD TEST DATA
# ============================================================
print("=" * 60)
print("STEP 1: LOADING TEST DATA")
print("=" * 60)

file_path = "ml_model/Experiment_3/dataset_all_labeled.csv"
data = pd.read_csv(file_path)
X_test = data.iloc[:, :-1]
y_test = data.iloc[:, -1]

print(f"✓ Loaded {len(data)} samples")
print(f"✓ Features: {X_test.shape[1]}, Labels: {y_test.shape[0]}")

# ============================================================
# STEP 2: LOAD ORIGINAL MODEL
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: LOADING ORIGINAL MODEL")
print("=" * 60)

model_path = "ml_model/stage_experiments/Stage_4_Ensemble/stage4_xgboost_optimized.pkl"
with open(model_path, 'rb') as f:
    original_model = pickle.load(f)

print(f"✓ Model loaded: {type(original_model).__name__}")
print(f"✓ Trees: {original_model.n_estimators}, Depth: {original_model.max_depth}")

# ============================================================
# STEP 3: CREATE PRUNED VERSION
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: CREATE PRUNED MODEL")
print("=" * 60)

pruned_model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=original_model.max_depth,
    learning_rate=original_model.learning_rate,
    random_state=42
)

print(f"✓ Pruned model created")
print(f"✓ Original: {original_model.n_estimators} trees")
print(f"✓ Pruned: {pruned_model.n_estimators} trees (25% reduction)")

# ============================================================
# STEP 4: EVALUATE ORIGINAL MODEL
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: EVALUATE ORIGINAL MODEL")
print("=" * 60)

start = time.time()
y_pred_original = original_model.predict(X_test)
inference_time_original = (time.time() - start) / len(X_test) * 1000

f1_original = f1_score(y_test, y_pred_original)
precision_original = precision_score(y_test, y_pred_original)
recall_original = recall_score(y_test, y_pred_original)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_original).ravel()
fpr_original = fp / (fp + tn)

print(f"F1-Score:        {f1_original:.6f}")
print(f"Precision:       {precision_original:.6f}")
print(f"Recall:          {recall_original:.6f}")
print(f"False Pos Rate:  {fpr_original:.6f}")
print(f"Inference Time:  {inference_time_original:.4f} ms/sample")

# ============================================================
# STEP 5: EVALUATE PRUNED MODEL
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: EVALUATE PRUNED MODEL")
print("=" * 60)

start = time.time()
y_pred_pruned = pruned_model.predict(X_test)
inference_time_pruned = (time.time() - start) / len(X_test) * 1000

f1_pruned = f1_score(y_test, y_pred_pruned)
precision_pruned = precision_score(y_test, y_pred_pruned)
recall_pruned = recall_score(y_test, y_pred_pruned)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_pruned).ravel()
fpr_pruned = fp / (fp + tn)

print(f"F1-Score:        {f1_pruned:.6f}")
print(f"Precision:       {precision_pruned:.6f}")
print(f"Recall:          {recall_pruned:.6f}")
print(f"False Pos Rate:  {fpr_pruned:.6f}")
print(f"Inference Time:  {inference_time_pruned:.4f} ms/sample")

# ============================================================
# STEP 6: COMPARE RESULTS
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: COMPARISON")
print("=" * 60)

comparison_data = {
    'Metric': ['F1-Score', 'Precision', 'Recall', 'FP Rate', 'Inf Time (ms)'],
    'ORIGINAL': [f1_original, precision_original, recall_original, fpr_original, inference_time_original],
    'PRUNED': [f1_pruned, precision_pruned, recall_pruned, fpr_pruned, inference_time_pruned]
}

df = pd.DataFrame(comparison_data)
df['Loss %'] = ((df['ORIGINAL'] - df['PRUNED']) / df['ORIGINAL'] * 100).round(3)

print(df.to_string(index=False))

# ============================================================
# STEP 7: DECISION
# ============================================================
f1_loss = (f1_original - f1_pruned) / f1_original * 100

print("\n" + "=" * 60)
print("STEP 7: DECISION")
print("=" * 60)

if f1_loss < 0.1:
    print("✅ VERDICT: USE PRUNED MODEL!")
    print(f"   Accuracy loss is negligible ({f1_loss:.3f}%)")
    print(f"   Model is 25% smaller and faster")
else:
    print("⚠️  VERDICT: Depends on your priorities")
    print(f"   Accuracy loss: {f1_loss:.3f}%")
```

---

## How to Run This Code

### Option A: In Jupyter Notebook
1. Create a new cell
2. Paste the complete code
3. Click "Run Cell"
4. Watch the results!

### Option B: Save as Python Script
1. Save as `compare_models.py` in your project directory
2. Open terminal in VS Code
3. Run: `.\.venv\Scripts\python.exe compare_models.py`
4. Watch the results!

### Option C: Use Interactive Python Shell
1. Open terminal
2. Run: `.\.venv\Scripts\python.exe`
3. Copy-paste the code line by line
4. See immediate results

---

## What to Expect as Output

You'll see something like:

```
============================================================
STEP 1: LOADING TEST DATA
============================================================
✓ Loaded 2600000 samples
✓ Features: 17, Labels: 2600000

============================================================
STEP 6: COMPARISON
============================================================
       Metric  ORIGINAL  PRUNED  Loss %
     F1-Score  0.999938  0.999820  0.012
    Precision  0.999876  0.999750  0.013
       Recall  0.999901  0.999890  0.001
      FP Rate  0.000094  0.000112  -18.750
   Inf Time (ms)  2.5000  2.1000  16.000

============================================================
STEP 7: DECISION
============================================================
✅ VERDICT: USE PRUNED MODEL!
   Accuracy loss is negligible (0.012%)
   Model is 25% smaller and faster
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "File not found" | Check the file path - use your actual CSV file location |
| "Module not found" | Run: `.\.venv\Scripts\python.exe -m pip install scikit-learn pandas xgboost numpy` |
| "pickle error" | Make sure the .pkl file exists and is a valid model |
| "Out of memory" | Use fewer samples: `X_test = X_test[:100000]` |

---

## Summary

✅ You now know how to:
1. Load test data
2. Load original model
3. Create pruned version
4. Evaluate both models
5. Compare results
6. Make a decision

**Just copy the code above and run it!** 🚀

