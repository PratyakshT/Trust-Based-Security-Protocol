from django.contrib import admin
from .models import  InteractionHistory, UserDimension, DeviceDimension,ServiceDimension, NodeRelationship

@admin.register(InteractionHistory) 
class InteractionHistoryAdmin(admin.ModelAdmin):
    list_display = ('interaction_id','requester', 'provider','quality_of_service_provided','rating_received','total_trust_for_interaction','timestamp')
    list_filter = ('requester', 'provider')

@admin.register(UserDimension) 
class UserDimensionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'credibility', 'reputation','rating_trend','fluctuation','user_trust_score','total_interaction_provider','total_interaction_requester','prev_qos_provided')
    list_filter = ('user_id',)

@admin.register(DeviceDimension) 
class DeviceDimensionAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'dcc_score', 'elc_score','msrc_score','device_trust_score')
    list_filter = ('device_id',)

@admin.register(ServiceDimension) 
class ServiceDimensionAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'latency', 'response_time','successfulness','availability','service_trust_score')
    list_filter = ('service_id',)

@admin.register(NodeRelationship) 
class NodeRelationshipAdmin(admin.ModelAdmin):
    list_display = ('source_node', 'target_node', 'relationship_strength','similarity','direct_exchange','rating_frequency','recommendation','total_interaction_bw_prov_req')
    list_filter = ('source_node', 'target_node')