## Using Flux Job Status and Control API

### Description: Submit job bundles, get event updates, and wait until all jobs complete

#### Setup

If you haven't already, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-status-control
```

#### Execution

1. Allocate three nodes from a resource manager:

`salloc -N3 -p pdebug`

2. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Run the bookkeeper executable along with the number of jobs to be submitted (if no size is specified, 6 jobs are submitted: 3 instances of **compute.py**, and 3 instances of **io-forwarding,py**):

`./bookkeeper.py 2`

```
bookkeeper: all jobs submitted
bookkeeper: waiting until all jobs complete
job 39040581632 triggered event 'submit'
job 39040581633 triggered event 'submit'
job 39040581632 triggered event 'depend'
job 39040581632 triggered event 'priority'
job 39040581632 triggered event 'alloc'
job 39040581633 triggered event 'depend'
job 39040581633 triggered event 'priority'
job 39040581633 triggered event 'alloc'
job 39040581632 triggered event 'start'
job 39040581633 triggered event 'start'
job 39040581632 triggered event 'finish'
job 39040581633 triggered event 'finish'
job 39040581633 triggered event 'release'
job 39040581633 triggered event 'free'
job 39040581633 triggered event 'clean'
job 39040581632 triggered event 'release'
job 39040581632 triggered event 'free'
job 39040581632 triggered event 'clean'
bookkeeper: all jobs completed
```

---

### Notes

- The following constructs a job request using the **JobspecV1** class with customizable parameters for how you want to utilize the resources allocated for your job:
```python
compute_jobreq = JobspecV1.from_command(
    command=["./compute.py", "10"], num_tasks=4, num_nodes=2, cores_per_task=2
)
compute_jobreq.cwd = os.getcwd()
compute_jobreq.environment = dict(os.environ)
```

- `with FluxExecutor() as executor:` creates a new `FluxExecutor` which can be used to submit jobs, wait for them to complete, and get event updates. Using the executor as a context manager (`with ... as ...:`) ensures it is shut down properly.

- `executor.submit(compute_jobreq)` returns a `concurrent.futures.Future` subclass which completes when the underlying job is done. The jobid of the underlying job can be fetched with the `.jobid([timeout])` method (which waits until the jobid is ready).

- Throughout the course of a job, various events will occur to it. `future.add_event_callback(event, event_callback)` adds a callback which will be invoked when the given event occurs.
