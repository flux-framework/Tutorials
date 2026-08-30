#!/bin/bash
#FLUX: --nodes=2
#FLUX: --nslots=2
#FLUX: --cores-per-slot=1

echo "Starting my batch job"
echo "Print the resources allocated to this batch job"
flux resource list

echo "Use sleep to emulate a parallel program"
echo "Run the program at a total of 2 processes each requiring"
echo "1 core. These processes are equally spread across 2 nodes."
flux run -N 2 -n 2 sleep 30
flux run -N 2 -n 2 sleep 30

