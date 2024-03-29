#!/bin/bash

flux submit --flags=waitable -N1 --output=/tmp/hello-batch-1.out echo "Hello job 1 from $(hostname) 💛️"
flux submit --flags=waitable -N1 --output=/tmp/hello-batch-2.out echo "Hello job 2 from $(hostname) 💚️"
flux submit --flags=waitable -N1 --output=/tmp/hello-batch-3.out echo "Hello job 3 from $(hostname) 💙️"
flux submit --flags=waitable -N1 --output=/tmp/hello-batch-4.out echo "Hello job 4 from $(hostname) 💜️"
# Wait for the jobs to finish
flux job wait --all