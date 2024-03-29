#!/usr/bin/env sh

NCORES=3

date

for i in `seq 1 ${NCORES}`; do
    flux mini submit -N 1 -n 1 flux start ./ensemble.sh
done

flux queue drain
echo "First Level Done"

date
