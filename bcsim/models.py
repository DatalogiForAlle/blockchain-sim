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
    is_paused = models.BooleanField(default=False)

    is_simple = models.BooleanField(default=True)    

    class Type(models.IntegerChoices):
        SIMPLE = 1, ('Uden token-marked')
        COMPLEX = 2, ('Med token-marked')

    type = models.PositiveSmallIntegerField(
        choices=Type.choices,
        default=Type.SIMPLE
    )

    class Level(models.IntegerChoices):
        EASY = 1, ('Nem')
        MEDIUM = 2, ('Middel')
        DIFFICULT = 3, ('Svær')

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
        blockchain_is_brand_new = not self.id 
        if blockchain_is_brand_new: 
            self.id = new_unique_blockchain_id()
        super(Blockchain, self).save(*args, **kwargs)
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.save()

    def hash_is_valid(self, hash):

        if self.difficulty == Blockchain.Level.EASY:
            if hash[0] in ["0", "1"]:
                return True

        elif self.difficulty == Blockchain.Level.MEDIUM:
            if hash[0] == "0":
                return True

        elif self.difficulty == Blockchain.Level.DIFFICULT:
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
    is_creator = models.BooleanField(default=False)
    number_of_last_block_seen = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name}[{self.id}]"

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

    def add_miner_reward(self):
        self.balance += 100
        self.save()
        
    def missed_last_block(self):
        current_block_num = Block.objects.filter(
            blockchain=self.blockchain).count()
        return current_block_num != self.number_of_last_block_seen


    def color(self):
        """
        Get the unique color identifying the miner in question. 
        
        The first 38 miners who join a blockchain will get a color from from this list collection of nice colors
        https: // davidpiesse.github.io/tailwind-md-colours /
        (more colors can be added from the list if needed)
        
        The following miners will get a randomly generated color.
        """
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


class Token(models.Model):
    owner = models.ForeignKey(Miner, on_delete=models.CASCADE)
    seed = models.CharField(max_length=10)
    price = models.IntegerField(null=True, blank=True)

    def for_sale(self):
        is_for_sale = self.price is not None
        return is_for_sale

    def blockchain(self):
        return self.owner.blockchain


class Transaction(models.Model):
    sender = models.ForeignKey(
        Miner, on_delete=models.CASCADE, null=True, blank=True, related_name='sender')
    recipient = models.ForeignKey(
        Miner, on_delete=models.CASCADE, null=True, blank=True, related_name='recipient')
    amount = models.IntegerField()
    token = models.ForeignKey(Token, on_delete=models.CASCADE)


class Block(models.Model):

    # block_num is not primary_key, as it is only unique together w. the blockchain
    # block_num is None untill block is validated
    block_num = models.IntegerField(primary_key=False, null=True, blank=True)

    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    miner = models.ForeignKey(Miner, on_delete=models.CASCADE)

    nonce = models.IntegerField(null=True, blank=True)

    prev_hash = models.CharField(max_length=200)

    # transaction will be None when there is no token market
    transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.CASCADE)

    def hash(self):
        s = f"{self.block_num}{self.miner.name}{self.prev_hash}{self.payload_str}{self.nonce}"
        hash = hashlib.sha256(s.encode()).hexdigest()
        return hash

    def hash_is_valid(self):
        hash = self.hash()
        return hash, self.blockchain.hash_is_valid(hash)


    def payload_str(self):

        if self.block_num == 0:
            return 'Genesis'

        first_names = ('John', 'Andy', 'Joe', 'Sandy', 'Sally',
                    'Alice', 'Joanna', 'Serena', 'Oliver', 'Steven')

        last_names = ('Johnson', 'Smith', 'Williams', 'Brown',
                    'Silbersmith', 'Garcia', 'Miller', 'Davis', 'Jones', 'Lopez')

        random.seed(self.blockchain.id + str(self.block_num))

        sender = f"{random.choice(first_names)} {random.choice(last_names)}"
        recipient = f"{random.choice(first_names)} {random.choice(last_names)}"

        amount = random.randint(1, 100)

        return f"{amount} DIKU-coins fra {sender} til {recipient}"

