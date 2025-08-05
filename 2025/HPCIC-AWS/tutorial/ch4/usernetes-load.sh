#!/bin/bash

# Load a container into usernetes.
# This is intended for the HPCIC 25 tutorial, hence hard coded paths.

URI=${1:-"ghcr.io/converged-computing/flux-view-rocky:arm-9"}
SAVE_URI=$(echo $URI | tr '/:' '_-').tar
mkdir -p /home/ubuntu/usernetes/images
docker pull $URI
docker save -o /home/ubuntu/usernetes/images/${SAVE_URI} ${URI}

# Using the shared path (usernetes root) tell containerd to load it
docker exec -it usernetes-node-1 ctr --namespace k8s.io image import /usernetes/images/${SAVE_URI}
crictl images | grep ${URI}
