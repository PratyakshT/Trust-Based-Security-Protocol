from django.db import models
from django.utils import timezone

class UserDimension(models.Model):
    user_id = models.IntegerField(primary_key=True)
    credibility=models.FloatField(default=0.5)
    reputation=models.FloatField(default=0.5)
    rating_trend=models.FloatField(default=0.5)
    fluctuation=models.FloatField(default=0.5)
    total_interaction_provider=models.IntegerField(default=0)
    total_interaction_requester=models.IntegerField(default=0)
    prev_qos_provided=models.FloatField(default=0.5)
    user_trust_score=models.FloatField(default=0.5)

    def __str__(self):
        return f"{self.user_id}"

class DeviceDimension(models.Model):
    device_id = models.IntegerField(primary_key=True)
    dcc_score=models.FloatField(default=0.5)
    elc_score=models.FloatField(default=0.5)
    msrc_score=models.FloatField(default=0.5)
    device_trust_score=models.FloatField(default=0.5)

    def __str__(self):
        return f"{self.device_id}"
    
class ServiceDimension(models.Model):
    service_id = models.IntegerField(primary_key=True)
    latency=models.FloatField(default=0.5)
    response_time=models.FloatField(default=0.5)
    successfulness=models.FloatField(default=0.5)
    availability=models.FloatField(default=0.5)
    service_trust_score=models.FloatField(default=0.5)

    def __str__(self):
        return f"{self.service_id}"

class NodeRelationship(models.Model):
    # The two nodes involved in the relationship
    source_node = models.ForeignKey(UserDimension, related_name='relationships_out', on_delete=models.CASCADE)
    target_node = models.ForeignKey(UserDimension, related_name='relationships_in', on_delete=models.CASCADE)
    
    # Your 5 matrix values (If these are calculated numbers, change CharField to FloatField!)
    relationship_strength = models.FloatField(default=0.5)
    similarity = models.FloatField(default=0.5)
    direct_exchange = models.FloatField(default=0.5)
    rating_frequency = models.FloatField(default=0.5)
    recommendation = models.FloatField(default=0.5)
    total_interaction_bw_prov_req=models.IntegerField(default=0)

    class Meta:
        # This acts as your N x N matrix coordinate constraint: 
        # Only one relationship row can exist for a specific pair of nodes
        unique_together = ('source_node', 'target_node')
        indexes = [
            models.Index(fields=['source_node', 'target_node']),
        ]

    def __str__(self):
        return f"{self.source_node.user_id} -> {self.target_node.user_id}"

class InteractionHistory(models.Model):
    """The immutable ledger of all network events used for ML feature extraction."""
    interaction_id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(UserDimension, related_name='requests_made', on_delete=models.CASCADE)
    provider = models.ForeignKey(UserDimension, related_name='services_provided', on_delete=models.CASCADE)
    quality_of_service_provided=models.FloatField(default=0.5)
    rating_received=models.FloatField(default=0.5)
    total_trust_for_interaction=models.FloatField(default=0.5)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        # Indexing speeds up the complex groupby queries our DL model will run later
        indexes = [
            models.Index(fields=['provider', 'requester']), 
        ]