from django.contrib import admin
from .models import Blockchain, Block, Miner

class BlockchainAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
        'creator_name'
    )


class BlockAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'block_num',
        'blockchain',
        'payload',
        'nonce',
    )


class MinerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'miner_num',
        'balance'
    )


admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Miner, MinerAdmin)
