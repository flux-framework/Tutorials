#!/usr/bin/env sh

NJOBS=750
MAXTIME=$(expr ${NJOBS} + 2)

for i in `seq 1 ${NJOBS}`; do
    flux mini submit --nodes=1 --ntasks=1 --cores-per-task=1 sleep 0
done

flux jobs 
flux queue drain
echo "Final Level Done"
