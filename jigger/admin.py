from django.contrib import admin
from .models import Contact, ContactTag, Campaign, CampaignLead, FunnelEvent

class FunnelEventAdmin(admin.ModelAdmin):
    # display datetime in the changelist
    list_display = ('id', 'timestamp', 'source', 'action', 'seen', 'incoming', 'lead', 'parent')
    # display datetime when you edit comments
    readonly_fields = ('timestamp',)
    # optional, use only if you need custom ordering of the fields
    #fields = ('title', 'body', 'datetime')


admin.site.register(Contact)
admin.site.register(ContactTag)
admin.site.register(Campaign)
admin.site.register(CampaignLead)
admin.site.register(FunnelEvent, FunnelEventAdmin)
