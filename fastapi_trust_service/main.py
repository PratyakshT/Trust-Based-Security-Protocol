import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator import NUM_USERS, NUM_DEVICES, NUM_SERVICES
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select
import models
import random
from database import engine, Base, get_db
from pydantic import BaseModel
from trust_calculation import calc_user_trust, calc_device_trust, calc_service_trust

app = FastAPI(title="DSL-STM Cyber e v3")

class InteractionCreate(BaseModel):
    requester_id: int
    provider_id: int
    quality_of_service_provided: float
    rating_received: float
    total_trust_for_interaction: float

class TotalTrustPayload(BaseModel):
    requester_id: int
    provider_id: int
    device_id: int
    service_id: int
    qos : float
    rating_provided: float

class InitPayload(BaseModel):
    user_points: dict[int, list[str]] = None

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/api/interactions/")
async def log_interaction(interaction: InteractionCreate, db: AsyncSession = Depends(get_db)):
    new_interaction = models.InteractionHistory(
        requester_id=interaction.requester_id,
        provider_id=interaction.provider_id,
        quality_of_service_provided=interaction.quality_of_service_provided,
        rating_received=interaction.rating_received,
        total_trust_for_interaction=interaction.total_trust_for_interaction
    )
    db.add(new_interaction)
    await db.commit()
    return {"status": "success"}

@app.post("/api/init_dimensions/")
async def init_dimensions(payload: InitPayload = None, db: AsyncSession = Depends(get_db)):
    try:
        
        # Explicitly setting the default values that Django expects (0.5) to avoid NOT NULL errors
        users = [{"user_id": i, "credibility": 0.5, "reputation": 0.5, "rating_trend": 0.5, "fluctuation": 0.5, "total_interaction_provider": 0, "total_interaction_requester": 0, "prev_qos_provided": 0.5, "user_trust_score": 0.5} for i in range(1, NUM_USERS + 1)]
        devices = []
        limit_60 = int(0.6 * NUM_DEVICES)
        for i in range(1, NUM_DEVICES + 1):
            if i <= limit_60:
                devices.append({"device_id": i, "dcc_score": 1, "elc_score": 0.5, "msrc_score": 1, "device_trust_score": 0.5})
            else:
                devices.append({"device_id": i, "dcc_score": 0.5, "elc_score": 0.25, "msrc_score": 0.25, "device_trust_score": 0.5})

        services = []
        limit_60 = int(0.6 * NUM_SERVICES)
        for i in range(1, NUM_SERVICES + 1):
            if i <= limit_60:
                services.append({"service_id": i, "latency": random.uniform(0.8,1), "response_time": random.uniform(0.8,1), "successfulness": random.uniform(0.8,1), "availability": random.uniform(0.8,1), "service_trust_score": 0.5})
            else:
                services.append({"service_id": i, "latency": random.uniform(0,0.3), "response_time": random.uniform(0,0.3), "successfulness": random.uniform(0,0.3), "availability": random.uniform(0,0.3), "service_trust_score": 0.5})

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


