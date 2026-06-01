# models.py
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey
from database import Base
import datetime

class SIoTNode(Base):
    # Django created this table as "appname_modelname"
    __tablename__ = "network_state_siotnode"

    node_id = Column(String(100), primary_key=True, index=True)
    device_category = Column(String(50))
    dcc_score = Column(Float)
    elc_score = Column(Float)
    msrc_score = Column(Float)
    is_malicious = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class InteractionHistory(Base):
    __tablename__ = "network_state_interactionhistory"

    interaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Mapping Foreign Keys to the Django table
    requester_id = Column(String(100), ForeignKey("network_state_siotnode.node_id"))
    provider_id = Column(String(100), ForeignKey("network_state_siotnode.node_id"))
    service_id = Column(String(100))
    rating = Column(Integer)  # 0 for Bad, 1 for Good
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_mitigated = Column(Boolean, default=False)