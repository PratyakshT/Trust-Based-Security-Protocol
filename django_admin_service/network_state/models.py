from django.db import models
from django.utils import timezone

class SIoTNode(models.Model):
    """Represents a Device/User entity in the SIoT network."""
    node_id = models.CharField(max_length=100, primary_key=True)
    device_category = models.CharField(max_length=50) # e.g., 'sensor', 'smartphone'
    
    # Device Trust-Dimension (Hardware Ability Features)
    dcc_score = models.FloatField(help_text="Device Capability Criterion (0.0 - 1.0)")
    elc_score = models.FloatField(help_text="Energy Limitation Criterion (0.0 - 1.0)")
    msrc_score = models.FloatField(help_text="Minimal Security Requirements (0.0 - 1.0)")
    
    # Security Flag
    is_malicious = models.BooleanField(default=False, help_text="Flagged by the ML Model")
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.node_id} ({self.device_category})"

class InteractionHistory(models.Model):
    """The immutable ledger of all network events used for ML feature extraction."""
    interaction_id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(SIoTNode, related_name='requests_made', on_delete=models.CASCADE)
    provider = models.ForeignKey(SIoTNode, related_name='services_provided', on_delete=models.CASCADE)
    
    service_id = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(0, 'Bad'), (1, 'Good')])
    response_time_ms = models.FloatField(default=0.0)
    latency_ms = models.FloatField(default=0.0)
    social_similarity_score = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(default=timezone.now)
    is_mitigated = models.BooleanField(default=False, help_text="True if rating was nullified by countermeasure")

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