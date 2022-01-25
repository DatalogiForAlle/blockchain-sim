import requests
import re
import time
import sys
import random

### Helper functions ###
########################
def get_csrf_token(html):
    match = re.search(r'csrfmiddlewaretoken" value="([^"]+)"', html)
    if not match:
        raise ValueError("Unable to extract csrfmiddlewaretoken")
    return match[1]


def get_miner_id(html):
    match = re.search(r'minearbejder-ID = ([a-z0-9]{8})', r.text)
    if not match:
        raise ValueError("Unable to extract miner id / bot id")
    return match[1]


def sim_is_paused(html):
    match = re.search("på pause", r.text)
    if match:
        return True
    else:
        return False


def get_block_num(html):
   match = re.search("Blok #([0-9]+)<", r.text)

   try:
       block_num = int(match[1])
   except ValueError:
       raise ValueError("Unable to extract block id")

   return block_num


def get_hash(html):
    match = re.search(r"nonce [0-9]+\)<br>\n\s+<small>([0-9a-z]+)</small>", r.text)
    if not match:
        raise ValueError("Unable to extract hash")
    
    return match[1]

def get_hash_rules(html):
    # "Gyldige hashes starter med 0 eller 1"
    match = re.search(r"Gyldige hashes starter med ([^\n<]+)", html)

    if match:
        # "0 eller 1"
        chars = re.findall(r"[0-9]+", match[1])

        if len(chars)>0:
            return chars

    raise ValueError("Unable to extract valid start characters (hash rules)")


def block_added_success(html):

    if re.search(r"før dig!", r.text):
        return False
    elif re.search(r"til blockchainen!", r.text):
        return True
    else:
        raise ValueError("Unable to extract block submission status")
        


### Command line parameters ###
###############################
try:
    blockchain_id = sys.argv[1]
    bot_name = sys.argv[2]
    delay  = float(sys.argv[3]) # Delay between nonce guesses/requests
except (IndexError, ValueError):
    print(f"Usage: {sys.argv[0]} <blockchain id> <bot name> <delay>")
    print(f"e.g. {sys.argv[0]} 0ee59356 Bot 1.5")
    sys.exit()


# Session object
s = requests.Session()
base_url = "https://blockchain-sim.dataekspeditioner.dk"


### Join block chain ###
########################
r = s.get(base_url)

data = {'csrfmiddlewaretoken': get_csrf_token(r.text),
        'name': bot_name,
        'blockchain_id': blockchain_id,
        'join_bc': 'submit'}

r = s.post(base_url, data=data)

# New bot joined successfully
if r.url == base_url + "/minedrift/":
    r = s.get(base_url + "/inviter")
    bot_miner_id = get_miner_id(r.text)

    # Save the bot id / miner id to be able to rejoin later
    with open(f"bot_library/{blockchain_id}_{bot_name}.miner.bot", "w") as f:
        f.write(bot_miner_id)


# Bot could not join (likely the name is already in use)
# To try join as existing user
else:
    try:
        # Read bot id / miner id from disk
        with open(f"bot_library/{blockchain_id}_{bot_name}.miner.bot", "r") as f:
            bot_miner_id = f.readline().strip() 

    except:
        print("Failed to login as new bot and failed to find stored bot miner id")
        sys.exit()

    data = {'csrfmiddlewaretoken': get_csrf_token(r.text),
            'blockchain_id': blockchain_id,
            'miner_id': bot_miner_id,
            'login': 'submit'}

    r = s.post(base_url, data=data)

    if r.url != base_url + "/minedrift/":
        print("Failed to join blockchain.")
        sys.exit()


### Mining loop ###
###################
r = s.get(base_url + "/minedrift/")
start_chars = get_hash_rules(r.text)

print("## Mining bot ##")
print(f"  Joined blockchain {blockchain_id} as bot '{bot_name}' (id: {bot_miner_id})")
print(f"  Valid hashes begin with: {start_chars}")

nonce = random.randint(0,1000)
prev_block_num = 0
tries_since_last_win = 0
tries_to_win = []
while True:


    # Detect paused block chains (unfortunate extra request)
    r = s.get(base_url + "/minedrift/")

    if sim_is_paused(r.text):
        print("  Mining paused by blockchain owner.")
        time.sleep(delay)
        continue

    # Determine if a new block is being mined 
    # or if it is the same block as last iteration
    block_num = get_block_num(r.text)

    if block_num > prev_block_num:

        if prev_block_num != 0:
            print(f"  Another miner won block {prev_block_num}, trying the next!")

        print(f"\n# Trying to mine block {block_num}")
        prev_block_num = block_num
        
        # New block new random nonce
        nonce = random.randint(0,1000)


    # Try new nonce
    print(f"\n  Trying nonce {int(nonce)} (bot: {bot_name})")
    tries_since_last_win += 1

    data = {'csrfmiddlewaretoken': get_csrf_token(r.text),
            'nonce': str(nonce),
            'calculate_hash': 'submit'}

    r = s.post(base_url + "/minedrift/", data=data)
   
    hash_ = get_hash(r.text)
    print("  Hash:", hash_)

    # Determine if the hash is valid
    if [x for x in start_chars if hash_.startswith(x)]:
        print("  Valid hash!")

        data = {'csrfmiddlewaretoken': get_csrf_token(r.text),
                'nonce': str(nonce),
                'add_to_chain': 'true'}
        r = s.post(base_url + "/minedrift/", data=data)

        if block_added_success(r.text):
            print(f"  Won block {block_num}")
            tries_to_win.append(tries_since_last_win)
            tries_avg = sum(tries_to_win)/len(tries_to_win)
            print(f"  Tries to win: {tries_to_win} (avg. {tries_avg:.1f})") 
            tries_since_last_win = 0

        else: 
            print(f"  Lost block {block_num}, another miner claimed it first!")

    nonce = nonce+1
    time.sleep(delay)
