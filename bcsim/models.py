from ssl import HAS_NEVER_CHECK_COMMON_NAME
from django.db import models
import secrets
import hashlib
import random
from .animal_avatar.animal_avatar import Avatar
from time import perf_counter


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
    creator_name = models.CharField(max_length=36, default="Skaber")
    title = models.CharField(max_length=50, default="Transaktioner")
    created_at = models.DateTimeField(auto_now_add=True)
    is_paused = models.BooleanField(default=False)
    
    # Class constants 
    MINER_REWARD = 100
    BANK_TOKEN_PRICE = 150
    NUM_INITIAL_TRANSACTIONS_PR_MINER = 2
    NUM_TOKENS_FOR_SALE_IN_BANK_AT_ALL_TIMES = 3
    ADD_TO_CHAIN_TIME_DELAY_IN_SECONDS = 2 
    
    class Type(models.IntegerChoices):
        HAS_NO_TOKENS = 1, ('Uden NFT-marked')
        HAS_TOKENS = 2, ('Med NFT-marked')

    type = models.PositiveSmallIntegerField(
        choices=Type.choices,
        default=Type.HAS_NO_TOKENS
    )

    class Level(models.IntegerChoices):
        EASY = 1, ('Nem')
        MEDIUM = 2, ('Middel')
        DIFFICULT = 3, ('Svær')

    difficulty = models.PositiveSmallIntegerField(
        choices=Level.choices,
        default=Level.MEDIUM
    )

    def _create_initial_transaction(self, miner):
        """ Create 1 initial transaction for new miner """
        nft_bank = self.get_bank()

        token = Token.objects.create(
            blockchain=self,
            owner=nft_bank,
            price=None,
            transaction_in_process=True,
        )

        Transaction.objects.create(
            buyer=miner,
            seller=nft_bank,
            token=token,
            blockchain=self,
            processed=False,
            amount=0
        )


    def create_initial_transactions(self, miner):
        """ Create initial transactions for new miner """
        for _ in range(Blockchain.NUM_INITIAL_TRANSACTIONS_PR_MINER):
            self._create_initial_transaction(miner)
    
    
    def add_token_to_bank(self, number_of_tokens_to_add=1):
        for _ in range(number_of_tokens_to_add):
            Token.objects.create(
                blockchain=self,
                owner=self.get_bank(),
                price=Blockchain.BANK_TOKEN_PRICE,
                transaction_in_process = False
            )

    def get_bank(self):
        nft_bank = Miner.objects.get(blockchain=self, name='NFT-banken')
        return nft_bank

    def has_tokens(self):
        return self.type == self.Type.HAS_TOKENS

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

    def get_unprocessed_transactions(self):
        if self.has_tokens():
            unprocessed_transactions = Transaction.objects.filter(
                    blockchain=self, processed=False)
            if unprocessed_transactions.count() == 0:
                next_transaction = None
            else:
                next_transaction = unprocessed_transactions.first()
        else:
            unprocessed_transactions = None
            next_transaction = None
        return unprocessed_transactions, next_transaction

    def create_genesis_block(self, creator):
        
        genesis_hash_is_valid = False
        nonce = 0

        while not genesis_hash_is_valid:

            block = Block(
                block_num=0,
                blockchain=self,
                miner=creator,
                nonce=str(nonce),
                prev_hash="—"
            )
            _, genesis_hash_is_valid = block.hash_is_valid()

            nonce += 1

        block.save()

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
    balance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_creator = models.BooleanField(default=False)
    number_of_last_block_seen = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        """ Set unique id and miner_num for miner before creating a new miner object """
        if not self.id:
            # we are creating a new miner (not updating an existing miner)
            self.id = new_unique_miner_id()
            self.miner_num = Miner.objects.filter(
                blockchain=self.blockchain).count()
        super(Miner, self).save(*args, **kwargs)

    def num_mined_blocks(self):
        """ Number of mined blocks (genesis block not included) """
        num_mined_blocks = Block.objects.filter(
            miner=self, block_num__gte=1).count()
        return num_mined_blocks

    def add_miner_reward(self):
        self.balance += self.blockchain.MINER_REWARD
        self.save()

    def missed_last_block(self):
        current_block_num = Block.objects.filter(
            blockchain=self.blockchain).count()
        return current_block_num != self.number_of_last_block_seen

    def tokens(self):
        return Token.objects.filter(owner=self)

    def can_buy_token(self, token):
        if token.transaction_in_process:
            return False
        if token.owner == self:
            return False
        if not token.price:
            return False
        if self.balance < token.price:
            return False
        return True

    def number_of_tokens(self):
        return Token.objects.filter(owner=self).count()

    def color(self):
        """
        Get the unique color identifying the miner in question. 

        The first 37 miners who join a blockchain will get a color from from this list collection of nice colors
        https: // davidpiesse.github.io/tailwind-md-colours /
        (more colors can be added from the list if needed)

        The following miners will get a randomly generated color.
        """
        NICE_COLORS = [
            "#b3e5fc", "#dcedc8", "#ffcdd2", "#ff8a80", "#ff80ab", "#ea80fc", "#b388ff", "#42a5f5", "#03a9f4", "#26c6da",
            "#26a69a", "#8bc34a", "#dce775", "#ffee58", "#ffca28", "#ffa726", "#ff7043", "#c5cae9", "#b2dfdb", "#a7ffeb",
            "#fff9c4", "#f8bbd0", "#bbdefb", "#c8e6c9", "#ffecb3", "#e1bee7", "#69f0ae", "#ffe0b2", "#ffd180", "#d1c4e9", 
            "#b2ebf2", "#84ffff", "#f0f4c3", "#f4ff81", "#ffccbc",  "#ff9e80", "#b2ff59", ]

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
    
    def has_trade_in_process_as_buyer(self):
        transactions_in_process = Transaction.objects.filter(
            processed=False, buyer=self, amount__gt=1)
        
        for t in transactions_in_process:
            print(t.amount)
        if transactions_in_process.exists():
            return True
        else: 
            return False

def create_random_avatar_seed():
    """ Create random seed for Tokens """
    random.seed(perf_counter())

    random_seed = "".join(random.sample(
        "abcdefghijklmnopqrstuvxyz0123456789", 10))

    return random_seed

class Token(models.Model):
    blockchain = models.ForeignKey(
        Blockchain, null=True, blank=True, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        Miner, null=True, blank=True, on_delete=models.CASCADE)
    seed = models.CharField(max_length=10)
    price = models.IntegerField(null=True, blank=True)
    transaction_in_process = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.id:
            # we are creating a new miner (not updating an existing miner)
            self.seed = create_random_avatar_seed()
        super(Token, self).save(*args, **kwargs)

    def is_for_sale(self):
        return (self.price is not None) and (self.price > 0) and (not self.transaction_in_process)

    def big_svg(self):
        avatar = Avatar(self.seed, size=160)
        svg = avatar.create_avatar()
        return svg

    def small_svg(self):
        avatar = Avatar(self.seed, size=60)
        svg = avatar.create_avatar()
        return svg

    def in_queue_for_initial_transaction(self):
        owned_by_bank = (self.owner == self.blockchain.get_bank())
        price_is_none = (self.price is None)
        return (price_is_none and owned_by_bank)

class Transaction(models.Model):
    """
    Transactions are generated in 2 different situations:
    1. A new token is created when miner is joining game
        buyer = the miner
        seller = NFT-bank
        amount = 0
        token = Token(owner=NFT-bank, price=0)

    2. A miner tries to buy a token from another miner (possible the NFT-bank)
        buyer = the miner buying the token
        seller = the miner selling the token (possible the NFT-bank)
        amount > 0
        token = token(owner=seller, price > 0)
    """
    blockchain = models.ForeignKey(
        Blockchain, null=True, on_delete=models.CASCADE)

    # The buyer is the miner paying the money (or the miner receiving the token in the case of an initial transactions)
    buyer = models.ForeignKey(
        Miner, on_delete=models.CASCADE, null=True, related_name='buyer')

    # The seller is the miner receiving the money (will be None for initial transactions)
    seller = models.ForeignKey(
        Miner, on_delete=models.CASCADE, null=True, related_name='seller')

    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    processed = models.BooleanField(default=False)

    amount = models.IntegerField(null=True)

    def is_valid(self):

        if not self.buyer.balance >= self.amount:
            return False, "Køberen har ikke penge nok"

        if not self.token.owner == self.seller:
            return False, "Sælgeren ejer ikke længere tokenet"

        if not self.token.in_queue_for_initial_transaction():
            if not self.token.price:
                return False, "Tokenet er ikke til salg"

        if self.processed: 
            return False, "Transaktionen er allerede behandlet"

        return True, ""



    def process(self, miner):

        transaction_is_valid, error_message = self.is_valid()

        if transaction_is_valid:
            # update token
            self.token.transaction_in_process = False
            self.token.price = None
            self.token.owner = self.buyer
            self.token.save()

            # update buyer 
            self.buyer.balance -= self.amount
            self.buyer.save()

            # update seller
            self.seller.balance += self.amount
            self.seller.save()

            # add miner reward
            miner.refresh_from_db()
            miner.add_miner_reward()

        else:
            self.token.transaction_in_process = False
            self.token.price = None
            self.token.save()

            
        self.processed = True
        self.save()

        return transaction_is_valid, error_message

    def is_initial_transaction(self):
        return self.amount == 0


    def payload_str(self):
        """ 
        Payload string to be shown in user interface 
        Only used when blockchain has NFt-market
        """

        if self.is_initial_transaction():
            payload = f"{self.token.small_svg()} til <b>{self.buyer.name}</b> fra NFT-banken"

        else:
            payload = f"{self.token.small_svg()} til <b>{self.buyer.name}</b> fra {self.seller.name}  for {self.amount} DIKU-coins"

        return payload


    def payload_str_for_hash(self):
        """ 
        Payload string used when calculating hash of block 
        Only used when blockchain has NFt-market
        """
        if self.is_initial_transaction():
            payload = f"{self.token.seed} til {self.buyer.name} fra NFT-banken"

        else:
            payload = f"{self.amount} DIKU-coins fra {self.buyer.name} til {self.seller.name} for {self.token.seed}"

        return payload


class Block(models.Model):

    # block_num is not primary_key, as it is only unique together w. the blockchain
    # block_num is None untill block is validated
    block_num = models.IntegerField(primary_key=False, null=True, blank=True)

    blockchain = models.ForeignKey(Blockchain, on_delete=models.CASCADE)

    miner = models.ForeignKey(Miner, on_delete=models.CASCADE)

    nonce = models.IntegerField(null=True, blank=True)

    prev_hash = models.CharField(max_length=200)

    # transaction will be None when there is no token market
    transaction = models.ForeignKey(
        Transaction, null=True, blank=True, on_delete=models.CASCADE)

    def string_to_be_hashed(self):
        """ 
        Generates the string to be hashed
        Used only in the case of blockchain with no NFT-market 
        """
        if self.block_num == 0:
            payload_str = 'Genesis'
        elif not self.blockchain.has_tokens():
            payload_str = self.random_payload_str()
        else:
            payload_str = self.transaction.payload_str_for_hash()
        s = f"{self.block_num}{self.miner.name}{self.prev_hash}{payload_str}{self.nonce}"
        return s

    def hash(self):
        to_be_encoded = self.string_to_be_hashed()
        hash = hashlib.sha256(to_be_encoded.encode()).hexdigest()
        return hash

    def hash_is_valid(self):
        hash = self.hash()
        return hash, self.blockchain.hash_is_valid(hash)

    def random_payload_str(self):
        """ Generates random payload string (used in games with no token market) """

        if self.block_num == 0:
            return 'Genesis'

        first_names = ('John', 'Andy', 'Joe', 'Sandy', 'Sally',
                       'Alice', 'Joanna', 'Serena', 'Oliver', 'Steven')

        last_names = ('Johnson', 'Smith', 'Williams', 'Brown',
                      'Silbersmith', 'Garcia', 'Miller', 'Davis', 'Jones', 'Lopez')

        random.seed(self.blockchain.id + str(self.block_num))

        buyer = f"{random.choice(first_names)} {random.choice(last_names)}"
        seller = f"{random.choice(first_names)} {random.choice(last_names)}"

        amount = random.randint(1, 100)

        return f"{amount} DIKU-coins fra {buyer} til {seller}"
