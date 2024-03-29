## Python Job Submit/Wait

To run the following examples, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-submit-wait
```

### Part(a) - Python Job Submit/Wait

#### Description: Submit jobs asynchronously and wait for them to complete in any order

1. Allocate three nodes from a resource manager:

`salloc -N3 -ppdebug`

2. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Submit the **submitter_wait_any.py** script, along with the number of jobs you want to run (if no argument is passed, 10 jobs are submitted):

`./submitter_wait_any.py 10`

```
submit: 46912591450240 compute_jobspec
submit: 46912591450912 compute_jobspec
submit: 46912591451080 compute_jobspec
submit: 46912591363152 compute_jobspec
submit: 46912591362984 compute_jobspec
submit: 46912591451360 bad_jobspec
submit: 46912591451528 bad_jobspec
submit: 46912591451696 bad_jobspec
submit: 46912591451864 bad_jobspec
submit: 46912591452032 bad_jobspec
wait: 46912591451528 Error: job returned exit code 1
wait: 46912591451864 Error: job returned exit code 1
wait: 46912591451360 Error: job returned exit code 1
wait: 46912591451696 Error: job returned exit code 1
wait: 46912591452032 Error: job returned exit code 1
wait: 46912591450240 Success
wait: 46912591363152 Success
wait: 46912591450912 Success
wait: 46912591451080 Success
wait: 46912591362984 Success
```

---

### Part(b) - Python Job Submit/Wait (Sliding Window)

#### Description: Asynchronously submit jobs and keep at most a number of those jobs active

1. Allocate three nodes from a resource manager:

`salloc -N3 -ppdebug`

2. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Submit the **submitter_sliding_window.py** script, along with the number of jobs you want to run and the size of the window (if no argument is passed, 10 jobs are submitted and the window size is 2 jobs):

`./submitter_sliding_window.py 10 3`

```
submit: 5624175788032
submit: 5624611995648
submit: 5625014648832
wait: 5624175788032 Success
submit: 5804329533440
wait: 5624611995648 Success
submit: 5804648300544
wait: 5625014648832 Success
submit: 5805084508160
wait: 5804329533440 Success
submit: 5986144223232
wait: 5804648300544 Success
submit: 5986462990336
wait: 5805084508160 Success
submit: 5986882420736
wait: 5986144223232 Success
submit: 6164435697664
wait: 5986462990336 Success
wait: 5986882420736 Success
wait: 6164435697664 Success
```

---

### Part(c) - Python Job Submit/Wait (Specific Job ID)

#### Description: Asynchronously submit jobs, block/wait for specific jobs to complete

1. Allocate three nodes from a resource manager:

`salloc -N3 -ppdebug`

2. Launch a Flux instance on the current allocation by running `flux start` once per node, redirecting log messages to the file `out` in the current directory:

`srun --pty --mpi=none -N3 flux start -o,-S,log-filename=out`

3. Submit the **submitter_wait_in_order.py** script, along with the number of jobs you want to run (if no argument is passed, 10 jobs are submitted):

`./submitter_wait_in_order.py 10`

```
submit: 46912593818008 compute_jobspec
submit: 46912593818176 compute_jobspec
submit: 46912593818344 compute_jobspec
submit: 46912593818512 compute_jobspec
submit: 46912593738048 compute_jobspec
submit: 46912519873816 bad_jobspec
submit: 46912593818792 bad_jobspec
submit: 46912593818960 bad_jobspec
submit: 46912593819128 bad_jobspec
submit: 46912593819296 bad_jobspec
wait: 46912593818008 Success
wait: 46912593818176 Success
wait: 46912593818344 Success
wait: 46912593818512 Success
wait: 46912593738048 Success
wait: 46912519873816 Error: job returned exit code 1
wait: 46912593818792 Error: job returned exit code 1
wait: 46912593818960 Error: job returned exit code 1
wait: 46912593819128 Error: job returned exit code 1
wait: 46912593819296 Error: job returned exit code 1
```

---

### Notes

- The following constructs a job request using the **JobspecV1** class with customizable parameters for how you want to utilize the resources allocated for your job:

```python
# create jobspec for compute.py
compute_jobspec = JobspecV1.from_command(command=["./compute.py", "15"], num_tasks=4, num_nodes=2, cores_per_task=2)
compute_jobspec.cwd = os.getcwd()
compute_jobspec.environment = dict(os.environ)
```

- Using the executor as a context manager (`with FluxExecutor() as executor`) ensures it shuts down properly.

- `executor.submit(jobspec)` returns a future which completes when the job is done.

- `future.exception()` blocks until the future is complete and returns (not raises) an exception if the job was canceled or was otherwise prevented from execution. Otherwise the method returns ``None``.

- `future.result()` blocks until the future is complete and returns the return code of the job. If the job succeeded, the return code will be 0.
