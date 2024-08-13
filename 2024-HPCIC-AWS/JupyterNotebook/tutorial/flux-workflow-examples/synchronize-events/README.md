# Using Events with Separate Nodes

## Description: Using events to synchronize compute and io-forwarding jobs running on separate nodes

If you haven't already, download the files and change your working directory:

```console
$ cd flux-workflow-examples/synchronize-events
```

Ask for a Slurm allocation, if relevant:

```bash
salloc -N3 -ppdebug
srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out
flux submit --nodes=1 --ntasks=4 --cores-per-task=2 ./compute.lua 120
```

And:

```bash
flux submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120
```

5. List running jobs:

```bash
flux jobs
```
```
JOBID    USER     NAME       ST NTASKS NNODES  RUNTIME RANKS
ƒA4TgT7d fluxuser  io-forward  R      1      1   4.376s 2
ƒ6vEcj7M fluxuser  compute.lu  R      4      2   11.51s [0-1]
```

6. Attach to running or completed job output:

```bash
flux job attach ƒ6vEcj7M
```
```console
Block until we hear go message from the an io forwarder
Block until we hear go message from the an io forwarder
Recv an event: please proceed
Recv an event: please proceed
Will compute for 120 seconds
Will compute for 120 seconds
Block until we hear go message from the an io forwarder
Block until we hear go message from the an io forwarder
Recv an event: please proceed
Recv an event: please proceed
Will compute for 120 seconds
Will compute for 120 seconds
```
