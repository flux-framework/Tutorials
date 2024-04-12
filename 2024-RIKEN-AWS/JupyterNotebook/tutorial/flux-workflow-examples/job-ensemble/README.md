### Job Ensemble Submitted with a New Flux Instance

#### Description: Launch a flux instance and submit one instance of an io-forwarding job and 50 compute jobs, each spanning the entire set of nodes.

#### Setup

If you haven't already, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-ensemble
```

#### Execution

1. `salloc -N3 -ppdebug`

2. `cat ensemble.sh`

```
#!/usr/bin/env sh

NJOBS=10
MAXTIME=$(expr ${NJOBS} + 2)
JOBIDS=""

JOBIDS=$(flux mini submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua ${MAXTIME})
for i in `seq 1 ${NJOBS}`; do
    JOBIDS="${JOBIDS} $(flux mini submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 1)"
done

flux jobs
flux queue drain

# print mock-up prevenance data
for i in ${JOBIDS}; do
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo "Jobid: ${i}"
    KVSJOBID=$(flux job id --from=dec --to=kvs ${i})
    flux kvs get ${KVSJOBID}.R | jq
done
```

3. `srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out ./ensemble.sh`

```
JOBID         USER      NAME       STATE    NTASKS NNODES  RUNTIME RANKS
1721426247680 fluxuser  compute.lu RUN           4      2   0.122s [1-2]
1718322462720 fluxuser  compute.lu RUN           4      2   0.293s [0,2]
1715201900544 fluxuser  compute.lu RUN           4      2   0.481s [0-1]
1712299442176 fluxuser  compute.lu RUN           4      2   0.626s [1-2]
1709296320512 fluxuser  compute.lu RUN           4      2   0.885s [0,2]
1706293198848 fluxuser  compute.lu RUN           4      2   1.064s [0-1]
1691378253824 fluxuser  io-forward RUN           1      1   1.951s 0
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
