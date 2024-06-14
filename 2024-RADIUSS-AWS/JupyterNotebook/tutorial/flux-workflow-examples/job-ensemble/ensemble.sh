#!/usr/bin/env sh

NJOBS=10
MAXTIME=$(expr ${NJOBS} + 2)
JOBIDS=""

JOBIDS=$(flux mini submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua ${MAXTIME})
for i in `seq 1 ${NJOBS}`; do
    JOBIDS="${JOBIDS} $(flux mini submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 1)"
done

flux jobs
flux queue drain

# print mock-up prevenance data
for i in ${JOBIDS}; do
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Jobid: ${i}"
    KVSJOBID=$(flux job id --from=dec --to=kvs ${i})
    flux kvs get ${KVSJOBID}.R | jq
done
