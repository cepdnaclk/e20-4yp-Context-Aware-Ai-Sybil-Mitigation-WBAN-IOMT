import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# -----------------------------
# Step 1: Load Dataset
# -----------------------------
# Replace with your CSV dataset path
dataset_path = '/mnt/data/your_dataset.csv'
df = pd.read_csv(dataset_path)

# Example columns: 'MAC', 'ResidualEnergy', 'Label'

# -----------------------------
# Step 2: Initialize parameters
# -----------------------------
FS = [0, 0.2, 0.4, 0.6, 0.8, 1]  # Fuzzy set for trust
TS = 0.05                         # Trust sample increment/decrement
TH = 0.5                           # Trust value threshold
E_n_init = 100                     # Initial energy
N_trusted = []                      # List of trusted nodes
blockchain = []                     # For storing trust values

# -----------------------------
# Step 3: Trust Calculation Function
# -----------------------------
def calculate_trust(mac, residual_energy):
    P = int(mac.replace(':', ''), 16) % len(FS)  # Simplified P = MAC/d
    TV_i = TS if P in FS else 0
    TV_f = TS + TV_i + (residual_energy / E_n_init)
    return TV_f

# -----------------------------
# Step 4: Detection & Isolation
# -----------------------------
def detect_sybil(df):
    detected_labels = []
    
    for index, row in df.iterrows():
        TV_new = calculate_trust(row['MAC'], row['ResidualEnergy'])
        
        if TV_new < TH and row['ResidualEnergy'] < 50:
            # Sybil attack
            detected_labels.append(1)
        else:
            # Legitimate node
            detected_labels.append(0)
        
        # Update blockchain
        blockchain.append({'MAC': row['MAC'], 'TrustValue': TV_new})
    
    return detected_labels

# -----------------------------
# Step 5: Run Detection
# -----------------------------
df['Predicted'] = detect_sybil(df)

# -----------------------------
# Step 6: Calculate Accuracy
# -----------------------------
accuracy = accuracy_score(df['Label'], df['Predicted'])
conf_matrix = confusion_matrix(df['Label'], df['Predicted'])
report = classification_report(df['Label'], df['Predicted'])

print(f"Accuracy: {accuracy*100:.2f}%")
print("Confusion Matrix:")
print(conf_matrix)
print("Classification Report:")
print(report)