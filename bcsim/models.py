from django.db import models
from datetime import datetime
import secrets
import hashlib


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
    creator_name = models.CharField(max_length=36,default="Blockchain creator")
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


class Miner(models.Model):
    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)
    name = models.CharField(max_length=36,)
    created_at = models.DateTimeField(auto_now_add=True)


class Block(models.Model):

    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    miner = models.ForeignKey(Miner, on_delete=models.CASCADE)

    payload = models.CharField(max_length=200, null=True, blank=True)

    # Nonce has to be an integer, but to be able to store very big integers, we save it as a string.
    nonce = models.CharField(max_length=60, null=True, blank=True)

    prev_hash = models.CharField(max_length=200)

    def hash(self):
        s = f"{self.block_id}{self.miner.id}{self.prev_hash}{self.payload}{self.nonce}"
        hash = hashlib.sha256(s.encode()).hexdigest()
        return hash

    def valid(self):
        hash = self.hash()
        if hash[0] in list("012"):
            return True
