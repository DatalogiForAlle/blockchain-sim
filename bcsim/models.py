from django.db import models
import secrets


def new_unique_blockchain_id():
    """
    Create a new unique market ID (8 alphabetic chars)
    """
    while True:
        blockchain_id = secrets.token_hex(4)
        if not Blockchain.objects.filter(id=blockchain_id).exists():
            break
    return blockchain_id

class Blockchain(models.Model):
    # should id just be auto generated?
    id = models.CharField(max_length=16, primary_key=True)
    
    # max-length of title?
    title = models.CharField(max_length=len("No blockchain title should be longer than this quite long title"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}[{self.id}]"
    
    def save(self, *args, **kwargs):
        """
        Set unique custom id for blockchain before creating a new blockchain object
        """
        # Create blockchain id we are creating a new blockchain (not saving an existing blockchain)
        if not self.id:
            self.id = new_unique_blockchain_id()
        super(Blockchain, self).save(*args, **kwargs)


class Block(models.Model):
    # should block_id be primary key?
    block_id = models.IntegerField() 

    blockchain_id = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    # how long should miner_id be allowed to be?
    miner_id = models.CharField(max_length=16)

    # what exactly is the payload? how long can it be?
    payload = models.CharField(max_length=200)

    # max_length of nonce?
    nonce = models.CharField(max_length=200)


    # max-length of prev_hast?
    nonce = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payload}[{self.block_id}]"



