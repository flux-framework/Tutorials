#!/bin/bash

set -euo pipefail

mummi_mlserver_nnodes=1
MUMMI_APP=/opt/clones/mummi-ras

# Prepare output directory
outdir=/workdir
outpath=/workdir/tmp
mkdir -p $outpath
cd $outdir

export MUMMI_ROOT=$MUMMI_APP
export MUMMI_RESOURCES=/opt/clones/mummi_resources
export MUMMI_APP
model="/opt/clones/mummi_resources/ml/chonky-model/CG_pos_data_summary_pos_dis_C1_v1.npz"
ws=/opt/clones/mummi-ras/mlserver

# Shared output for validator, sampler, and generator
mldir=/opt/clones/mummi-ras/mlserver
resources="martini3-validator"
complex="ras-rbdcrd-ref-CG.gro"
cmd="mummi-ml start --jobid structure_000001 --workspace=${ws} --outdir=${outpath} --tag mlrunner --plain-http --encoder-model ${model} --ml-outdir=${mldir} --resources ${resources} --complex=${complex}"

mkdir -p /opt/clones/extract
cd /opt/clones/extract
tar --touch -xzvf /opt/clones/model.tar.gz
extracted=$(ls /opt/clones/extract)
cd -
mv /opt/clones/extract/${extracted} /opt/clones/mummi_resources/ml/chonky-model

# nproc is OK to run on an arm instance - will return physical cores
NUM_THREADS=$(nproc)
export OMP_NUM_THREADS=$NUM_THREADS
echo "Running with ${NUM_THREADS} cpu"
export KERAS_BACKEND='theano'
umask 007
python $MUMMI_APP/mummi_ras/scripts/create_organization.py

# Trajectory feedback files
here=$(pwd)

cd $here
echo "$cmd"
$cmd

echo "mlrunner output:"
tree /workdir/tmp/
