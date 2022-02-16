import os
import requests
import re
import time
import sys
import random
from threading import Thread
from bs4 import BeautifulSoup
import hashlib

def get_payload_str_for_hash(soup):
    result = soup.find_all(
        'script', {'id': 'payload_str_for_hash'})[0].text
    return result


def get_prev_hash(soup):
    prev_hash = soup.find_all(
        'script', {'id': 'prev_hash'})[0].text
    prev_hash = prev_hash.replace('"', '')
    return prev_hash
    
def get_block_num(soup):
    return soup.find_all(
        'script', {'id': 'block_num'})[0].text


def get_csrf_token(html):
    match = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise ValueError("Unable to extract csrfmiddlewaretoken")
    return match[1]


def no_transactions_to_mine(html):
    return re.search(r"Der er ingen transaktioner", html)


def get_miner_id(html):
    match = re.search(r'minearbejder-ID = ([a-z0-9]{8})', html)
    if not match:
        raise ValueError("Unable to extract miner id / bot id")
    return match[1]


def get_hash_rules(html):
    if re.search(r"Gyldige hashes starter med 0 eller 1", html): 
        return ['0', '1']

    if re.search(r"Gyldige hashes starter med 00", html):
        return ['00']

    if re.search(r"Gyldige hashes starter med 0", html):
        return ['0']

    raise ValueError("Unable to extract valid start characters (hash rules)")


def sim_is_paused(html):
    match = re.search("på pause", html)
    if match:
        return True
    else:
        return False


def get_hash(html):
    match = re.search(
        r"nonce [0-9]+\)<br>\n\s+<small>([0-9a-z]+)</small>", html)
    if not match:
        if re.search(r"før dig!", html):
            return "Hash was not calculated (block already claimed by another miner)"
        else: 
            return "Unable to extract hash"
            #raise ValueError("Unable to extract hash")
    else: 
        return match[1]


def block_added_success(html):
    if re.search(r"belønning", html):
        return True
    else: 
        return False


def block_claimed_by_another_miner(html):
    if re.search(r"før dig", html):
        return True
    else:
        return False


def tried_to_add_invalid_hash(html):
    if re.search(r"ikke gyldigt proof-of-work", html):
        return True
    else:
        return False
                    

class Bot():
    def __init__(self, name, controller):
        self.session = requests.Session()
        self.name = name
        self.miner_id = None
        self.base_url = controller.base_url
        self.blockchain_id = controller.blockchain_id
        self.controller = controller
        self.tries_since_last_win = 0
        self.tries_to_win = []
         

    def join_blockchain(self):
        response = self.session.get(self.base_url)

        data = {'csrfmiddlewaretoken': get_csrf_token(response.text),
                'name': self.name,
                'blockchain_id': self.blockchain_id,
                'join_bc': 'submit'}

        response = self.session.post(self.base_url, data=data)


        # Create bot_library folder if it does not exists
        if not os.path.exists('bot_library'):
            os.makedirs('bot_library')

        # New bot joined successfully
        if response.url == self.base_url + "/minedrift/":
            response = self.session.get(self.base_url + "/deltagere")
            self.miner_id = get_miner_id(response.text)

            # Save the bot id / miner id to be able to rejoin later
            with open(f"bot_library/{self.blockchain_id}_{self.name}.miner.bot", "w") as f:
                f.write(self.miner_id)


        # Bot could not join (likely the name is already in use)
        # To try join as existing user
        else:
            try:
                # Read bot id / miner id from disk
                with open(f"bot_library/{self.blockchain_id}_{self.name}.miner.bot", "r") as f:
                    self.miner_id = f.readline().strip()

            except:
                print("Failed to login as new bot and failed to find stored bot miner id")
                sys.exit()

            data = {'csrfmiddlewaretoken': get_csrf_token(response.text),
                    'blockchain_id': self.blockchain_id,
                    'miner_id': self.miner_id,
                    'login': 'submit'}

            response = self.session.post(self.base_url, data=data)

            if response.url != self.base_url + "/minedrift/":
                print("Failed to join blockchain.")
                sys.exit()
        
        print(f"  Mining bot with name '{self.name}' and miner-id {self.miner_id} joined blochchain {self.blockchain_id}")
  

    def simulate_human_time_delay(self):
        tiny_random_delay = random.uniform(0.4, 2)
        time.sleep(tiny_random_delay)


    def calculate_hash(self, html, nonce):
        soup = BeautifulSoup(html)
        block_num = get_block_num(soup)
        payload_str = get_payload_str_for_hash(soup)
        prev_hash = get_prev_hash(soup)
        
        to_be_encoded = f"{block_num}{self.name}{prev_hash}{payload_str}{nonce}"
        to_be_encoded = to_be_encoded.replace('"', '')
        hash = hashlib.sha256(to_be_encoded.encode()).hexdigest()
        
        return hash

    def hash_is_valid(self, hash):
        if [x for x in self.controller.start_chars if hash.startswith(x)]:
            return True
        else:
            return False


    def start_mining(self):

        while True:

            response = self.session.get(self.base_url + "/minedrift/")

            # Detect paused block chains 
            if sim_is_paused(response.text):
                print(f"  {self.name}: Mining paused by blockchain owner")
                time.sleep(3)
                continue 

            # Generate nonce and calculate hash
            block_num = get_block_num(BeautifulSoup(response.text))
            nonce = random.randint(0, 1000)
            hash = self.calculate_hash(response.text, nonce)
            self.tries_since_last_win += 1
            print(
                f"  {self.name}: Got hash: {hash[:5]}... when trying nonce {int(nonce)} on block #{block_num}")

            # We want bots to try to add block to chain when hash is valid and in some other random cases 
            chance = random.uniform(0, 1) < 0.20
            if self.hash_is_valid(hash) or chance:
                print(f"  {self.name}: Valid hash! Trying to add block to chain")

                data = {'csrfmiddlewaretoken': get_csrf_token(response.text),
                        'nonce': str(nonce)}
                response = self.session.post(self.base_url + "/minedrift/", data=data)

                if block_added_success(response.text):
                    self.tries_to_win.append(self.tries_since_last_win)
                    tries_avg = sum(self.tries_to_win)/len(self.tries_to_win)
                    print(
                        f"  {self.name}: Won block {block_num}. Tries to win: {self.tries_to_win} (avg. {tries_avg:.1f})")
                    self.tries_since_last_win = 0

                elif block_claimed_by_another_miner(response.text):
                    print(f"  {self.name}: Lost block {block_num}, another miner claimed it first!")

                elif tried_to_add_invalid_hash(response.text):
                    print(
                        f"  {self.name}: Error:Tried to add block {block_num} with invalid hash")

                else: 
                    print(response.text)
                    raise ValueError("Unable to extract submission status")

            nonce += 1
            
            self.simulate_human_time_delay()
 

class Controller():

    def __init__(self, params):
        self.blockchain_id = params['blockchain_id']
        self.bot_name = params['bot_name']
        self.num_bots = params['num_bots']
        self.host = params['host']

        self.base_url = None
        self.start_chars = None

        self.set_base_url()        
        self.set_start_chars()


    def set_base_url(self):
        if self.host == 'prod':
            self.base_url = "https://blockchain-sim.dataekspeditioner.dk"
        else:
            self.base_url = "http://127.0.0.1:8000"
            
    def set_start_chars(self):
        helper_bot = Bot("inactive-helper-bot", self)
        helper_bot.join_blockchain()
        response = helper_bot.session.get(self.base_url + "/minedrift")
        self.start_chars = get_hash_rules(response.text)  
        print(f"  Valid hashes begin with: {self.start_chars}")

        
    def start_bot(self, name):
        bot = Bot(name, self)
        bot.join_blockchain()
        bot.start_mining()


    def start_bots(self):
        for i in range(self.num_bots):
            bot_name = f"{self.bot_name}{i}" 
            t = Thread(target=self.start_bot, args=(bot_name,))
            t.start()


if __name__ == '__main__':

    try:
        command_line_parameters = {
            'blockchain_id': sys.argv[1],
            'bot_name': sys.argv[2],
            'num_bots': int(sys.argv[3]),
            'host': sys.argv[4]
        }
      
    except (IndexError, ValueError) as e:
        print(f"Usage: {sys.argv[0]} <blockchain id> <bot name> <number of bots> <host>")
        print(f"e.g. {sys.argv[0]} be8837e3 Bot 5 local")
        print(f"e.g. {sys.argv[0]} be8837e3 Bot 5 prod")

        sys.exit()
    
    else:
        controller = Controller(command_line_parameters)
        controller.start_bots()


