### Example 2(a) - Using a direct job.submit RPC

#### Description: Schedule and launch compute and io-forwarding jobs on separate nodes

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Run the submitter executable:

`./submitter.py`

3. List currently running jobs:

`flux job list`

```
JOBID		STATE	USERID	PRI	NAME		T_SUBMIT
316703506432	R	58985	16	./io-forwarding	2019-12-16T21:54:19Z
316250521600	R	58985	16	./compute.py   	2019-12-16T21:54:19Z
```

4. Information about jobs, such as the submitted job specification, an eventlog, and the resource description format **R** are stored in the KVS. The data can be queried via the `job-info` module via the `flux job info` command. For example, to fetch **R** for a job which has been allocated resources:

`flux job info 316703506432 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-1","children":{"core":"0-3"}}]}}
```

`flux job info 316250521600 R`

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

`flux job list`

```
JOBID		STATE	USERID	PRI	NAME		T_SUBMIT
266187309056	R	58985	16	./io-forwarding	2019-12-16T22:01:59Z
265767878656	R	58985	16	./compute.py   	2019-12-16T22:01:59Z
```

4. Fetch **R** for the jobs that have been allocated resources:

`flux job info 266187309056 R`

```
{"version":1,"execution":{"R_lite":[{"rank":"0-2","children":{"core":"4"}}]}}
```

`flux job info 265767878656 R`

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
