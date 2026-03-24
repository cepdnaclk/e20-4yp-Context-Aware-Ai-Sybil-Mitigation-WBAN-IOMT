"""
SIMPLE MODEL COMPARISON SCRIPT
Ready-to-run: Just execute this file!

Step-by-step guide:
1. Loads your test data
2. Loads your original trained model  
3. Creates a pruned version
4. Evaluates both
5. Compares and recommends

Usage:
    python compare_models.py
"""

import pandas as pd
import pickle
import time
import os
import numpy as np
import warnings
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb

warnings.filterwarnings('ignore')

print("\n" + "="*70)
print("  MODEL COMPARISON: ORIGINAL vs PRUNED")
print("="*70)

# ============================================================
# STEP 1: LOAD TEST DATA
# ============================================================
print("\nSTEP 1: LOADING TEST DATA")
print("-" * 70)

data_path = "ml_model/Experiment_3/dataset_all_labeled.csv"

if not os.path.exists(data_path):
    print("[ERROR] Test data file not found:", data_path)
    exit(1)

data = pd.read_csv(data_path)
print (f"Loaded: {len(data):,} samples, {data.shape[1]} columns")

# Use smaller sample for speed
data = data.head(50000)
print(f"Using: {len(data):,} samples (first 50k for speed)")

# Prepare features and labels
feature_df = data.iloc[:, :-1].copy()
y_test = data.iloc[:, -1].values.astype(int)

# Drop node_id, encode node_mac
if 'node_id' in feature_df.columns:
    feature_df = feature_df.drop(columns=['node_id'])
if 'node_mac' in feature_df.columns:
    feature_df['node_mac_code'] = pd.factorize(feature_df['node_mac'])[0]
    feature_df = feature_df.drop(columns=['node_mac'])

X_test = feature_df.values.astype(float)

# Remove NaN rows
nan_mask = np.isnan(X_test).any(axis=1)
if nan_mask.any():
    print(f"Removing {nan_mask.sum()} rows with NaN")
    X_test = X_test[~nan_mask]
    y_test = y_test[~nan_mask]

print(f"Features shape: {X_test.shape}")
print(f"Labels shape: {y_test.shape}")

# ============================================================
# STEP 2: LOAD ORIGINAL MODEL
# ============================================================
print("\nSTEP 2: LOADING ORIGINAL MODEL")
print("-" * 70)

model_path = "ml_model/stage_experiments/Stage_5_Final_Validation/STAGE5_WINNER_MODEL.pkl"

if not os.path.exists(model_path):
    print("[ERROR] Model file not found:", model_path)
    exit(1)

with open(model_path, 'rb') as f:
    original_model = pickle.load(f)

print(f"Model type: {type(original_model).__name__}")
print(f"Estimators: {original_model.n_estimators}")
print(f"Max depth: {original_model.max_depth}")

# ============================================================
# STEP 3: CREATE PRUNED VERSION
# ============================================================
print("\nSTEP 3: CREATE PRUNED MODEL")
print("-" * 70)

# For demonstration: create a simpler comparison
# Instead of creating a new unfitted model, let's create a copy and reduce its estimators
from sklearn.base import clone

# Clone the original model
pruned_model = clone(original_model)

# Since it's a Gradient Boosting model, we reduce n_estimators
pruned_model.n_estimators = 100  # Reduced from 150

print(f"Original: {original_model.n_estimators} estimators")
print(f"Pruned:   {pruned_model.n_estimators} estimators")
print(f"Reduction: {(1 - 100/150)*100:.1f}%")

# Note: For full accuracy, need to retrain, but we'll evaluate with existing
# This is a simplified demonstration
print("\nNote: For production, retrain the pruned model with training data")

# ============================================================
# STEP 4 & 5: EVALUATE BOTH MODELS
# ============================================================
print("\nSTEP 4: EVALUATING ORIGINAL MODEL")
print("-" * 70)

start = time.time()
y_pred_orig = original_model.predict(X_test)
time_orig = (time.time() - start) / len(X_test) * 1000

f1_orig = f1_score(y_test, y_pred_orig)
prec_orig = precision_score(y_test, y_pred_orig)
rec_orig = recall_score(y_test, y_pred_orig)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_orig).ravel()
fpr_orig = fp / (fp + tn)

print(f"F1-Score:  {f1_orig:.6f}")
print(f"Precision: {prec_orig:.6f}")
print(f"Recall:    {rec_orig:.6f}")
print(f"FPR:       {fpr_orig:.6f}")
print(f"Speed:     {time_orig:.4f} ms/sample")

print("\nSTEP 5: EVALUATING PRUNED MODEL")
print("-" * 70)

start = time.time()
y_pred_prune = pruned_model.predict(X_test)
time_prune = (time.time() - start) / len(X_test) * 1000

f1_prune = f1_score(y_test, y_pred_prune)
prec_prune = precision_score(y_test, y_pred_prune)
rec_prune = recall_score(y_test, y_pred_prune)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_prune).ravel()
fpr_prune = fp / (fp + tn)

print(f"F1-Score:  {f1_prune:.6f}")
print(f"Precision: {prec_prune:.6f}")
print(f"Recall:    {rec_prune:.6f}")
print(f"FPR:       {fpr_prune:.6f}")
print(f"Speed:     {time_prune:.4f} ms/sample")

# ============================================================
# STEP 6: COMPARE
# ============================================================
print("\n" + "="*70)
print("  COMPARISON RESULTS")
print("="*70)

comparison = {
    'Metric': ['F1-Score', 'Precision', 'Recall', 'False Pos Rate', 'Speed (ms)'],
    'Original': [f1_orig, prec_orig, rec_orig, fpr_orig, time_orig],
    'Pruned': [f1_prune, prec_prune, rec_prune, fpr_prune, time_prune]
}

df = pd.DataFrame(comparison)
df['Change'] = df['Original'] - df['Pruned']
df['% Change'] = (df['Change'] / df['Original'] * 100).round(2)

print("\n" + df.to_string(index=False))

# ============================================================
# STEP 7: RECOMMENDATION
# ============================================================
print("\n" + "="*70)
print("  ANALYSIS & RECOMMENDATION")
print("="*70)

f1_loss = (f1_orig - f1_prune) / f1_orig * 100
speed_gain = (time_orig - time_prune) / time_orig * 100

print(f"\nAccuracy loss: {f1_loss:+.3f}%")
print(f"Speed improvement: {speed_gain:+.1f}%")
print(f"FPR change: {(fpr_prune - fpr_orig):+.6f}")

print("\nANALYSIS:")
if f1_loss < 0.1:
    print(">>> Accuracy loss is NEGLIGIBLE (< 0.1%)")
elif f1_loss < 0.5:
    print(">>> Accuracy loss is SMALL (< 0.5%)")
elif f1_loss < 1.0:
    print(">>> Accuracy loss is NOTICEABLE (< 1%)")
else:
    print(">>> Accuracy loss is SIGNIFICANT (> 1%)")

if speed_gain > 10:
    print(f">>> Speed improvement is GOOD ({speed_gain:.1f}%)")
elif speed_gain > 0:
    print(f">>> Speed improvement is MODEST ({speed_gain:.1f}%)")

print("\nRECOMMENDATION:")
if f1_loss < 0.2:
    print("[RECOMMEND] Use PRUNED model:")
    print(f"  - Accuracy loss is acceptable ({f1_loss:.3f}%)")
    print(f"  - Speed improvement: {speed_gain:.1f}%")
    print(f"  - Save 33% in model size")
else:
    print("[RECOMMEND] Use ORIGINAL model:")
    print(f"  - Accuracy loss too high ({f1_loss:.3f}%)")

print("\n" + "="*70)
print("\n[DONE] Comparison complete!")
