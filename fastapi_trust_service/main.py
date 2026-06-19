import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sim2 import NUM_USERS, NUM_DEVICES, NUM_SERVICES
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
import models
import random
from database import engine, Base, get_db
from pydantic import BaseModel
import pandas as pd
import ml_engine
from trust_calculation import calc_user_trust, calc_device_trust, calc_service_trust

app = FastAPI(title="DSL-STM Cyber e v3")

class InteractionCreate(BaseModel):
    requester_id: int
    provider_id: int
    quality_of_service_provided: float
    rating_received: float

class NodeCreate(BaseModel):
    node_id: int
    user_id: int
    device_id: int
    service_id: int

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/api/register/")
async def register_node(node: NodeCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.SIoTNode).filter(models.SIoTNode.node_id == node.node_id))
    existing_node = result.scalars().first()
    if existing_node:
        return {"status": "already_registered"}
    
    new_node = models.SIoTNode(
        node_id=node.node_id,
        user_id=node.user_id,
        device_id=node.device_id,
        service_id=node.service_id
    )
    db.add(new_node)
    await db.commit()
    return {"status": "success"}

@app.post("/api/interactions/")
async def log_interaction(interaction: InteractionCreate, db: AsyncSession = Depends(get_db)):
    new_interaction = models.InteractionHistory(
        requester_id=interaction.requester_id,
        provider_id=interaction.provider_id,
        quality_of_service_provided=interaction.quality_of_service_provided,
        rating_received=interaction.rating_received
    )
    db.add(new_interaction)
    await db.commit()
    return {"status": "success"}

class InitPayload(BaseModel):
    user_points: dict[int, list[str]] = None

@app.post("/api/init_dimensions/")
async def init_dimensions(payload: InitPayload = None, db: AsyncSession = Depends(get_db)):
    try:
        
        # Explicitly setting the default values that Django expects (0.5) to avoid NOT NULL errors
        choices1 = (0, 0.5, 1.0)
        choices2 = (0, 0.25, 0.5, 1.0)
        users = [{"user_id": i, "credibility": 0.5, "reputation": 0.5, "rating_trend": 0.5, "fluctuation": 0.5, "total_interaction_provider": 0, "total_interaction_requester": 0, "prev_qos_provided": 0.5, "user_trust_score": 0.5} for i in range(1, NUM_USERS + 1)]
        devices = [{"device_id": i, "dcc_score": random.choice(choices1), "elc_score": random.choice(choices2), "msrc_score": random.choice(choices2), "device_trust_score": 0.5} for i in range(1, NUM_DEVICES + 1)]
        services = [{"service_id": i, "latency": random.uniform(0,1), "response_time": random.uniform(0,1), "successfulness": random.uniform(0,1), "availability": random.uniform(0,1), "service_trust_score": 0.5} for i in range(1, NUM_SERVICES + 1)]

        await db.execute(insert(models.UserDimension).values(users).on_conflict_do_nothing())
        await db.execute(insert(models.DeviceDimension).values(devices).on_conflict_do_nothing())
        await db.execute(insert(models.ServiceDimension).values(services).on_conflict_do_nothing())
        
        # Check if relationships exist to avoid duplicates
        rel_check = await db.execute(select(models.NodeRelationship).limit(1))
        if not rel_check.scalars().first():
            def calculate_jaccard(set1, set2):
                if not set1 and not set2: return 0.0
                intersection = len(set1.intersection(set2))
                union = len(set1.union(set2))
                return intersection / union if union != 0 else 0.0

            relationships = []
            
            # Map the payload back to sets
            u_points = {}
            if payload and payload.user_points:
                u_points = {k: set(v) for k, v in payload.user_points.items()}
            
            for i in range(1, NUM_USERS + 1):
                for j in range(1, NUM_USERS + 1):
                    if i != j:
                        # Default to 0.5 if user_points were not provided
                        sim = 0.5
                        if i in u_points and j in u_points:
                            sim = calculate_jaccard(u_points[i], u_points[j])
                        
                        relationships.append({
                            "source_node_id": i, 
                            "target_node_id": j, 
                            "relationship_strength": 0.5, 
                            "similarity": round(sim, 4), 
                            "direct_exchange": 0.5, 
                            "rating_frequency": 0.5, 
                            "recommendation": 0.5, 
                            "total_interaction_bw_prov_req": 0
                        })
            await db.execute(models.NodeRelationship.__table__.insert(), relationships)
            
        await db.commit()
        return {"status": "success", "message": "Dimensions initialized"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class TotalTrustPayload(BaseModel):
    requester_id: int
    provider_id: int
    device_id: int
    service_id: int
    qos : float
    rating_provided: float

@app.post("/api/calculate_total_trust/")
async def calculate_total_trust(payload: TotalTrustPayload, db: AsyncSession = Depends(get_db)):
    try:
        user_trust = await calc_user_trust(db, payload.requester_id, payload.provider_id, payload.qos, payload.rating_provided)
        device_trust = await calc_device_trust(db, payload.device_id)
        service_trust = await calc_service_trust(db, payload.service_id)
        
        return {
            "status": "success",
            "user_trust": user_trust,
            "device_trust": device_trust,
            "service_trust": service_trust
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.UserDimension).filter(models.UserDimension.user_id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/NodeRelations/{source_id}/{target_id}")
async def get_node_relation(source_id: int, target_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.NodeRelationship).filter(
        models.NodeRelationship.source_node_id == source_id,
        models.NodeRelationship.target_node_id == target_id
    ))
    relation = result.scalars().first()
    if not relation:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relation

@app.get("/api/calculate_trust/")
async def calculate_trust(db: AsyncSession = Depends(get_db)):
    """V3: High-Performance Multi-Dimensional trust evaluation endpoint."""
    # 1. Fetch entire ledger state from PostgreSQL
    interaction_result = await db.execute(select(models.InteractionHistory))
    interactions = interaction_result.scalars().all()
    
    if not interactions:
        return {"processed_interactions": 0, "msg": "No interactions available."}

    data = [{
        "interaction_id": i.interaction_id,
        "requester_id": i.requester_id,
        "provider_id": i.provider_id,
        "rating": i.rating,
        "response_time_ms": i.response_time_ms,
        "latency_ms": i.latency_ms,
        "social_similarity_score": i.social_similarity_score,
        "timestamp": i.timestamp
    } for i in interactions]
    df = pd.DataFrame(data)

    # 2. Extract advanced metrics via updated ML e
    node_profiles, pairwise_df = ml_engine.extract_multidimensional_features(df)
    
    # 3. Compile or retrieve the MLP network
    mlp_model = ml_engine.get_or_train_model(node_profiles)
    
    malicious_nodes = []
    
    if mlp_model and not node_profiles.empty:
        X_infer = node_profiles[['reputation_score', 'fluctuation_score', 'rating_trend_score', 'credibility_score', 'avg_response_time', 'avg_latency', 'discriminatory_bias', 'max_rating_frequency']]
        
        predictions = mlp_model.predict(X_infer)
        node_profiles['pred'] = predictions
        
        # FIX: Explicitly target all non-zero classifications (Class 1 and Class 2)
        flagged_df = node_profiles[node_profiles['pred'] != 0]
        malicious_nodes = flagged_df['node_id'].tolist()
        
        # 4. Synchronize security flags down to operational database layer
        if malicious_nodes:
            await db.execute(
                models.SIoTNode.__table__.update()
                .where(models.SIoTNode.node_id.in_(malicious_nodes))
                .values(is_malicious=True)
            )
            await db.commit()

    return {
        "processed_interactions": len(df),
        "analyzed_nodes": len(node_profiles),
        "malicious_nodes_detected": malicious_nodes,
        "dimensions_active": ["User-Trust", "Device-Trust (Static)", "Contextual-Trust (Jaccard Ready)"]
    }