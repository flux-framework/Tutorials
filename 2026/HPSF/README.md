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
docker build -f ./docker/Dockerfile.flux-operator -t vanessa/hpsf-flux:2026-flux-operator-pytorch-9 .
```

Or pull:

```bash
docker pull vanessa/hpsf-flux:2026-jupyter
```

## 1. Introduction to Flux 

The introduction to Flux section is a notebook. You can simply run the Image.

```bash
docker run --rm -it  -v /var/run/docker.sock:/var/run/docker.sock --name jupyterhub  -p 8888:8888 vanessa/hpsf-flux:2026-jupyter
```

## 2. The Flux Operator with Agents

The Flux Operator and MCP example is a Flux Framework MiniCluster. Either create a cloud (or have) a Kubernetes cluster. We are going to create two clusters:

Nodes that support EFA and GPU:

- P5 Instances: High-performance H100 GPU instances that support up to 3,200 Gbps network bandwidth and EFA.
- P4d/P4de Instances: A100 GPU instances commonly used for distributed training with EFA.
- G6e Instances: Equipped with NVIDIA L40S GPUs, suitable for training and inference.
- Trn1/Trn2 Instances

```bash
eksctl create cluster --config-file ./eks-config.yaml 
# or
eksctl create cluster --config-file ./eks-config-hpc8a.yaml 
eksctl create cluster --config-file ./eks-config-gpu.yaml
aws eks update-kubeconfig --region us-east-2 --name hpsf-flux
```
- vCPUs	96
- Memory (GiB)	384
- Memory per vCPU (GiB)	4
- Physical Processor AMD EPYC 7R13 Processor

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

We could also put `-n` for the number of tasks (processes) per node, but exclusive will ask for all of them. Here is using an agent. You will need to export `GEMINI_TOKEN`.

```bash
fractale agent -r ./fractale/examples/registry/parser-agents.yaml result_parse tell me a joke and parse the result log for the punchline.
```

Now let's ask the agent to optimize the run for us. Note that we are adding an optimize agent on the fly (`-r` == `--registry`)

```bash
fractale agent -r ./fractale/examples/registry/analysis-agents.yaml optimize Discover resources, and write a simple Python program that will do some kind of training using pytorch. You will need to use flux archive to create an archive, and flux exec across all nodes to extract the file. Once you have it working, parse the log and try to optimize the result for the resources you have. 
```

## 3. Kubeflow and Flux

The Kubeflow and Flux example can use the same cluster, but we add Kubeflow.
First, install the Kubeflow Trainer.

```bash
kubectl apply --server-side -k "https://github.com/kubeflow/trainer.git/manifests/overlays/manager?ref=master"
```

This LAMMPS example assumes two small nodes. You can retrieve and alter the LAMMPS manifest to increase the problem size if you have more than that. Apply the `ClusterTrainingRuntime` and the `TrainJob`:

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/kubeflow/trainer/refs/heads/master/examples/flux/flux-runtime.yaml
kubectl apply -f https://raw.githubusercontent.com/kubeflow/trainer/refs/heads/master/examples/flux/lammps-train-job.yaml
```

If you get error messages about the webhook, you need to wait a little longer.

### 1. Monitor the Job

Watch for the pods to be created, and wait for them to be `Running`.

```bash
kubectl get pods -w
```

### 2. Check Logs

You'll see the InitContainer, and then PodInitializing is usually a container pulling.
To see the Flux broker initialization and the output of the LAMMPS job, check the logs of the lead broker (pod index `0-0`):

```bash
kubectl logs lammps-flux-node-0-0-mvjsf -c node -f
```

You can look at the second pod to see the follower broker bootstrap with the lead broker, and then cleanup when LAMMPS is done running.

```bash
kubectl logs lammps-flux-node-0-1-glj22 -c node -f
```
## 4. GPU and Flux

Now let's switch to the other cluster.

```bash
aws eks update-kubeconfig --region us-east-2 --name gpu-cluster
```

Install the Flux Operator

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/refs/heads/main/examples/dist/flux-operator.yaml
```

Create the minicluster:

```bash
kubectl apply -f ./flux-operator/minicluster-gpu.yaml
flux proxy local:///mnt/flux/config/run/flux/local bash
flux run --env CUDA_VISIBLE_DEVICES=0 -o cpu-affinity=per-task -N2 -n 2 -g 1 lmp -k on g 1 -sf kk -pk kokkos cuda/aware off newton on neigh half -in in.reaxff.hns -v x 8 -v y 8 -v z 8 -in in.reaxff.hns -nocite  
```

Install the kubeflow trainer and flux runtime

```bash
kubectl apply -f flux-runtime.yaml 
clustertrainingruntime.trainer.kubeflow.org/flux-runtime created
kubectl apply -f flux-operator/lammps-train-job-gpu.yaml 
trainjob.trainer.kubeflow.org/lammps-flux created
```

When you are done:

```bash
eksctl delete cluster --config-file ./eks-config.yaml  --wait
kubectl delete all --all --all-namespaces 
```
