# Flux Jupyter Tutorial

This set of tutorials provides:

 - [Building Tutorial Images](#build-images)
 - [Introduction to Flux](#introduction-to-flux)
 - [The Flux Operator with Agents](#the-flux-operator-with-agents)

Pre-requisites:

 - Docker client installed locally
 - Excitement to learn about Flux!

## Build Images

Build the tutorial images.

```bash
docker build -f ./docker/Dockerfile -t hpsf-flux .
docker build -f ./docker/Dockerfile.ml -t hpsf-flux-ml .
docker build -f ./docker/Dockerfile.flux-operator -t ghcr.io/flux-framework/tutorials:flux-operator-pytorch .
```

## 1. Introduction to Flux 

The introduction to Flux section is a notebook. You can simply run the Image.

```bash
docker run --rm -it  -v /var/run/docker.sock:/var/run/docker.sock --name jupyterhub  -p 8888:8888 hpsf-flux
```

## 2. The Flux Operator with Agents

The Flux Operator and MCP example is a Flux Framework MiniCluster. Either create a cloud (or have) a Kubernetes cluster, or create one with kind:

```bash
kind create cluster --config ./flux-operator/kind-config.yaml
kind load docker-image ghcr.io/flux-framework/tutorials:flux-operator-pytorch
```
Install the Flux Operator:

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/refs/heads/main/examples/dist/flux-operator.yaml
```

Wait until both ranks are running, then shell inside and connect to the lead broker.

```bash
kubectl get pods --watch
kubectl exec -it pytorch-0-xxxx -- bash
. /mnt/flux/flux-view.sh
flux proxy $fluxsocket bash
flux resource list
```

Now let's run Pytorch, without agents. There is a simple "hello world" and training example with cifar.

```bash
flux run -N 2 --exclusive python distributed_flux_hello_world.py
flux run -N 2 --exclusive python distributed_flux.py 
```

We could also put `-n` for the number of tasks (processes) per node, but exclusive will ask for all of them.


## 3. Kubeflow and Flux

The Kubeflow and Flux example can use the same cluster, but we add Kubeflow.

**TODO**

