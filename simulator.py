# simulator.py
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:8001/api"
NUM_NODES = 50
TOTAL_INTERACTIONS = 500

# Designate the last 10 nodes as attackers, and target node_1
ATTACKERS = [f"node_{i}" for i in range(40, 50)]
TARGET_NODE = "node_1"

def register_nodes():
    print("--- [PHASE 1] Registering 50 IoT Nodes ---")
    for i in range(NUM_NODES):
        node_id = f"node_{i}"
        payload = {
            "node_id": node_id,
            "device_category": random.choice(["sensor", "camera", "smartphone"]),
            "dcc_score": round(random.uniform(0.1, 1.0), 2),
            "elc_score": round(random.uniform(0.1, 1.0), 2),
            "msrc_score": round(random.uniform(0.5, 1.0), 2)
        }
        requests.post(f"{BASE_URL}/register/", json=payload)
    print("Registration Complete.\n")

def simulate_interaction(interaction_id):
    """Simulates a single interaction event in the network."""
    requester = f"node_{random.randint(0, NUM_NODES - 1)}"
    
    # --- MALICIOUS BEHAVIOR (Bad Mouthing Attack) ---
    if requester in ATTACKERS:
        provider = TARGET_NODE
        rating = 0 # Attackers spam fake BAD ratings at the target
        print(f"[ATTACK] {requester} -> {provider} | Rating: {rating}")
        
    # --- LEGITIMATE BEHAVIOR ---
    else:
        provider = f"node_{random.randint(0, NUM_NODES - 1)}"
        while provider == requester: # Don't rate yourself
            provider = f"node_{random.randint(0, NUM_NODES - 1)}"
        # Normal nodes give mostly good ratings (85% of the time)
        rating = random.choices([0, 1], weights=[0.15, 0.85])[0] 
        print(f"[NORMAL] {requester} -> {provider} | Rating: {rating}")

    payload = {
        "requester_id": requester,
        "provider_id": provider,
        "service_id": f"srv_{random.randint(100, 105)}",
        "rating": rating
    }
    
    # Fire asynchronous request to FastAPI
    requests.post(f"{BASE_URL}/interactions/", json=payload)

def run_network_simulation():
    register_nodes()
    
    print(f"--- [PHASE 2] Simulating {TOTAL_INTERACTIONS} Interactions concurrently ---")
    # Spin up 20 parallel threads to blast the FastAPI server
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(simulate_interaction, i) for i in range(TOTAL_INTERACTIONS)]
        for future in as_completed(futures):
            pass # Wait for all to finish
            
    print("\n--- [PHASE 3] Triggering DSL-STM AI Engine ---")
    print("Calculating Multidimensional Trust and hunting for attackers...")
    
    response = requests.get(f"{BASE_URL}/calculate_trust/")
    result = response.json()
    
    print("\n=== SYSTEM REPORT ===")
    print(f"Total Interactions Processed: {result['processed_interactions']}")
    print(f"Malicious Nodes Caught: {len(result['malicious_nodes_detected'])}")
    print(f"Attacker IDs: {result['malicious_nodes_detected']}")

if __name__ == "__main__":
    run_network_simulation()