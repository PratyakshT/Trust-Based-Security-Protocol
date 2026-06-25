import random
import requests
import csv

CSV_FILE_PATH = "interactions_log.csv"
BASE_URL = "http://127.0.0.1:8001/api"

# Creating a persistent session to reuse TCP connections 
session = requests.Session()

NUM_USERS = 50
NUM_DEVICES = 10
NUM_SERVICES = 10
TOTAL_INTERACTIONS = 15000

INTERACTION_THRESHOLD_FOR_OSA = 10
SIMILARITY_THRESHOLD_FOR_DA = 0.4

BAD_MOUTHERS_OR_BALLOT_STUFFERS = {35,36,37,38,39,40}
DISCRIMINATORY_ATTACKERS = {41,42,43,44}
ON_OFF_ATTACKERS = {45,46,47}
OPORTUNISTIC_SERVICE_ATTACKERS = {48,49,50}

MALICIOUS = BAD_MOUTHERS_OR_BALLOT_STUFFERS | DISCRIMINATORY_ATTACKERS | ON_OFF_ATTACKERS | OPORTUNISTIC_SERVICE_ATTACKERS

def initialize_dimensions():
    print("--- [PHASE 0] Registering Users, Devices, and Services via FastAPI ---")
    
    properties_pool = [
        "Delhi", "NOIDA", "Gurgaon", "Mumbai", "Bangalore",
        "Music", "Sports", "Dance", "Gaming", "Reading",
        "AI", "Cybersecurity", "IoT", "Blockchain", "Art"
    ]
    
    user_points = {}
    for i in range(1, NUM_USERS+1):
        k = random.randint(3, 7) 
        user_points[i] = random.sample(properties_pool, k)

    print("User Point Subsets Generated for Jaccard Similarity:")
    for user_id, points in user_points.items():
        print(f"  User {user_id}: {set(points)}")
        
    try:
        payload = {"user_points": user_points}
        response = session.post(f"{BASE_URL}/init_dimensions/", json=payload)
        response.raise_for_status()
        print("Success:", response.json())
        print("Base Dimensions & NodeRelationships Registered.\n")
    except requests.exceptions.RequestException as e:
        print(f"Failed to initialize dimensions: {e}")
        
def simulate_interaction():
    requester_id = random.randint(1, NUM_USERS)

    provider_pool = [n for n in range(1, NUM_USERS + 1) if n != requester_id]
    provider_id = random.choice(provider_pool)

    prov_device = random.randint(1, NUM_DEVICES)
    prov_service = random.randint(1, NUM_SERVICES)

    provider = session.get(f"{BASE_URL}/user/{provider_id}").json()
    requester = session.get(f"{BASE_URL}/user/{requester_id}").json()
    common = session.get(f"{BASE_URL}/NodeRelations/{requester_id}/{provider_id}").json()

    attack_classes = []

    if provider_id in OPORTUNISTIC_SERVICE_ATTACKERS:
        curr_interactions = provider.get("total_interaction_provider", 0)
        if curr_interactions > INTERACTION_THRESHOLD_FOR_OSA:
            attack_classes.append(4)                                            # Opportunistic Service Attack
            quality_provided = random.uniform(0, 0.15)
        else:
            quality_provided = random.uniform(0.85, 1.0)

    elif provider_id in ON_OFF_ATTACKERS:
        attack_classes.append(3)                                                # On-Off Attack
        prev_qos_provided = provider.get("prev_qos_provided", 1.0)
        if prev_qos_provided < 0.2:                
            quality_provided = random.uniform(0.85, 1.0)
        else:
            quality_provided = random.uniform(0, 0.15)

    elif provider_id in (BAD_MOUTHERS_OR_BALLOT_STUFFERS | DISCRIMINATORY_ATTACKERS):
        quality_provided = random.uniform(0, 0.15)
    
    else:
        quality_provided = random.uniform(0.85, 1.0)

    if requester_id in BAD_MOUTHERS_OR_BALLOT_STUFFERS:
        attack_classes.append(1)                                                # Bad Mouthing / Ballot Stuffing
        if provider_id in MALICIOUS:
            rating_received = random.uniform(0.85, 1.0)
        else:
            rating_received = random.uniform(0, 0.15)

    elif requester_id in DISCRIMINATORY_ATTACKERS:
        attack_classes.append(2)                                                # Discriminatory Attack
        sim = common.get("similarity", 0)
        if sim > SIMILARITY_THRESHOLD_FOR_DA:
            rating_received = random.uniform(0.85, 1.0)
        else:
            rating_received = random.uniform(0, 0.15)

    else:
        rating_received = max(0, random.uniform(quality_provided - 0.1, quality_provided + 0.1))

    if not attack_classes:
        attack_classes.append(0)                                                # Class 0 represents normal/no attack

    trust_payload = {
        "requester_id": requester_id,
        "provider_id": provider_id,
        "device_id": prov_device,
        "service_id": prov_service,
        "qos" : quality_provided,
        "rating_provided": round(rating_received, 2)
    }

    total_trust = 0.5  # Default value in case the trust calculation API fails
    
    try:
        trust_response = session.post(f"{BASE_URL}/calculate_total_trust/", json=trust_payload)
        trust_response.raise_for_status()
        trust_data = trust_response.json()
        u_trust=trust_data.get('user_trust', 0)
        d_trust=trust_data.get('device_trust', 0)
        s_trust=trust_data.get('service_trust', 0)
        total_trust=(u_trust+d_trust+s_trust)/3
        print(f"Trust Calculated | User Trust: {u_trust:.2f} | Device Trust: {d_trust:.2f} | Service Trust: {s_trust:.2f} | Total Trust: {total_trust:.2f}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to calculate trust: {e}")

    payload = {
        "requester_id": requester_id,
        "provider_id": provider_id,
        "quality_of_service_provided": round(quality_provided, 2),
        "rating_received": round(rating_received, 2),
        "total_trust_for_interaction": round(total_trust, 2)
    }

    try:
        response = session.post(f"{BASE_URL}/interactions/", json=payload)
        response.raise_for_status()
        print(f"Interaction Logged | Req: {requester_id} -> Prov: {provider_id} | Qual: {quality_provided:.2f} | Rating: {rating_received:.2f} | Attacks: {attack_classes}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to log interaction: {e}")

    try:
        provider_updated = session.get(f"{BASE_URL}/user/{provider_id}").json()
        requester_updated = session.get(f"{BASE_URL}/user/{requester_id}").json()
        common_updated = session.get(f"{BASE_URL}/NodeRelations/{requester_id}/{provider_id}").json()

        with open(CSV_FILE_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                requester_id,
                provider_id,
                provider_updated.get("reputation", 0),
                provider_updated.get("fluctuation", 0),
                provider_updated.get("total_interaction_provider", 0), 
                requester_updated.get("rating_trend", 0),
                requester_updated.get("credibility", 0),
                common_updated.get("rating_frequency", 0),
                common_updated.get("similarity", 0),
                common_updated.get("direct_exchange", 0),
                str(attack_classes)  
            ])
    except Exception as e:
        print(f"Failed to write to CSV: {e}")


def run_simulation():
    initialize_dimensions()

    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "requester_id",
            "provider_id",
            "provider_reputation",
            "provider_fluctuation",
            "provider_total_interactions", 
            "requester_rating_trend",
            "requester_credibility",
            "common_rating_frequency",
            "common_similarity",
            "common_direct_exchange",
            "attack_class"
        ])

    for i in range(TOTAL_INTERACTIONS):
        simulate_interaction()


if __name__ == "__main__":
    run_simulation()


# future enhancement: multithreading: As most process is I/O bound, using multithreading can extremely increase execution speed