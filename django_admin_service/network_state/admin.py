# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import SIoTNode, InteractionHistory, TrustScore

@admin.register(SIoTNode)
class SIoTNodeAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'device_category', 'is_malicious', 'joined_at')
    list_filter = ('is_malicious', 'device_category')
    search_fields = ('node_id',)

@admin.register(InteractionHistory)
class InteractionHistoryAdmin(admin.ModelAdmin):
    list_display = ('requester', 'provider', 'service_id', 'rating', 'timestamp', 'is_mitigated')
    list_filter = ('rating', 'is_mitigated')

@admin.register(TrustScore)
class TrustScoreAdmin(admin.ModelAdmin):
    list_display = ('node', 't_final', 't_user', 't_device', 't_service', 'updated_at')