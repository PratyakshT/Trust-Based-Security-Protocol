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
    """
    if interactions_df.empty:
        return pd.DataFrame()

    # 1. Reputation (Global Feature): Just the mean rating received
    reputation = interactions_df.groupby('provider_id')['rating'].mean().reset_index()
    reputation.rename(columns={'rating': 'reputation_score'}, inplace=True)
    
    # 2. Rating-Trend & Frequency: How they behave as a Requester
    # We now count how many ratings they GAVE to find the spammers
    rating_trend = interactions_df.groupby('requester_id')['rating'].agg(['mean', 'count']).reset_index()
    rating_trend.rename(columns={
        'requester_id': 'provider_id', 
        'mean': 'rating_trend', 
        'count': 'total_interactions' # How many times they attacked
    }, inplace=True)

    # Merge into a single profile dataframe
    user_features = pd.merge(reputation, rating_trend, on='provider_id', how='outer')
    user_features.fillna(0.5, inplace=True) # Default neutral score for missing data
    
    return user_features

def get_or_train_model(features_df):
    """
    Phase 2: Trust-Aggregation.
    """
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as file:
            return pickle.load(file)
            
    print("No existing model found. Training initial MLP...")
    
    # --- Bootstrapping logic for the MVP ---
    def flag_attacker(row):
        # Malicious Recommenders spam bad ratings (trend < 0.2) 
        # and do it repeatedly (total_interactions > 5)
        if row['rating_trend'] < 0.2 and row['total_interactions'] > 5:
            return 1 # Malicious
        return 0 # Legitimate
        
    features_df['is_malicious'] = features_df.apply(flag_attacker, axis=1)
    
    X = features_df[['reputation_score', 'total_interactions', 'rating_trend']]
    y = features_df['is_malicious']
    
    mlp = MLPClassifier(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
    
    if len(y.unique()) > 1:
        mlp.fit(X, y)
        with open(MODEL_PATH, 'wb') as file:
            pickle.dump(mlp, file)
        return mlp
    else:
        print("Not enough diverse data to train yet!")
        return None