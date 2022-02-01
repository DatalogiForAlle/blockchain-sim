from django.contrib import admin
from .models import Blockchain, Block, Miner, Token

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
        'nonce',
    )


class MinerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'miner_num',
        'balance'
    )


class TokenAdmin(admin.ModelAdmin):
    list_display = (
        'owner',
        'seed',
        'price'
    )

admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Miner, MinerAdmin)
admin.site.register(Token, TokenAdmin)
