# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from pydantic import BaseModel
import pandas as pd

# Local imports
import models
from database import get_db
from ml_engine import extract_trust_features, get_or_train_model

app = FastAPI(title="DSL-STM Ingestion & Trust Engine")

# --- Pydantic Schemas for Data Validation ---
class InteractionCreate(BaseModel):
    requester_id: str
    provider_id: str
    service_id: str
    rating: int

class NodeCreate(BaseModel):
    node_id: str
    device_category: str
    dcc_score: float
    elc_score: float
    msrc_score: float

# --- API Endpoints ---

@app.post("/api/register/")
async def register_node(node: NodeCreate, db: AsyncSession = Depends(get_db)):
    """Day 4 Add-on: Registers a node so Foreign Keys don't fail."""
    new_node = models.SIoTNode(**node.model_dump())
    db.add(new_node)
    try:
        await db.commit()
    except Exception:
        await db.rollback() # Ignore if node already exists from previous runs
    return {"status": "success", "node_id": node.node_id}


@app.post("/api/interactions/")
async def log_interaction(interaction: InteractionCreate, db: AsyncSession = Depends(get_db)):
    """
    Day 2: High-speed endpoint. Accepts interactions and writes them to PostgreSQL asynchronously.
    """
    if interaction.rating not in [0, 1]:
        raise HTTPException(status_code=400, detail="Rating must be 0 or 1")
    
    # Create the SQLAlchemy object
    new_interaction = models.InteractionHistory(
        requester_id=interaction.requester_id,
        provider_id=interaction.provider_id,
        service_id=interaction.service_id,
        rating=interaction.rating
    )
    
    # Async database write
    db.add(new_interaction)
    await db.commit()
    
    return {"status": "success", "message": "Interaction logged"}


@app.get("/api/calculate_trust/")
async def calculate_system_trust(db: AsyncSession = Depends(get_db)):
    """
    Day 3: The main trigger for the DSL-STM calculations.
    Pulls data, extracts features, runs the Neural Network, and punishes attackers.
    """
    # 1. Fetch all interactions asynchronously
    result = await db.execute(select(models.InteractionHistory))
    interactions = result.scalars().all()
    
    if not interactions:
        return {"status": "skipped", "message": "No interactions to process."}
        
    # Convert SQLAlchemy objects to Pandas DataFrame for the ML engine
    data = [{
        "requester_id": i.requester_id, 
        "provider_id": i.provider_id, 
        "rating": i.rating
    } for i in interactions]
    
    df = pd.DataFrame(data)
    
    # 2. Extract Features (Trust Composition)
    features_df = extract_trust_features(df)
    
    # 3. Get the AI Model and Predict
    mlp = get_or_train_model(features_df)
    
    malicious_nodes = []
    if mlp is not None:
        # Prepare the features exactly as the model expects them
        X_predict = features_df[['reputation_score', 'total_interactions', 'rating_trend']]
        predictions = mlp.predict(X_predict)
        features_df['is_malicious_prediction'] = predictions
        
        # 4. Countermeasures (Punishing the attackers)
        for index, row in features_df.iterrows():
            provider_id = row['provider_id']
            is_malicious = bool(row['is_malicious_prediction'])
            
            if is_malicious:
                malicious_nodes.append(provider_id)
                
                # Apply mathematical penalty (as per the paper)
                penalized_score = row['reputation_score'] / 1.5
                
                # Update the database to flag this node as malicious
                await db.execute(
                    update(models.SIoTNode)
                    .where(models.SIoTNode.node_id == provider_id)
                    .values(is_malicious=True)
                )

    await db.commit()
    
    return {
        "status": "success",
        "processed_interactions": len(interactions),
        "analyzed_nodes": len(features_df),
        "malicious_nodes_detected": malicious_nodes
    }