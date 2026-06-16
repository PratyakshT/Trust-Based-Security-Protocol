from django.db import models
from django.utils import timezone

class UserDimension(models.Model):
    user_id = models.IntegerField(primary_key=True)
    credibility=models.FloatField(default=0.5)
    reputation=models.FloatField(default=0.5)
    rating_trend=models.FloatField(default=0.5)
    fluctuation=models.FloatField(default=0.5)
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

    class Meta:
        # This acts as your N x N matrix coordinate constraint: 
        # Only one relationship row can exist for a specific pair of nodes
        unique_together = ('source_node', 'target_node')
        indexes = [
            models.Index(fields=['source_node', 'target_node']),
        ]

    def __str__(self):
        return f"{self.source_node.user_id} -> {self.target_node.user_id}"


class SIoTNode(models.Model):
    """Represents a Device/User entity in the SIoT network."""
    node_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(UserDimension, on_delete=models.CASCADE)
    device = models.ForeignKey(DeviceDimension, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceDimension, on_delete=models.CASCADE)

    # Security Flag
    is_malicious = models.BooleanField(default=False, help_text="Flagged by the ML Model")
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.node_id}"

class InteractionHistory(models.Model):
    """The immutable ledger of all network events used for ML feature extraction."""
    interaction_id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(SIoTNode, related_name='requests_made', on_delete=models.CASCADE)
    provider = models.ForeignKey(SIoTNode, related_name='services_provided', on_delete=models.CASCADE)
    
    # service_id = models.CharField(max_length=100)
    # rating = models.IntegerField(choices=[(0, 'Bad'), (1, 'Good')])
    # response_time_ms = models.FloatField(default=0.0)
    # latency_ms = models.FloatField(default=0.0)
    # social_similarity_score = models.FloatField(default=0.0)
    # timestamp = models.DateTimeField(default=timezone.now)
    # is_mitigated = models.BooleanField(default=False, help_text="True if rating was nullified by countermeasure")

    class Meta:
        # Indexing speeds up the complex groupby queries our ML model will run later
        indexes = [
            models.Index(fields=['provider', 'requester']), 
        ]

class TrustScore(models.Model):
    """The final calculated multi-dimensional trust output."""
    node = models.OneToOneField(SIoTNode, on_delete=models.CASCADE, related_name='trust_score')
    t_user = models.FloatField(default=0.5, help_text="User Intention Score")
    t_device = models.FloatField(default=0.5, help_text="Device Hardware Score")
    t_service = models.FloatField(default=0.5, help_text="Service Quality Score")
    t_final = models.FloatField(default=0.5, help_text="Aggregated Multidimensional Score")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trust Profile: {self.node.node_id} | Final: {self.t_final}"