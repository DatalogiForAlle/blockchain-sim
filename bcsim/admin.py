from django.contrib import admin
from .models import Blockchain, Block

class BlockchainAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
    )


class BlockAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'block_id',
        'blockchain_id',
        'miner_id',
        'payload',
        'nonce',
        'created_at'
    )


admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Block, BlockAdmin)
