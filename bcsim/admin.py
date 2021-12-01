from django.contrib import admin
from .models import Blockchain, Block, Miner

class BlockchainAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'created_at',
    )


class BlockAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'blockchain',
        'payload',
        'nonce',
    )


class MinerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
    )


admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Miner, MinerAdmin)
