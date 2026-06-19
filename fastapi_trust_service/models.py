# models.py
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, Table, UniqueConstraint, Index
from database import Base
import datetime

class SIoTNode(Base):
    # Django created this table as "appname_modelname"
    __tablename__ = "network_state_siotnode"

    node_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("network_state_userdimension.user_id"))
    device_id = Column(Integer, ForeignKey("network_state_devicedimension.device_id"))
    service_id = Column(Integer, ForeignKey("network_state_servicedimension.service_id"))
    is_malicious = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    
class InteractionHistory(Base):
    __tablename__ = "network_state_interactionhistory"

    interaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requester_id = Column(Integer, ForeignKey("network_state_userdimension.user_id"))
    provider_id = Column(Integer, ForeignKey("network_state_userdimension.user_id"))
    quality_of_service_provided=Column(Float, default=0.5)
    rating_received=Column(Float, default=0.5)
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class UserDimension(Base):
    __tablename__ = "network_state_userdimension"
    user_id = Column(Integer, primary_key=True)
    credibility = Column(Float, default=0.5)
    reputation = Column(Float, default=0.5)
    rating_trend = Column(Float, default=0.5)
    fluctuation = Column(Float, default=0.5)
    total_interaction_provider = Column(Integer, default=0)
    total_interaction_requester = Column(Integer, default=0)
    prev_qos_provided = Column(Float, default=0.5)
    user_trust_score = Column(Float, default=0.5)

class DeviceDimension(Base):
    __tablename__ = "network_state_devicedimension"
    device_id = Column(Integer, primary_key=True)
    dcc_score = Column(Float, default=0.5)
    elc_score = Column(Float, default=0.5)
    msrc_score = Column(Float, default=0.5)
    device_trust_score = Column(Float, default=0.5)

class ServiceDimension(Base):
    __tablename__ = "network_state_servicedimension"
    service_id = Column(Integer, primary_key=True)
    latency = Column(Float, default=0.5)
    response_time = Column(Float, default=0.5)
    successfulness = Column(Float, default=0.5)
    availability = Column(Float, default=0.5)
    service_trust_score = Column(Float, default=0.5)

class NodeRelationship(Base):
    __tablename__ = "network_state_noderelationship"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(Integer, ForeignKey("network_state_userdimension.user_id"))
    target_node_id = Column(Integer, ForeignKey("network_state_userdimension.user_id"))
    relationship_strength = Column(Float, default=0.5)
    similarity = Column(Float, default=0.5)
    direct_exchange = Column(Float, default=0.5)
    rating_frequency = Column(Float, default=0.5)
    recommendation = Column(Float, default=0.5)
    total_interaction_bw_prov_req = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('source_node_id', 'target_node_id', name='network_state_noder_source_node_id_target_nod_9831a293_uniq'),
        Index('network_state_noderelation_source_node_id_8180dc_idx', 'source_node_id', 'target_node_id'),
    )
