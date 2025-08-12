# Job Submit CLI

To run the following examples, download the files and change your working directory:

```console
$ cd flux-workflow-examples/job-submit-cli
```

## Example

### Launch a flux instance and submit compute and io-forwarding jobs

If you need an allocation:

```bash
salloc -N3 -ppdebug
srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out
```

To submit

```bash
# if you have more than one node...
flux submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 120

# and if not!
flux submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120
```

Attach to watch output:

```bash
# Control +C then Control+Z to detach
flux job attach $(flux job last)
```

List running jobs:

```bash
flux jobs
```
```console  
JOBID     USER     NAME       ST NTASKS NNODES  RUNTIME
ƒ3ETxsR9H fluxuser  io-forward  R      1      1   2.858s
ƒ38rBqEWT fluxuser  compute.lu  R      4      2    15.6s
```

Get information about job:

```bash
flux job info $(flux job last) R
flux job info $(flux job last) jobspec
flux job info $(flux job last) eventlog
flux job info $(flux job last) guest.output

# Example with flux job id
flux job info ƒ3ETxsR9H R
```
```console
{"version": 1, "execution": {"R_lite": [{"rank": "0", "children": {"core": "5-7"}}], "nodelist": ["674f16a501e5"], "starttime": 1723225494, "expiration": 4876808372}}
```
