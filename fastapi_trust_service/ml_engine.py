# ml_engine.py
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
import pickle
import os

MODEL_PATH = "dsl_stm_mlp.pkl"

def extract_trust_features(interactions_df):
    """
    Phase 1: Trust-Composition.
    Extracts Global and Local features from the raw interaction history.
    """
    if interactions_df.empty:
        return pd.DataFrame()

    # 1. Reputation (Global Feature): Ratio of good ratings / total interactions received
    reputation = interactions_df.groupby('provider_id')['rating'].agg(['mean', 'count']).reset_index()
    reputation.rename(columns={'mean': 'reputation_score', 'count': 'total_interactions'}, inplace=True)
    
    # 2. Rating-Trend (Global Feature): Is the user generally optimistic or a spammer?
    rating_trend = interactions_df.groupby('requester_id')['rating'].apply(lambda x: x.mean()).reset_index()
    rating_trend.rename(columns={'requester_id': 'provider_id', 'rating': 'rating_trend'}, inplace=True)

    # Merge into a single profile dataframe
    user_features = pd.merge(reputation, rating_trend, on='provider_id', how='outer')
    user_features.fillna(0.5, inplace=True) # Default neutral score for missing data
    
    return user_features

def get_or_train_model(features_df):
    """
    Phase 2: Trust-Aggregation.
    Loads the serialized MLP or trains a new one if it doesn't exist.
    """
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as file:
            return pickle.load(file)
            
    print("No existing model found. Training initial MLP...")
    
    # --- Bootstrapping logic for the MVP ---
    # To train the AI, we simulate "Ground Truth" for malicious behavior.
    # An attacker spamming bad ratings will have a trend < 0.1 and high interaction count.
    def flag_attacker(row):
        if (row['rating_trend'] < 0.2 or row['rating_trend'] > 0.9) and row['total_interactions'] > 5:
            return 1 # Malicious
        return 0 # Legitimate
        
    features_df['is_malicious'] = features_df.apply(flag_attacker, axis=1)
    
    X = features_df[['reputation_score', 'total_interactions', 'rating_trend']]
    y = features_df['is_malicious']
    
    # The Multi-Layer Perceptron architecture specified in the paper
    mlp = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
    
    # Only train if we actually have variations in our data (both good and bad nodes)
    if len(y.unique()) > 1:
        mlp.fit(X, y)
        with open(MODEL_PATH, 'wb') as file:
            pickle.dump(mlp, file)
        return mlp
    else:
        return None # Not enough diverse data to train yet