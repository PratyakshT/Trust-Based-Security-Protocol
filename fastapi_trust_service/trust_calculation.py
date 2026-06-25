from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
from simulator import BAD_MOUTHERS_OR_BALLOT_STUFFERS,DISCRIMINATORY_ATTACKERS,ON_OFF_ATTACKERS,OPORTUNISTIC_SERVICE_ATTACKERS

def update_credibility_sync(requester, qos: float,rating_provided:float):
    prev_cred = requester.credibility

    diff = abs(qos - rating_provided)
    if diff >= 0.65:
        new_cred=max(prev_cred-0.25,0)

    elif diff==0:
        new_cred=min(prev_cred+0.25,1)

    elif diff <= 0.30:
        new_cred = min(prev_cred+0.15,1)

    else:
        new_cred = prev_cred

    requester.credibility = new_cred

def update_rating_trend_sync(requester, rating_provided:float):
    total_inter = requester.total_interaction_requester + 1
    prev_rating_trend = requester.rating_trend
    if rating_provided >= 0.5:
        new_rat_trend = ((prev_rating_trend*(total_inter-1))+rating_provided)/total_inter
    else:
        new_rat_trend = (prev_rating_trend*(total_inter-1))/total_inter
    requester.rating_trend = new_rat_trend

def update_reputation_sync(provider, requester_id: int,rating_received:float):
        
    total_inter = provider.total_interaction_provider + 1
    prev_repu = provider.reputation

    if requester_id in (BAD_MOUTHERS_OR_BALLOT_STUFFERS | DISCRIMINATORY_ATTACKERS):
        new_repu=prev_repu

    elif rating_received >= 0.5:
        new_repu = ((prev_repu*(total_inter-1))+rating_received)/total_inter

    else:
        new_repu = max(0,prev_repu-0.2)

    provider.reputation = new_repu

def update_fluctuation_sync(provider, qos:float):
    total_inter = provider.total_interaction_provider + 1
    prev_fluctuation = provider.fluctuation
    prev_qos_provided = provider.prev_qos_provided

    diff = abs(qos - prev_qos_provided)

    if diff >= 0.65:
        new_fluctuation = ((prev_fluctuation*(total_inter-1))+diff)/total_inter
    else:
        new_fluctuation = (prev_fluctuation*(total_inter-1))/total_inter

    provider.fluctuation = new_fluctuation
    provider.prev_qos_provided = qos

def update_direct_exchange_sync(common, rating_provided:float):
    total_inter = common.total_interaction_bw_prov_req + 1
    prev_direct_exch = common.direct_exchange
    new_direct_exch = ((prev_direct_exch*(total_inter-1)) + rating_provided)/total_inter
    common.direct_exchange = new_direct_exch

def update_rating_frequency_sync(common, requester):
    total_inter = requester.total_interaction_requester + 1
    prev_rating_freq = common.rating_frequency
    new_rating_frequency = ((prev_rating_freq*(total_inter-1)) + 1)/total_inter
    common.rating_frequency = new_rating_frequency

async def calc_user_trust(db: AsyncSession, requester_id: int, provider_id: int, qos:float, rating_provided:float):
    result1 = await db.execute(select(models.UserDimension).filter(models.UserDimension.user_id == provider_id))
    provider = result1.scalars().first()

    result2 = await db.execute(select(models.UserDimension).filter(models.UserDimension.user_id == requester_id))
    requester = result2.scalars().first()

    result_common = await db.execute(select(models.NodeRelationship).filter(models.NodeRelationship.source_node_id == requester_id, models.NodeRelationship.target_node_id == provider_id))
    common = result_common.scalars().first()

    update_reputation_sync(provider, requester_id, rating_provided)
    update_credibility_sync(requester, qos, rating_provided)
    update_rating_trend_sync(requester, rating_provided)
    update_fluctuation_sync(provider, qos)
    update_rating_frequency_sync(common, requester)
    update_direct_exchange_sync(common, rating_provided)

    total_trust = (provider.reputation+provider.credibility+provider.rating_trend+(2*(1-provider.fluctuation))+common.direct_exchange+common.rating_frequency+common.similarity)/8

    provider.total_interaction_provider+=1
    requester.total_interaction_requester+=1
    common.total_interaction_bw_prov_req+=1
    
    provider.user_trust_score=total_trust

    await db.commit()
    return total_trust

async def calc_device_trust(db: AsyncSession, device_id: int):
    result = await db.execute(select(models.DeviceDimension).filter(models.DeviceDimension.device_id == device_id).with_for_update())
    device = result.scalars().first()
    if device:
        total_trust = (device.dcc_score+device.elc_score+device.msrc_score)/3
        device.device_trust_score=total_trust
        await db.commit()
        return total_trust
    return 0.5
    
async def calc_service_trust(db: AsyncSession, service_id: int):
    result = await db.execute(select(models.ServiceDimension).filter(models.ServiceDimension.service_id == service_id).with_for_update())
    service = result.scalars().first()
    if service:
        total_trust = (service.latency+service.response_time+service.successfulness+service.availability)/4
        service.service_trust_score=total_trust
        await db.commit()
        return total_trust
    return 0.5
