# Job Ensemble Submitted with a New Flux Instance

## Description: Launch a flux instance and submit one instance of an io-forwarding job and 50 compute jobs, each spanning the entire set of nodes.

### Setup

If you haven't already, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-ensemble
```

### Execution

If you need a Slurm allocation:

```bash
salloc -N3 -ppdebug

# Take a look at the script first
cat ensemble.sh
```
Here is how to run under Slurm:

```bash
srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out ./ensemble.sh
```

Or without:

```bash
flux start -o,-S,log-filename=out ./ensemble.sh
```

```
JOBID         USER      NAME       STATE    NTASKS NNODES  RUNTIME 
1721426247680 fluxuser  compute.lu RUN           4      2   0.122s 
1718322462720 fluxuser  compute.lu RUN           4      2   0.293s 
1715201900544 fluxuser  compute.lu RUN           4      2   0.481s 
1712299442176 fluxuser  compute.lu RUN           4      2   0.626s 
1709296320512 fluxuser  compute.lu RUN           4      2   0.885s 
1706293198848 fluxuser  compute.lu RUN           4      2   1.064s 
1691378253824 fluxuser  io-forward RUN           1      1   1.951s
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Jobid: 1691378253824
{
  "version": 1,
  "execution": {
    "R_lite": [
      {
        "rank": "0",
        "children": {
          "core": "0-1"
        }
      }
    ]
  }
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Jobid: 1694414929920
{
  "version": 1,
  "execution": {
    "R_lite": [
      {
        "rank": "1-2",
        "children": {
          "core": "0-3"
        }
      }
    ]
  }
}
.
.
.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Jobid: 1721426247680
{
  "version": 1,
  "execution": {
    "R_lite": [
      {
        "rank": "1-2",
        "children": {
          "core": "8-11"
        }
      }
    ]
  }
}

```
