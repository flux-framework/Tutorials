### Example 2(a) - Using a direct job.submit RPC

#### Description: Schedule and launch compute and io-forwarding jobs on separate nodes

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Run the submitter executable:

`./submitter.py`

3. List currently running jobs:

`flux jobs`

```
       JOBID USER     NAME       STATE    NTASKS RUNTIME
249024217088 ubuntu   io-forward RUN           1 3.583s
248688672768 ubuntu   compute.py RUN           4 3.667s
```

4. Information about jobs, such as the submitted job specification, an eventlog, and the resource description format **R** are stored in the KVS. The data can be queried via the `job-info` module via the `flux job info` command. For example, to fetch **R** for a job which has been allocated resources:

`flux job info 248688672768 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

`flux job info 249024217088 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"2","children":{"core":"0"}}]}}
```

### Example 2(b) - Using a direct job.submit RPC

#### Description: Schedule and launch both compute and io-forwarding jobs across all nodes

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Run the second submitter executable:

`./submitter2.py`

3. List currently running jobs:

`flux jobs`

```
        JOBID USER     NAME       STATE    NTASKS RUNTIME
1729898741760 ubuntu   io-forward RUN           3 6.371s
1729563197440 ubuntu   compute.py RUN           6 6.473s
```

4. Fetch **R** for the jobs that have been allocated resources:

`flux job info 1729898741760 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"4"}}]}}
```

`flux job info 1729563197440 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"0-3"}}]}}
```

---

##### Notes

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
