from django.contrib import admin
from .models import TextMessage, TextMessageBatch

class TextMessageAdmin(admin.ModelAdmin):
    # display datetime in the changelist
    list_display = ('id', 'timestamp', 'batch', 'internal_id', 'status', 'notified', 'recipient', 'text', 'producer')
    # display datetime when you edit comments
    readonly_fields = ('timestamp', 'batch', 'producer')
    # optional, use only if you need custom ordering of the fields
    #fields = ('title', 'body', 'datetime')
    #raw_id_fields = ('producer',)


# Register your models here.
admin.site.register(TextMessage, TextMessageAdmin)
admin.site.register(TextMessageBatch)
