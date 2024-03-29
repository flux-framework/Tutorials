## Job Submit API

To run the following examples, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-submit-api
```

### Part(a) - Using a direct job.submit RPC

#### Description: Schedule and launch compute and io-forwarding jobs on separate nodes

1. Allocate three nodes from a resource manager:

`salloc -N3 -p pdebug`

2. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Run the submitter executable:

`./submitter.py`

4. List currently running jobs:

`flux jobs`

```
JOBID    USER     NAME       ST NTASKS NNODES  RUNTIME RANKS
ƒ5W8gVwm moussa1  io-forward  R      1      1   19.15s 2
ƒ5Vd2kJs moussa1  compute.py  R      4      2   19.18s [0-1]
```

5. Information about jobs, such as the submitted job specification, an eventlog, and the resource description format **R** are stored in the KVS. The data can be queried via the `job-info` module via the `flux job info` command. For example, to fetch **R** for a job which has been allocated resources:

`flux job info ƒ5W8gVwm R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"0"}}]}}
```

`flux job info ƒ5Vd2kJs R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

### Part(b) - Using a direct job.submit RPC

#### Description: Schedule and launch both compute and io-forwarding jobs across all nodes

1. Allocate three nodes from a resource manager:

`salloc -N3 -p pdebug`

2. Launch another Flux instance on the current allocation:  

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Run the second submitter executable:

`./submitter2.py`

4. List currently running jobs:

`flux jobs`

```
JOBID    USER     NAME       ST NTASKS NNODES  RUNTIME RANKS
ƒctYadhh moussa1  io-forward  R      3      3   3.058s [0-2]
ƒct1StnT moussa1  compute.py  R      6      3   3.086s [0-2]
```

5. Fetch **R** for the jobs that have been allocated resources:

`flux job info ƒctYadhh R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"0-3"}}]}}
```

`flux job info ƒct1StnT R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"0-3"}}]}}
```

---

### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.


- The following constructs a job request using the **JobspecV1** class with customizable parameters for how you want to utilize the resources allocated for your job:
```python
compute_jobreq = JobspecV1.from_command(
    command=["./compute.py", "120"], num_tasks=4, num_nodes=2, cores_per_task=2
)
compute_jobreq.cwd = os.getcwd()
compute_jobreq.environment = dict(os.environ)
```

- `flux.job.submit(f, compute_jobreq)` submits the job to be run, and returns a job ID once it begins running.
