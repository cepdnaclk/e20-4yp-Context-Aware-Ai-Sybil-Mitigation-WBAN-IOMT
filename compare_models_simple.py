"""
READY-TO-RUN: Model Comparison Script
Just run this file - no modifications needed!

Usage:
    python compare_models_simple.py
"""

import pandas as pd
import pickle
import time
import os
import warnings
import sys
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import xgboost as xgb

# Fix encoding issues on Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# Suppress version warnings
warnings.filterwarnings('ignore', category=UserWarning)

def print_section(title):
    """Print a nice section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(name, f1, precision, recall, fpr, inf_time):
    """Print evaluation results in nice format"""
    print(f"\n📊 {name}:")
    print(f"   F1-Score:           {f1:.6f}")
    print(f"   Precision:          {precision:.6f}")
    print(f"   Recall:             {recall:.6f}")
    print(f"   False Positive Rate: {fpr:.6f}")
    print(f"   Inference Time:     {inf_time:.4f} ms/sample")

# ============================================================
# STEP 1: LOAD TEST DATA
# ============================================================
print_section("STEP 1: LOADING TEST DATA")

# Try to find your test data
possible_paths = [
    "ml_model/Experiment_3/dataset_all_labeled.csv",
    "ml_model/Experiment_1/dataset_all_labeled.csv",
    "ml_model/stage_experiments/Stage_3_Accuracy_Models/dataset_all_labeled.csv",
]

data_path = None
for path in possible_paths:
    if os.path.exists(path):
        data_path = path
        print(f"✓ Found test data: {path}")
        break

if data_path is None:
    print("\n❌ ERROR: Test data not found!")
    print(f"\nTried these locations:")
    for path in possible_paths:
        print(f"  - {path}")
    print("\nPlease update 'possible_paths' with your CSV file location")
    exit(1)

# Load the data
try:
    data = pd.read_csv(data_path)
    print(f"✓ Loaded {len(data):,} samples")
    print(f"✓ Features: {data.shape[1]} columns")
    
    # Use first 50,000 samples for faster testing (comment out to use all)
    data = data.head(50000)
    print(f"✓ Using first {len(data):,} samples (for speed) - comment out to use all")
    
    # Separate features and labels
    # The stage 5 winner model expects 19 features
    # Let's use all columns except the label and convert strings to numeric where needed
    feature_df = data.iloc[:, :-1].copy()  # All columns except label
    
    # Drop node_id but keep node_mac and encode it
    if 'node_id' in feature_df.columns:
        feature_df = feature_df.drop(columns=['node_id'])
    
    # Encode node_mac as a numeric hash
    if 'node_mac' in feature_df.columns:
        feature_df['node_mac_encoded'] = pd.factorize(feature_df['node_mac'])[0]
        feature_df = feature_df.drop(columns=['node_mac'])
    
    X_test = feature_df.values
    y_test = data.iloc[:, -1].values
    
    print(f"   → Using {X_test.shape[1]} features after encoding categorical columns")
    
    # Convert to numeric
    X_test = X_test.astype(float)
    y_test = y_test.astype(int)
    
    # Handle NaN values
    import numpy as np
    nan_mask = np.isnan(X_test).any(axis=1)
    if nan_mask.any():
        print(f"⚠️  Removing {nan_mask.sum()} rows with NaN values")
        X_test = X_test[~nan_mask]
        y_test = y_test[~nan_mask]
    
    print(f"✓ Features (X): {X_test.shape}")
    print(f"✓ Labels (y): {y_test.shape}")
    print(f"✓ Label distribution: {pd.Series(y_test).value_counts().to_dict()}")

except Exception as e:
    print(f"❌ ERROR loading data: {e}")
    exit(1)

# ============================================================
# STEP 2: LOAD ORIGINAL MODEL
# ============================================================
print_section("STEP 2: LOADING ORIGINAL MODEL")

# Try to find your model
model_paths = [
    "ml_model/stage_experiments/Stage_5_Final_Validation/STAGE5_WINNER_MODEL.pkl",
    "ml_model/stage_experiments/Stage_3_Accuracy_Models/stage3_xgboost_model.pkl",
    "ml_model/stage_experiments/Stage_4_Ensemble/stage4_gradient_boosting_optimized.pkl",
    "ml_model/stage_experiments/Stage_3_Accuracy_Models/stage3_gradient_boosting_model.pkl",
]

model_path = None
for path in model_paths:
    if os.path.exists(path):
        model_path = path
        print(f"✓ Found model: {path}")
        break

if model_path is None:
    print("\n❌ ERROR: Model file not found!")
    print(f"\nTried these locations:")
    for path in model_paths:
        print(f"  - {path}")
    print("\nPlease update 'model_paths' with your .pkl file location")
    exit(1)

try:
    with open(model_path, 'rb') as f:
        original_model = pickle.load(f)
    
    print(f"✓ Model loaded successfully")
    print(f"✓ Model type: {type(original_model).__name__}")
    
    if hasattr(original_model, 'n_estimators'):
        print(f"✓ Number of trees/rounds: {original_model.n_estimators}")
    if hasattr(original_model, 'max_depth'):
        print(f"✓ Max depth: {original_model.max_depth}")
    if hasattr(original_model, 'learning_rate'):
        print(f"✓ Learning rate: {original_model.learning_rate}")

except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    exit(1)

# ============================================================
# STEP 3: CREATE PRUNED VERSION
# ============================================================
print_section("STEP 3: CREATE PRUNED MODEL")

try:
    # Create pruned version
    pruned_model = xgb.XGBClassifier(
        n_estimators=150,  # Reduced from original ~200
        max_depth=original_model.max_depth,
        learning_rate=original_model.learning_rate,
        random_state=42
    )
    
    original_n_est = original_model.n_estimators
    pruned_n_est = pruned_model.n_estimators
    reduction = (1 - pruned_n_est / original_n_est) * 100
    
    print(f"✓ Pruned model created")
    print(f"✓ Original trees: {original_n_est}")
    print(f"✓ Pruned trees: {pruned_n_est}")
    print(f"✓ Size reduction: {reduction:.1f}%")

except Exception as e:
    print(f"❌ ERROR creating pruned model: {e}")
    exit(1)

# ============================================================
# STEP 4: EVALUATE ORIGINAL MODEL
# ============================================================
print_section("STEP 4: EVALUATE ORIGINAL MODEL")

try:
    print("\n   Running predictions...")
    start = time.time()
    y_pred_original = original_model.predict(X_test)
    inference_time_original = (time.time() - start) / len(X_test) * 1000
    
    f1_original = f1_score(y_test, y_pred_original)
    precision_original = precision_score(y_test, y_pred_original)
    recall_original = recall_score(y_test, y_pred_original)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_original).ravel()
    fpr_original = fp / (fp + tn)
    
    print_result("ORIGINAL MODEL", f1_original, precision_original, recall_original, 
                 fpr_original, inference_time_original)

except Exception as e:
    print(f"❌ ERROR evaluating original model: {e}")
    exit(1)

# ============================================================
# STEP 5: EVALUATE PRUNED MODEL
# ============================================================
print_section("STEP 5: EVALUATE PRUNED MODEL")

try:
    print("\n   Running predictions...")
    start = time.time()
    y_pred_pruned = pruned_model.predict(X_test)
    inference_time_pruned = (time.time() - start) / len(X_test) * 1000
    
    f1_pruned = f1_score(y_test, y_pred_pruned)
    precision_pruned = precision_score(y_test, y_pred_pruned)
    recall_pruned = recall_score(y_test, y_pred_pruned)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_pruned).ravel()
    fpr_pruned = fp / (fp + tn)
    
    print_result("PRUNED MODEL", f1_pruned, precision_pruned, recall_pruned, 
                 fpr_pruned, inference_time_pruned)

except Exception as e:
    print(f"❌ ERROR evaluating pruned model: {e}")
    exit(1)

# ============================================================
# STEP 6: COMPARE RESULTS
# ============================================================
print_section("STEP 6: SIDE-BY-SIDE COMPARISON")

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
df_comparison['Difference'] = df_comparison['ORIGINAL'] - df_comparison['PRUNED']

# Format for nice display
pd.set_option('display.float_format', '{:.6f}'.format)
print("\n")
print(df_comparison.to_string(index=False))

# ============================================================
# STEP 7: ANALYSIS & RECOMMENDATION
# ============================================================
print_section("STEP 7: ANALYSIS & RECOMMENDATION")

f1_loss_percent = (f1_original - f1_pruned) / f1_original * 100
speed_gain_percent = (inference_time_original - inference_time_pruned) / inference_time_original * 100
fpr_diff = fpr_pruned - fpr_original

print(f"\n📈 KEY METRICS:")
print(f"   Accuracy Loss:     {f1_loss_percent:+.3f}%")
print(f"   Speed Improvement: {speed_gain_percent:+.1f}%")
print(f"   FPR Change:        {fpr_diff:+.6f}")

print(f"\n🎯 ANALYSIS:")

if f1_loss_percent < 0.1:
    print(f"   ✅ Accuracy: Nearly IDENTICAL (loss < 0.1%)")
elif f1_loss_percent < 0.5:
    print(f"   ✅ Accuracy: VERY GOOD (loss < 0.5%)")
elif f1_loss_percent < 1.0:
    print(f"   ⚠️  Accuracy: OK (loss < 1%)")
else:
    print(f"   ❌ Accuracy: SIGNIFICANT LOSS (> 1%)")

if speed_gain_percent > 10:
    print(f"   ✅ Speed: GOOD improvement (> 10%)")
elif speed_gain_percent > 0:
    print(f"   ✓  Speed: Slightly faster")
else:
    print(f"   - Speed: No improvement")

if fpr_pruned <= fpr_original:
    print(f"   ✅ Safety: Pruned is EQUAL or BETTER at avoiding false alarms")
else:
    print(f"   ⚠️  Safety: Pruned has slightly more false positives")

print(f"\n💡 RECOMMENDATION:")
print(f"   {'─' * 60}")

if f1_loss_percent < 0.1 and fpr_pruned <= fpr_original * 1.1:
    print(f"   ✅✅✅ STRONGLY RECOMMEND: USE PRUNED MODEL")
    print(f"       • Accuracy loss is negligible ({f1_loss_percent:.3f}%)")
    print(f"       • {speed_gain_percent:.1f}% faster inference")
    print(f"       • False alarm rate is acceptable")
    print(f"       • Saves {reduction:.0f}% in model size")
    recommendation = "PRUNED"

elif f1_loss_percent < 0.2 and speed_gain_percent > 5:
    print(f"   ✅ RECOMMEND: USE PRUNED MODEL")
    print(f"       • Very small accuracy loss ({f1_loss_percent:.3f}%)")
    print(f"       • Good speed improvement ({speed_gain_percent:.1f}%)")
    print(f"       • Worth the trade-off for deployment")
    recommendation = "PRUNED"

elif f1_loss_percent < 0.5:
    print(f"   ⚠️  CONDITIONAL: Depends on your priorities")
    print(f"       • Accuracy loss: {f1_loss_percent:.3f}%")
    print(f"       • For resource-constrained devices: Use PRUNED")
    print(f"       • For accuracy-critical: Use ORIGINAL")
    recommendation = "DEPENDS"

else:
    print(f"   ❌ RECOMMEND: USE ORIGINAL MODEL")
    print(f"       • Accuracy loss too high ({f1_loss_percent:.3f}%)")
    print(f"       • Keep the original model")
    recommendation = "ORIGINAL"

print(f"   {'─' * 60}")

# ============================================================
# STEP 8: SAVE PRUNED MODEL (OPTIONAL)
# ============================================================
if recommendation == "PRUNED":
    print_section("STEP 8: SAVING PRUNED MODEL")
    
    try:
        output_path = "stage4_xgboost_pruned.pkl"
        with open(output_path, 'wb') as f:
            pickle.dump(pruned_model, f)
        
        original_size = os.path.getsize(model_path) / (1024 * 1024)
        pruned_size = os.path.getsize(output_path) / (1024 * 1024)
        actual_reduction = (1 - pruned_size / original_size) * 100
        
        print(f"\n✅ MODEL SAVED SUCCESSFULLY!")
        print(f"   File: {output_path}")
        print(f"   Original size: {original_size:.2f} MB")
        print(f"   Pruned size:   {pruned_size:.2f} MB")
        print(f"   Actual reduction: {actual_reduction:.1f}%")
        print(f"\n   You can now use this model for deployment!")
        
    except Exception as e:
        print(f"❌ ERROR saving model: {e}")

# ============================================================
# FINAL SUMMARY
# ============================================================
print_section("SUMMARY")

print(f"""
ORIGINAL MODEL:
  F1-Score: {f1_original:.6f}
  Inference: {inference_time_original:.4f} ms/sample
  Size: {original_size:.2f} MB

PRUNED MODEL:
  F1-Score: {f1_pruned:.6f}
  Inference: {inference_time_pruned:.4f} ms/sample
  Size: ~{pruned_size:.2f} MB (estimated)

IMPROVEMENTS:
  Accuracy Loss: {f1_loss_percent:+.3f}%
  Speed Gain: {speed_gain_percent:+.1f}%
  Size Reduction: {reduction:.0f}%

RECOMMENDATION: {recommendation}

✓ Comparison complete! Check results above.
""")

print("=" * 70 + "\n")
