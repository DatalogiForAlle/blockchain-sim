from django.contrib import admin
from .models import Blockchain, Block, Miner, Token, Transaction


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
        'pk',
        'owner',
        'seed',
        'price',
        'transaction_in_process'
    )


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'blockchain',
        'buyer',
        'seller',
        'token',
        'processed',
        'amount'
    )


admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Miner, MinerAdmin)
admin.site.register(Token, TokenAdmin)
