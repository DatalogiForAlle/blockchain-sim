from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))


@register.filter
def miner_can_buy(token, miner):
    return miner.can_buy_token(token)


@register.filter
def reason_miner_cannot_buy(token, miner):
    if token.in_queue_for_initial_transaction():
        return 'Har ingen ejer endnu'
    elif not token.price:
        return 'Ikke sat til salg'
    elif token.owner == miner:
        return 'Din egen token'
    elif token.transaction_in_process:
        return 'Handel i proces'
    elif token.price > miner.balance:
        return 'Du har ikke råd'
    return 'Bug..?'
