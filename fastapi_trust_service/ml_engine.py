import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

MODEL_PATH = "dsl_stm_mlp.pkl"

def extract_multidimensional_features(interactions_df):
    """V7: The Complete Architecture (Includes Rating-Frequency Swarm Defense)"""
    if interactions_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    interactions_df = interactions_df.sort_values('timestamp')

    # 1. BAYESIAN REPUTATION
    reputation_df = interactions_df.groupby('provider_id').agg(
        raw_reputation=('rating', 'mean'), rating_count=('rating', 'count')
    ).reset_index()
    C = interactions_df['rating'].mean()
    m = 15
    reputation_df['reputation_score'] = ((reputation_df['rating_count'] * reputation_df['raw_reputation']) + (m * C)) / (reputation_df['rating_count'] + m)
    reputation_df.rename(columns={'provider_id': 'node_id'}, inplace=True)

    # 2. FLUCTUATION & TREND
    fluctuation_df = interactions_df.groupby('provider_id')['rating'].std().reset_index()
    fluctuation_df.rename(columns={'provider_id': 'node_id', 'rating': 'fluctuation_score'}, inplace=True)
    fluctuation_df['fluctuation_score'].fillna(0.0, inplace=True)

    trend_df = interactions_df.groupby('requester_id')['rating'].mean().reset_index()
    trend_df.rename(columns={'requester_id': 'node_id', 'rating': 'rating_trend_score'}, inplace=True)

    # 3. VECTOR ALIGNMENT (Credibility)
    cred_merge = pd.merge(
        interactions_df[['requester_id', 'provider_id', 'rating']],
        reputation_df.rename(columns={'node_id': 'provider_id'}), on='provider_id'
    )
    def get_cosine_sim(group):
        user_vec = group['rating'].values.reshape(1, -1)
        global_vec = group['reputation_score'].values.reshape(1, -1)
        if np.sum(user_vec) == 0 and np.sum(global_vec) == 0: return 1.0 
        if np.sum(user_vec) == 0 or np.sum(global_vec) == 0: return 0.0 
        return float(cosine_similarity(user_vec, global_vec)[0][0])

    credibility_df = cred_merge.groupby('requester_id').apply(get_cosine_sim).reset_index(name='credibility_score')
    credibility_df.rename(columns={'requester_id': 'node_id'}, inplace=True)

    # 4. SCALED SERVICE TELEMETRY
    service_df = interactions_df.groupby('provider_id').agg(
        avg_response_time=('response_time_ms', 'mean'), avg_latency=('latency_ms', 'mean')
    ).reset_index()
    service_df.rename(columns={'provider_id': 'node_id'}, inplace=True)
    service_df['avg_response_time'] = service_df['avg_response_time'] / 1000.0 
    service_df['avg_latency'] = service_df['avg_latency'] / 100.0

    # 5. CONTEXTUAL TRUST (Discriminatory Bias)
    bias_series = interactions_df.groupby('provider_id').apply(lambda x: x['social_similarity_score'].corr(x['rating']))
    bias_df = bias_series.reset_index(name='discriminatory_bias')
    bias_df['discriminatory_bias'].fillna(0.0, inplace=True)
    bias_df.rename(columns={'provider_id': 'node_id'}, inplace=True)

    # ---> 6. RATING-FREQUENCY (The Swarm Defense) <---
    total_req = interactions_df.groupby('requester_id').size().reset_index(name='total_requests')
    pair_req = interactions_df.groupby(['requester_id', 'provider_id']).size().reset_index(name='pair_requests')
    freq_df = pd.merge(pair_req, total_req, on='requester_id')
    
    # What percentage of their total traffic goes to a single target?
    freq_df['rating_frequency'] = freq_df['pair_requests'] / freq_df['total_requests']
    
    # Extract the absolute maximum targeted frequency for each node
    max_freq_df = freq_df.groupby('requester_id')['rating_frequency'].max().reset_index(name='max_rating_frequency')
    max_freq_df.rename(columns={'requester_id': 'node_id'}, inplace=True)

    # 7. COMPILE THE MASTER 8-PARAMETER MATRIX
    node_profiles = pd.merge(reputation_df[['node_id', 'reputation_score']], fluctuation_df, on='node_id', how='outer')
    node_profiles = pd.merge(node_profiles, trend_df, on='node_id', how='outer')
    node_profiles = pd.merge(node_profiles, credibility_df, on='node_id', how='outer')
    node_profiles = pd.merge(node_profiles, service_df, on='node_id', how='outer')
    node_profiles = pd.merge(node_profiles, bias_df, on='node_id', how='outer')
    node_profiles = pd.merge(node_profiles, max_freq_df, on='node_id', how='outer') # Inject Frequency
    
    node_profiles.fillna({
        'reputation_score': C, 'fluctuation_score': 0.0, 'rating_trend_score': C, 
        'credibility_score': 0.5, 'avg_response_time': 0.200, 'avg_latency': 0.30,
        'discriminatory_bias': 0.0, 'max_rating_frequency': 0.0
    }, inplace=True)

    return node_profiles, pd.DataFrame()

def get_or_train_model(profiles_df):
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as file: return pickle.load(file)
            
    print("Training Final V7 Swarm-Resistant Engine...")
    
    def flag_attacker(row):
        # NEW RULE: If you spend > 40% of your total network traffic rating one node, you are a Swarm Attacker
        if row['max_rating_frequency'] > 0.40 or row['credibility_score'] < 0.3: return 1 
        if row['fluctuation_score'] > 0.45 or row['avg_response_time'] > 0.45: return 2
        if row['discriminatory_bias'] > 0.7: return 3 
        return 0 
        
    profiles_df['is_malicious'] = profiles_df.apply(flag_attacker, axis=1)
    
    # Input matrix now has 8 fully baked features
    X = profiles_df[['reputation_score', 'fluctuation_score', 'rating_trend_score', 'credibility_score', 'avg_response_time', 'avg_latency', 'discriminatory_bias', 'max_rating_frequency']]
    y = profiles_df['is_malicious']
    
    mlp = MLPClassifier(hidden_layer_sizes=(20, 15), max_iter=3000, random_state=42)
    if len(y.unique()) > 1:
        mlp.fit(X, y)
        with open(MODEL_PATH, 'wb') as file: pickle.dump(mlp, file)
        return mlp
    return None