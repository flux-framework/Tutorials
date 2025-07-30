#!/bin/bash
#FLUX: -N1

flux batch -N1 ./sub_job2.sh
flux queue drain

