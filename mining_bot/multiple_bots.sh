#!/bin/bash
# Start multiple bots from the command line
# Usage: sh multiple_bots.sh <blockchain id> <bot name> <delay> <number of bots> <host>
# Example 1: sh multiple_bots.sh 548c3f11 charlotte 2 5 local 
# Example 2: sh multiple_bots.sh 548c3f11 charlotte 2 5 prod

echo Starting $4 bots 
echo Blockchain-ID: $1
echo Bot names: $2_1, $2_2, ...
echo Delay: $3
echo Host: $5

for i in $(seq $4)
do 
    python3 -u mining_bot.py $1 $2_$i 2 $5 > /tmp/bot_$i.log& 
done