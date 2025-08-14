#!/bin/bash

set -euo pipefail

# Set a jobid
jobid=structure_099868581
outpath=/workdir/out
mkdir -p $outpath

MUMMI_APP=/opt/clones/mummi-ras MUMMI_ROOT=$MUMMI_APP
MUMMI_RESOURCES=/opt/clones/mummi_resources
export MUMMI_ROOT MUMMI_APP MUMMI_RESOURCES
export OMPI_COMM_WORLD_RANK=1
export OMP_NUM_THREADS=64

simname=${jobid}
locpath=/tmp/workdir
mv /tmp/out ${locpath}
mkdir -p ${outpath}; cd ${locpath} 
ls
cframe=0
touch /tmp/workdir/cg_analysis.out
touch /tmp/workdir/cg_analysis.log
mummi_cganalysis \
    --simname ${jobid} \
    --path $locpath \
    --pathremote $outpath \
    --siminputs $outpath \
    --fstype mummi \
    --fbio mummi \
    --simbin gmx \
    --backend GROMACS \
    --simcores ${OMP_NUM_THREADS} \
    --nprocs 1 \
    --stopsimtime 100 \
    --frameProcessBatchSize 10 \
    --simruntime 0.1 \
    --logstdout \
    --loglevel 2 \
    --mini \
    --no-gpu \
    --fcount $cframe
echo $?
echo "cganalysis output:"
tree /workdir/out
