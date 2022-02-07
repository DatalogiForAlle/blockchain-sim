"""
Script used in development to calibrate the difficulty levels of diffent hash criteria
To run it from command line:
$ python3 hash_test.py
"""

from random import randrange
import hashlib


EASY = 0
MEDIUM = 0
HARD = 0

N = 100000

for _ in range(N):

    s = "vrøvl" + str(randrange(4000000000)) + "sludder"
    hash = hashlib.sha256(s.encode()).hexdigest()

    if hash[0] in ["0", "1"]:
        EASY += 1

    if hash[0] == "0":
        MEDIUM += 1

    if hash[:2] in ["00", "11", "22"]:
        HARD += 1

print(EASY/N)
print(MEDIUM/N)
print(HARD/N)
