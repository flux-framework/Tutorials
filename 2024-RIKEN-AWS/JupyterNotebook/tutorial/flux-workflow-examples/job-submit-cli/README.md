## Job Submit CLI

To run the following examples, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-submit-cli
```

### Part(a) - Partitioning Schedule

#### Description: Launch a flux instance and schedule/launch compute and io-forwarding jobs on separate nodes

1. `salloc -N3 -ppdebug`

2. `srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. `flux mini submit --nodes=2 --ntasks=4 --cores-per-task=2 ./compute.lua 120`

4. `flux mini submit --nodes=1 --ntasks=1 --cores-per-task=2 ./io-forwarding.lua 120`

5. List running jobs:

`flux jobs`

```  
JOBID     USER     NAME       ST NTASKS NNODES  RUNTIME RANKS
ƒ3ETxsR9H moussa1  io-forward  R      1      1   2.858s 2
ƒ38rBqEWT moussa1  compute.lu  R      4      2    15.6s [0-1]
```

6. Get information about job:

`flux job info ƒ3ETxsR9H R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"0-1"}}]}}
```

`flux job info ƒ38rBqEWT R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

### Part(b) - Overlapping Schedule

#### Description: Launch a flux instance and schedule/launch both compute and io-forwarding jobs across all nodes

1. `salloc -N3 -ppdebug`

2. `srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. `flux mini submit --nodes=3 --ntasks=6 --cores-per-task=2 ./compute.lua 120`

4. `flux mini submit --nodes=3 --ntasks=3 --cores-per-task=1 ./io-forwarding.lua 120`

5. List jobs in KVS:

`flux jobs`

```
JOBID     USER     NAME       ST NTASKS NNODES  RUNTIME RANKS
ƒ3ghmgCpw moussa1  io-forward  R      3      3   16.91s [0-2]
ƒ3dSybfQ3 moussa1  compute.lu  R      6      3    24.3s [0-2]

```

6. Get information about job:

`flux job info ƒ3ghmgCpw R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"4"}}]}}
```

`flux job info ƒ3dSybfQ3 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"0-3"}}]}}
```
