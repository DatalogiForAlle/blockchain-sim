from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import secrets
import hashlib
import random

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
    creator_name = models.CharField(max_length=36,default="Skaber")
    title = models.CharField(max_length=50, default="Transaktioner")
    created_at = models.DateTimeField(auto_now_add=True)
    paused = models.BooleanField(default=False)

    class Level(models.IntegerChoices):
        NEM = 1
        MEDIUM = 2
        SVÆR = 3

    difficulty = models.PositiveSmallIntegerField(
        choices=Level.choices, 
        default=Level.MEDIUM
    )

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
    
    def hash_is_valid(self, hash):

        if self.difficulty == Blockchain.Level.NEM:
            if hash[0] in ["0", "1"]:
                return True

        elif self.difficulty == Blockchain.Level.MEDIUM:
            if hash[0] == "0":
                return True

        elif self.difficulty == Blockchain.Level.SVÆR:
            if hash[:2] == "00":
                return True

        return False
    
    
def new_unique_miner_id():
    """
    Create a new unique blockchain ID (8 alphabetic chars)
    """
    while True:
        miner_id = secrets.token_hex(4)
        if not Miner.objects.filter(id=miner_id).exists():
            break
    return miner_id


class Miner(models.Model):
    id = models.CharField(max_length=16, primary_key=True)
    miner_num = models.IntegerField(primary_key=False, null=True)
    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)
    name = models.CharField(max_length=36,)
    balance = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Set unique custom id for miner before creating a new blockchain object
        """
        if not self.id:
            # we are creating a new miner (not updating an existing miner)
            self.id = new_unique_miner_id()
        super(Miner, self).save(*args, **kwargs)

    def num_mined_blocks(self):
        """ Number of mined blocks (genesis block not included) """
        num_mined_blocks = Block.objects.filter(miner=self, block_num__gte=1).count()
        return num_mined_blocks

    def color(self):
        """
        Get the unique color identifying the miner in question. 
        """

        # The 38 nice colors are from this list: https: // davidpiesse.github.io/tailwind-md-colours /
        # (more colors can be added from the list if needed)
        
        NICE_COLORS = [
            "#b3e5fc", "#dcedc8", "#ffcdd2", "#ff8a80", "#ff80ab", "#ea80fc", "#b388ff", "#42a5f5", "#03a9f4", "#26c6da",
            "#26a69a", "#8bc34a", "#dce775", "#ffee58", "#ffca28", "#ffa726", "#ff7043", "#c5cae9", "#b2dfdb", "#a7ffeb",
            "#fff9c4", "#f8bbd0", "#bbdefb", "#c8e6c9", "#ffecb3", "#e1bee7", "#69f0ae", "#ffe0b2", "#ffd180", "#cfd8dc",
            "#d1c4e9", "#b2ebf2", "#84ffff", "#f0f4c3", "#f4ff81", "#ffccbc",  "#ff9e80", "#b2ff59", ]

        # We want a random ordering of the colors
        random.seed(self.blockchain.id)
        random.shuffle(NICE_COLORS)

        i = self.miner_num
        if i < len(NICE_COLORS):
            color = NICE_COLORS[i]
        else:
            red = (100 + i*100) % 255
            green = (50 + int((i/3)*100)) % 255
            blue = (0 + int((i/2)*100)) % 255
            color = f"rgb({red},{green},{blue}, 0.3)"
        return color

MAX_NONCE = 2**32 - 1

class Block(models.Model):

    # block_num is not primary_key, as it is only unique together w. the blockchain
    block_num = models.IntegerField(primary_key=False)

    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    miner = models.ForeignKey(Miner, on_delete=models.CASCADE)

    payload = models.CharField(max_length=200)

    nonce = models.IntegerField(null=True, blank=False)

    prev_hash = models.CharField(max_length=200)

    def hash(self):
        s = f"{self.block_num}{self.miner.name}{self.prev_hash}{self.payload}{self.nonce}"
        hash = hashlib.sha256(s.encode()).hexdigest()
        return hash

    def hash_is_valid(self):
        hash = self.hash()
        return hash, self.blockchain.hash_is_valid(hash)


class Token(models.Model):
    miner_id = models.ForeignKey(Miner, on_delete=models.CASCADE)
    seed = models.CharField(max_length=10)
