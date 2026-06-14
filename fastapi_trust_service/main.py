from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
from database import engine, Base, get_db
from pydantic import BaseModel
import pandas as pd
import ml_engine

app = FastAPI(title="DSL-STM Cyber e v3")

class InteractionCreate(BaseModel):
    requester_id: str
    provider_id: str
    service_id: str
    rating: int
    response_time_ms: float
    latency_ms: float
    social_similarity_score: float

class NodeCreate(BaseModel):
    node_id: str
    device_category: str
    dcc_score: float
    elc_score: float
    msrc_score: float

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
        device_category=node.device_category,
        dcc_score=node.dcc_score,
        elc_score=node.elc_score,
        msrc_score=node.msrc_score
    )
    db.add(new_node)
    await db.commit()
    return {"status": "success"}

@app.post("/api/interactions/")
async def log_interaction(interaction: InteractionCreate, db: AsyncSession = Depends(get_db)):
    if interaction.rating not in [0, 1]:
        raise HTTPException(status_code=400, detail="Rating must be 0 or 1")
    
    new_interaction = models.InteractionHistory(
        requester_id=interaction.requester_id,
        provider_id=interaction.provider_id,
        service_id=interaction.service_id,
        rating=interaction.rating,
        response_time_ms=interaction.response_time_ms,
        latency_ms=interaction.latency_ms,
        social_similarity_score=interaction.social_similarity_score
    )
    db.add(new_interaction)
    await db.commit()
    return {"status": "success"}

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