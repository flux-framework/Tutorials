# Docker Images

These images were originally derived from the state machine operator work. These should be done on the arm builder. 
The entrypoint are customized to make each container entirely modular to run an example, and show file output to the user.
The original instance builders were equivalently hpc7g, which is what the tutorial used.
They do not require the Flux operator, aside from the last one with MPI, which won't be used for the tutorial here but is provided as an example.

## MLRunner

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 633731392008.dkr.ecr.us-east-1.amazonaws.com
docker pull 633731392008.dkr.ecr.us-east-1.amazonaws.com/mini-mummi:mlrunner-arm

docker build --network host -f ./mlrunner/Dockerfile -t ghcr.io/converged-computing/sc25-flux-eks:mlrunner-arm ./mlrunner
docker push ghcr.io/converged-computing/sc25-flux-eks:mlrunner-arm
```

## Createsims

Initial Dockerfile [is here](https://github.com/converged-computing/mummi-experiments/blob/main/experiments/aws-march-2025/cpu-node-selector/Dockerfile.arm).
It has a sample built into it from mlrunner. Let's retagged for this repository.

```bash
docker build --network host -f ./createsims/Dockerfile -t ghcr.io/converged-computing/sc25-flux-eks:createsims-arm ./createsims
docker push ghcr.io/converged-computing/sc25-flux-eks:createsims-arm
```

## Cganalysis

We need to get the output from `/workdir/out` in the build above and move into the cganalysis/data directory for this build.

```bash
docker build --network host -f ./cganalysis/Dockerfile -t ghcr.io/converged-computing/sc25-flux-eks:cganalysis-arm ./cganalysis
docker push ghcr.io/converged-computing/sc25-flux-eks:cganalysis-arm
```

## Cganalysis-mpi

Ditto for data. This build adds an MPI enabled gmx.

```bash
docker build --network host -f ./cganalysis-mpi/Dockerfile -t ghcr.io/converged-computing/sc25-flux-eks:cganalysis-mpi-arm ./cganalysis-mpi
docker push ghcr.io/converged-computing/sc25-flux-eks:cganalysis-mpi-arm
```
