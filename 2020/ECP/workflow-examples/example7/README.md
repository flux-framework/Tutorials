### Example 7 - Using Flux Job Status and Control API

#### Description: Submit job bundles and wait until all jobs complete

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Run the bookkeeper executable:

`./bookkeeper.py 5`

```
141732243046
141775863808
141816129126
282058555392
285564993536
bookkeeper: all jobs submitted
bookkeeper: waiting until all jobs complete
job 1417322430464 changed its state to DEPEND
job 1417322430464 changed its state to SCHED
job 1417758638080 changed its state to DEPEND
job 1417758638080 changed its state to SCHED
job 1418161291264 changed its state to DEPEND
job 1418161291264 changed its state to SCHED
.
.
.
job 282058555392 changed its state to CLEANUP
job 285564993536 changed its state to CLEANUP
.
.
.
job 282058555392 changed its state to INACTIVE
job 285564993536 changed its state to INACTIVE
.
.
.
bookkeeper: all jobs completed
```

---

##### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.


- The following constructs a job request using the **JobspecV1** class with customizable parameters for how you want to utilize the resources allocated for your job:
```python
compute_jobreq = JobspecV1.from_command(
    command=["./compute.py", "10"], num_tasks=4, num_nodes=2, cores_per_task=2
)
compute_jobreq.cwd = os.getcwd()
compute_jobreq.environment = dict(os.environ)
```

- `flux.job.submit(f, compute_jobreq)` submits the job to be run, and returns a job ID once it begins running.

- Throughout the course of a job, its state will go through a number of changes. The following subscribes to the event messages matching the transition of those states in the jobs submitted.
```python
f.event_subscribe("job-state")
f.msg_watcher_create(job_state_cb, 0, "job-state").start()
submit_bundles(f, args.integer)
print("bookkeeper: waiting until all jobs complete)
f.reactor_run(f.get_reactor(), 0)
print("bookkeeper: all jobs completed")
```
