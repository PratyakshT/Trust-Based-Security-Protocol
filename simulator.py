import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:8001/api"
NUM_NODES = 50
TOTAL_INTERACTIONS = 2500

# Adversarial Matrix Configurations
BAD_MOUTHERS = [f"node_{i}" for i in range(40, 50)]
ON_OFF_ATTACKERS = [f"node_{i}" for i in range(30, 40)]
DISCRIMINATORY_ATTACKERS = [f"node_{i}" for i in range(20, 30)]
TARGET_NODE = "node_1"

def register_nodes_v3():
    print("--- [PHASE 1] Registering 50 Discrete Hardware SIoT Nodes ---")
    categories = ["sensor", "actuator", "camera", "gateway", "smartphone"]
    for i in range(NUM_NODES):
        node_id = f"node_{i}"
        payload = {
            "node_id": node_id,
            "device_category": random.choice(categories),
            "dcc_score": float(random.choice([0, 0.5, 1])),
            "elc_score": float(random.choice([0, 0.25, 0.5, 1])),
            "msrc_score": float(random.choice([0, 0.25, 0.5, 1]))
        }
        requests.post(f"{BASE_URL}/register/", json=payload)
    print("Discrete Node Profiles Registered.\n")

def simulate_telemetry_interaction(idx):
    requester = f"node_{random.randint(0, NUM_NODES - 1)}"
    latency = round(random.uniform(10.0, 50.0), 2)
    response_time = round(random.uniform(100.0, 300.0), 2)
    
    # Generate the simulated Jaccard contextual score for this interaction
    social_sim = round(random.uniform(0.0, 1.0), 2)
    
    # --- THREAT VECTOR 3: Discriminatory Attackers ---
    # The provider is the attacker. They look at who is requesting the service.
    provider_pool = [n for n in range(NUM_NODES) if f"node_{n}" != requester]
    provider = f"node_{random.choice(provider_pool)}"
    
    if provider in DISCRIMINATORY_ATTACKERS:
        if social_sim > 0.5:
            # Treats "friends" perfectly
            rating = 1 
        else:
            # Sabotages "strangers"
            rating = 0
            response_time += 500.0 
            
    # --- THREAT VECTOR 1: Bad Mouthing ---
    elif requester in BAD_MOUTHERS:
        provider = TARGET_NODE
        rating = 0
    
    # --- THREAT VECTOR 2: On-Off Attackers ---
    elif requester in ON_OFF_ATTACKERS:
        provider = requester 
        requester = f"node_{random.randint(0, 19)}" 
        if idx < (TOTAL_INTERACTIONS // 2):
            rating = 1
        else:
            rating = 0
            response_time += 600.0
            
    # --- LEGITIMATE INFRASTRUCTURE ---
    else:
        rating = random.choices([0, 1], weights=[0.05, 0.95])[0]
        if rating == 0:
            response_time += 400.0

    payload = {
        "requester_id": requester,
        "provider_id": provider,
        "service_id": f"service_id_{random.randint(1, 5)}",
        "rating": rating,
        "response_time_ms": response_time,
        "latency_ms": latency,
        "social_similarity_score": social_sim
    }
    requests.post(f"{BASE_URL}/interactions/", json=payload)
def run_upgraded_simulation():
    register_nodes_v3()
    print(f"--- [PHASE 2] Simulating {TOTAL_INTERACTIONS} Multi-Threat Telemetry Invocations ---")
    
    # Execute sequentially or with a controlled pool to preserve chronological order for time-series math
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(simulate_telemetry_interaction, i) for i in range(TOTAL_INTERACTIONS)]
        for future in as_completed(futures):
            pass

    print("\n--- [PHASE 3] Invoking Multi-Dimensional Trust Aggregator ---")
    response = requests.get(f"{BASE_URL}/calculate_trust/")
    
    if response.status_code == 200:
        result = response.json()
        print("\n" + "="*25 + " ENHANCED THREAT REPORT " + "="*25)
        print(f"Telemetry Packets Processed : {result.get('processed_interactions')}")
        print(f"Total Unique Nodes Tracked : {result.get('analyzed_nodes')}")
        print(f"Malicious Attackers Caught : {len(result.get('malicious_nodes_detected', []))}")
        print(f"Identified Adversary IDs   : {result.get('malicious_nodes_detected')}")
        print("="*74)
    else:
        print(f"Pipeline Interrupted: {response.text}")

if __name__ == "__main__":
    run_upgraded_simulation()