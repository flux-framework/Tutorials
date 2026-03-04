# Flux Jupyter Tutorial

This set of tutorials provides:

 - [Building Tutorial Images](#build-images)
 - [Introduction to Flux](#introduction-to-flux)
 - [The Flux Operator with Agents](#the-flux-operator-with-agents)

Pre-requisites:

 - Docker client installed locally
 - Excitement to learn about Flux!

## Build Images

Build the tutorial images (these are also pushed to GitHub packages)

```bash
docker build -f ./docker/Dockerfile -t vanessa/hpsf-flux:2026-jupyter .
docker build -f ./docker/Dockerfile.ml -t vanessa/hpsf-flux:2026-ml .
docker build -f ./docker/Dockerfile.flux-operator -t vanessa/hpsf-flux:2026-flux-operator-pytorch .
```

## 1. Introduction to Flux 

The introduction to Flux section is a notebook. You can simply run the Image.

```bash
docker run --rm -it  -v /var/run/docker.sock:/var/run/docker.sock --name jupyterhub  -p 8888:8888 vanessa/hpsf-flux:2026-jupyter
```

## 2. The Flux Operator with Agents

The Flux Operator and MCP example is a Flux Framework MiniCluster. Either create a cloud (or have) a Kubernetes cluster, e.g:

```bash
eksctl create cluster --config-file ./eks-config.yaml 
aws eks update-kubeconfig --region us-east-2 --name hpsf-flux
```

or create one with kind:

```bash
kind create cluster --config ./flux-operator/kind-config.yaml
docker pull vanessa/flux-mcp:spack-ubuntu-24.04
kind load docker-image vanessa/hpsf-flux:2026-flux-operator-pytorch
```
Install the Flux Operator:

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/refs/heads/main/examples/dist/flux-operator.yaml
```

Create the minicluster:

```bash
kubectl apply -f ./flux-operator/minicluster.yaml
```

Wait until both ranks are running, then shell inside and connect to the lead broker.

```bash
kubectl get pods --watch
kubectl exec -it pytorch-0-xxxx -- bash
. /mnt/flux/flux-view.sh
flux proxy $fluxsocket bash
flux resource list
```
```console
fluxroot@pytorch-0:/code# flux resource list
     STATE NNODES   NCORES    NGPUS NODELIST
      free      2      192        0 pytorch-[0-1]
 allocated      0        0        0 
      down      0        0        0 
```

Now let's run Pytorch, without agents. There is a simple "hello world" and training example with cifar.

```bash
flux run -N 2 --exclusive python distributed_flux_hello_world.py 
flux run -N 2 --exclusive python distributed_flux.py 
```

We could also put `-n` for the number of tasks (processes) per node, but exclusive will ask for all of them.

Now let's ask the agent to optimize the run for us. Note that we are adding an optimize agent on the fly (`-r` == `--registry`)

```bash
fractale agent -r ./fractale/examples/registry/analysis-agents.yaml optimize Discover resources, and write a simple Python program that will do some kind of training using pytorch. You will need to use flux archive to create an archive, and flux exec across all nodes to extract the file. Once you have it working, parse the log and try to optimize the result for the resources you have. 
```

## 3. Kubeflow and Flux

The Kubeflow and Flux example can use the same cluster, but we add Kubeflow.

```bash
git clone -b flux-framework-plugin https://github.com/converged-computing/trainer
cd trainer

make generate
make manifests
docker build -t ghcr.io/kubeflow/trainer/trainer-controller-manager -f ./cmd/trainer-controller-manager/Dockerfile .
kind load docker-image ghcr.io/kubeflow/trainer/trainer-controller-manager
kubectl apply --server-side -k ./manifests/overlays/manager
sleep 20
kubectl apply -f examples/flux/flux-runtime.yaml
sleep 5
kubectl apply -f examples/flux/lammps-train-job.yaml
```
