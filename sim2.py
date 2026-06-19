import random
import requests

BASE_URL = "http://127.0.0.1:8001/api"

NUM_USERS = 30
NUM_DEVICES = 10
NUM_SERVICES = 10
TOTAL_INTERACTIONS = 500
INTERACTION_THRESHOLD_FOR_OSA = 10
SIMILARITY_THRESHOLD_FOR_DA = 0.3

BAD_MOUTHERS_OR_BALLOT_STUFFERS={21,22,23,24}
DISCRIMINATORY_ATTACKERS={25,26}
ON_OFF_ATTACKERS={27,28}
OPORTUNISTIC_SERVICE_ATTACKERS={29,30}

MALICIOUS = BAD_MOUTHERS_OR_BALLOT_STUFFERS | DISCRIMINATORY_ATTACKERS | ON_OFF_ATTACKERS | OPORTUNISTIC_SERVICE_ATTACKERS

def initialize_dimensions():
    print("--- [PHASE 0] Registering Users, Devices, and Services via FastAPI ---")
    
    # Define a pool of contextual properties
    properties_pool = [
        "Delhi", "NOIDA", "Gurgaon", "Mumbai", "Bangalore",
        "Music", "Sports", "Dance", "Gaming", "Reading",
        "AI", "Cybersecurity", "IoT", "Blockchain", "Art"
    ]
    
    # Generate random point subsets for each user for Jaccard Similarity
    user_points = {}
    for i in range(1, NUM_USERS+1):
        # randomly assign a subset of contextual properties to each user
        k = random.randint(3, 7) 
        user_points[i] = random.sample(properties_pool, k)

    print("User Point Subsets Generated for Jaccard Similarity:")
    for user_id, points in user_points.items():
        print(f"  User {user_id}: {set(points)}")
        
    try:
        payload = {"user_points": user_points}
        response = requests.post(f"{BASE_URL}/init_dimensions/", json=payload)
        response.raise_for_status()
        print("Success:", response.json())
        print("Base Dimensions & NodeRelationships Registered.\n")
    except requests.exceptions.RequestException as e:
        print(f"Failed to initialize dimensions: {e}")

def simulate_interaction():
    # Use integer IDs 1 to 10 for database relations
    requester_id = random.randint(1, NUM_USERS)

    provider_pool = [n for n in range(1, NUM_USERS + 1) if n != requester_id]
    provider_id = random.choice(provider_pool)

    prov_device = random.randint(1, NUM_DEVICES)
    prov_service = random.randint(1, NUM_SERVICES)

    provider = requests.get(f"{BASE_URL}/user/{provider_id}").json()
    requester = requests.get(f"{BASE_URL}/user/{requester_id}").json()
    common = requests.get(f"{BASE_URL}/NodeRelations/{requester_id}/{provider_id}").json()

    if provider_id in OPORTUNISTIC_SERVICE_ATTACKERS:
        curr_interactions = provider["total_interaction_provider"]
        if curr_interactions>INTERACTION_THRESHOLD_FOR_OSA:
            quality_provided = random.uniform(0,0.15)
        else:
            quality_provided = random.uniform(0.85,1.0)

    elif provider_id in ON_OFF_ATTACKERS:
        prev_qos_provided=provider["prev_qos_provided"]
        if prev_qos_provided < 0.2:                
            quality_provided=random.uniform(0.85,1.0)
        else:
            quality_provided=random.uniform(0,0.15)

    elif provider_id in BAD_MOUTHERS_OR_BALLOT_STUFFERS | DISCRIMINATORY_ATTACKERS:     # remove it later as a BMA user might provide good service to maintain reputation
        quality_provided=random.uniform(0,0.15)
    
    else:
        quality_provided=random.uniform(0.85,1.0)


    if requester_id in BAD_MOUTHERS_OR_BALLOT_STUFFERS:
        if provider_id in MALICIOUS:
            rating_received=random.uniform(0.85,1.0)
        else:
            rating_received=random.uniform(0,0.15)

    elif requester_id in DISCRIMINATORY_ATTACKERS:
        sim = common["similarity"]

        if sim>SIMILARITY_THRESHOLD_FOR_DA:
            rating_received = random.uniform(0.85,1.0)
        else:
            rating_received = random.uniform(0,0.15)

    else:
        rating_received = max(0,random.uniform(quality_provided - 0.1, quality_provided + 0.1))

    payload = {
        "requester_id": requester_id,
        "provider_id": provider_id,
        "quality_of_service_provided": round(quality_provided, 2),
        "rating_received": round(rating_received, 2)
    }

    try:
        response = requests.post(f"{BASE_URL}/interactions/", json=payload)
        response.raise_for_status()
        print(f"Interaction Logged | Requester: {requester_id} -> Provider: {provider_id} | Quality: {quality_provided:.2f} | Rating: {rating_received:.2f}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to log interaction: {e}")

    trust_payload = {
        "requester_id": requester_id,
        "provider_id": provider_id,
        "device_id": prov_device,
        "service_id": prov_service,
        "qos" : quality_provided,
        "rating_provided": round(rating_received, 2)
    }
    try:
        trust_response = requests.post(f"{BASE_URL}/calculate_total_trust/", json=trust_payload)
        trust_response.raise_for_status()
        trust_data = trust_response.json()
        print(f"Trust Calculated | User Trust: {trust_data.get('user_trust', 0):.2f} | Device Trust: {trust_data.get('device_trust', 0):.2f} | Service Trust: {trust_data.get('service_trust', 0):.2f}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to calculate trust: {e}")

def run_simulation():
    initialize_dimensions()
    for i in range(TOTAL_INTERACTIONS):
        simulate_interaction()


if __name__ == "__main__":
    run_simulation()


# future enhancement: multithreading: As most process is I/O bound, using multithreading can extremely increase execution speed