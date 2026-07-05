#!/bin/bash

# Load a container into usernetes.
# This is intended for the HPCIC 25 tutorial, hence hard coded paths.

URI=${1:-"ghcr.io/converged-computing/flux-view-rocky:arm-9"}
SAVE_URI=$(echo $URI | tr '/:' '_-').tar
mkdir -p /home/ubuntu/usernetes/images
docker pull $URI
echo "Saving ${URI} to ${SAVE_URI} for loading..."
docker save -o /home/ubuntu/usernetes/images/${SAVE_URI} ${URI}

# Using the shared path (usernetes root) tell containerd to load it
echo "Importing ${URI} into usernetes node"
docker exec -it usernetes-node-1 ctr --namespace k8s.io image import /usernetes/images/${SAVE_URI}
docker exec -it usernetes-node-1 crictl images | grep ${URI}

# Times hpc7g with g3
# make up -> cluster 116 seconds
# pulling mlrunner: 5m55s to running
# pull to load lammps efa container: 7m
# just to load from .tar: 2m 59s.
