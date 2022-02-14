import os
import requests
import re
import time
import sys
import random
from threading import Thread


def get_csrf_token(html):
    match = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise ValueError("Unable to extract csrfmiddlewaretoken")
    return match[1]


def get_miner_id(html):
    match = re.search(r'minearbejder-ID = ([a-z0-9]{8})', html)
    if not match:
        raise ValueError("Unable to extract miner id / bot id")
    return match[1]


def get_hash_rules(html):
    if re.search(r"Gyldige hashes starter med 0 eller 1", html): 
        print("EASY!!")   
        print(html)
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


def get_block_num(html):
   match = re.search("Blok #([0-9]+)<", html)

   try:
       block_num = int(match[1])
   except ValueError:
       raise ValueError("Unable to extract block id")

   return block_num


def get_hash(html):
    match = re.search(
        r"nonce [0-9]+\)<br>\n\s+<small>([0-9a-z]+)</small>", html)
    if not match:
        if re.search(r"før dig!", html):
            return "Hash was not calculated (block already claimed by another miner)"
        else: 
            raise ValueError("Unable to extract hash")
    else: 
        return match[1]


def block_added_success(html):
    if re.search(r"før dig!", html):
        return False
    elif re.search(r"belønning", html):
        return True
    else:
        print(html)
        raise ValueError("Unable to extract block submission status")


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
            response = self.session.get(self.base_url + "/inviter")
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

    def start_mining(self):

        self.simulate_human_time_delay()

        while True:
            nonce = random.randint(0, 1000)

            response = self.session.get(self.base_url + "/minedrift/")

            # Detect paused block chains 
            if sim_is_paused(response.text):
                print(f"  {self.name}: Mining paused by blockchain owner")
                time.sleep(3)
                continue 

            block_num = get_block_num(response.text)

            # Try nonce
            print(f"  {self.name}: Trying nonce {int(nonce)} on block #{block_num}")
            self.tries_since_last_win += 1

            data = {'csrfmiddlewaretoken': get_csrf_token(response.text),
                    'nonce': str(nonce),
                    'calculate_hash': 'submit'}

            response = self.session.post(self.base_url + "/minedrift/", data=data)

            hash_ = get_hash(response.text)
            print(f"  {self.name}: Got hash: {hash_}")


            # Determine if the hash is valid
            self.simulate_human_time_delay()
            if [x for x in self.controller.start_chars if hash_.startswith(x)]:
                print(f"  {self.name}: Valid hash!")

                data = {'csrfmiddlewaretoken': get_csrf_token(response.text),
                        'nonce': str(nonce),
                        'add_to_chain': 'true'}
                response = self.session.post(self.base_url + "/minedrift/", data=data)

                if block_added_success(response.text):
                    print(f"  {self.name}: Won block {block_num}")
                    self.tries_to_win.append(self.tries_since_last_win)
                    tries_avg = sum(self.tries_to_win)/len(self.tries_to_win)
                    print(
                        f"  {self.name}: Tries to win: {self.tries_to_win} (avg. {tries_avg:.1f})")
                    self.tries_since_last_win = 0

                else:
                    print(
                        f"  {self.name}: Lost block {block_num}, another miner claimed it first!")

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


