#!/bin/bash

flux mini batch -N1 ./sub_job2.sh
flux queue drain

