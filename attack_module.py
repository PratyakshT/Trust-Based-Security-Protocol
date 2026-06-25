from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.models import Model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
import ast
from sklearn.metrics import classification_report

NUM_ATTACK_CLASSES = 5
NUM_INPUTS = 8

# Model Architecture 
input_layer = Input(shape=(NUM_INPUTS,))
hidden_layer = Dense(32, activation='relu')(input_layer)
drop_layer = Dropout(0.2)(hidden_layer)
hidden_layer = Dense(32, activation='relu')(drop_layer)
drop_layer = Dropout(0.2)(hidden_layer)
hidden_layer = Dense(16, activation='relu')(drop_layer)

# Sigmoid is correct for multi-label classification
output_layer = Dense(NUM_ATTACK_CLASSES, activation='sigmoid')(hidden_layer)

model_attack = Model(inputs=input_layer, outputs=output_layer)

# binary_crossentropy treats each of the 5 outputs as an independent True/False prediction
model_attack.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

def train_model(csv_path="interactions_log.csv"):
    try:
        # 1. Load the dataset
        df = pd.read_csv(csv_path)
        
        if len(df) == 0:
            print("Dataset is empty. Please run the simulation first.")
            return

        # We discard the first 30% of the simulation where parameters are still converging from 0.5
        burn_in_percentage = 0.30
        drop_index = int(len(df) * burn_in_percentage)
        
        # Keep only the rows AFTER the drop_index, and reset the index cleanly
        df = df.iloc[drop_index:].reset_index(drop=True)

        print(f"Total interactions simulated: {drop_index + len(df)}")
        print(f"Dropped the first {drop_index} rows (unconverged transient phase).")
        print(f"Loaded highly-converged dataset with {len(df)} samples for training.")

        # 2. Separate features (X) and labels (y)
        X_df = df.drop(['attack_class', 'requester_id', 'provider_id'], axis=1)
        
        # Initialize the scaler and normalize the features
        scaler = StandardScaler()
        X = scaler.fit_transform(X_df.values)
        
        # CSVs save lists as strings (e.g., "[0, 2]"). 
        # This safely converts strings to lists, and wraps rogue integers in a list.
        df['attack_class'] = df['attack_class'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [x])
        )
        y = df['attack_class'].values

        # 3. Convert labels to Multi-hot encoding
        # Explicitly passing the classes ensures the array is always shape (n, 5)
        mlb = MultiLabelBinarizer(classes=[0, 1, 2, 3, 4])
        y_multihot = mlb.fit_transform(y)

        # 4. Split into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_multihot, test_size=0.2, random_state=42
        )

        # 5. Train the model
        print("Starting training...")
        history = model_attack.fit(
            X_train, y_train,
            epochs=20,
            batch_size=32,
            validation_split=0.2,
            verbose=1
        )

        # 6. Evaluate the model on test data
        loss, accuracy = model_attack.evaluate(X_test, y_test, verbose=0)
        print(f"\nTest Accuracy: {accuracy*100:.2f}%")

        # 7. Calculate Precision, Recall, and F1-Score
        y_pred = model_attack.predict(X_test)
        
        # --- PHASE 3: Custom Threshold Tuning ---
        thresholds = np.array([0.5, 0.5, 0.5, 0.5, 0.5]) 
        
        # Apply the array of thresholds
        y_pred_classes = (y_pred > thresholds).astype(int) 
        y_true_classes = y_test # Already multi-hot encoded

        # Calculate metrics globally
        precision = precision_score(y_true_classes, y_pred_classes, average='macro', zero_division=0)
        recall = recall_score(y_true_classes, y_pred_classes, average='macro', zero_division=0)
        f1 = f1_score(y_true_classes, y_pred_classes, average='macro', zero_division=0)

        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")

        # 8. Save the model
        model_attack.save("attack_detection_model.keras")
        print("Model saved to attack_detection_model.keras")
        
        return history

    except FileNotFoundError:
        print(f"Error: {csv_path} not found. Please run the simulation first to generate the dataset.")

if __name__ == "__main__":
    train_model()