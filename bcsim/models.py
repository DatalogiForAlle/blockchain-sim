from django.db import models
import secrets


def new_unique_blockchain_id():
    """
    Create a new unique blockchain ID (8 alphabetic chars)
    """
    while True:
        blockchain_id = secrets.token_hex(4)
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            break
    return blockchain_id


class Blockchain(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    title = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        """
        Set unique custom id for blockchain before creating a new blockchain object
        """
        if not self.id:
            # we are creating a new blockchain (not updating an existing blockchain)
            self.id = new_unique_blockchain_id()
        super(Blockchain, self).save(*args, **kwargs)


class Block(models.Model):

    block_id = models.IntegerField(primary_key=False)

    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    miner_id = models.CharField(max_length=16)

    payload = models.CharField(max_length=200)

    nonce = models.CharField(max_length=200)

    prev_hash = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
