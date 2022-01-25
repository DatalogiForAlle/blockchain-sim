#!/bin/bash
# Start multiple bots from the command line
# Usage: $ multiple_bots <blockchain id> <bot name> <number of bots>
for i in $(seq $3)
do 
    python3 -u mining_bot.py $1 $2_$i 2 > /tmp/bot_$i.log& 
done