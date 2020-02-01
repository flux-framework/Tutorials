### Example 10(a) - Python Job Submit/Wait

#### Description: Submit jobs asynchronously and wait for them to complete in any order

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Submit the **submitter_wait_any.py** script, along with the number of jobs you want to run (if no argument is passed, 10 jobs are submitted):

`./submitter_wait_any.py 10`

```
submit: 11123713638400 compute_jobspec
submit: 11124099514368 compute_jobspec
submit: 11124518944768 compute_jobspec
submit: 11124921597952 compute_jobspec
submit: 11125257142272 compute_jobspec
submit: 11125626241024 bad_jobspec
submit: 11126028894208 bad_jobspec
submit: 11126347661312 bad_jobspec
submit: 11126649651200 bad_jobspec
submit: 11126968418304 bad_jobspec
wait: 11123713638400 Success
wait: 11124099514368 Success
wait: 11124518944768 Success
wait: 11124921597952 Success
wait: 11125257142272 Success
wait: 11125626241024 Error: task(s) exited with exit code 1
wait: 11126028894208 Error: task(s) exited with exit code 1
wait: 11126347661312 Error: task(s) exited with exit code 1
wait: 11126649651200 Error: task(s) exited with exit code 1
wait: 11126968418304 Error: task(s) exited with exit code 1
```

---

### Example 10(b) - Python Job Submit/Wait (Sliding Window)

#### Description: Asynchronously submit jobs and keep at most a number of those jobs active

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Submit the **submitter_sliding_window.py** script, along with the number of jobs you want to run and the size of the window (if no argument is passed, 10 jobs are submitted and the window size is 2 jobs):

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

### Example 10(c) - Python Job Submit/Wait (Specific Job ID)

#### Description: Asynchronously submit jobs, block/wait for specific jobs to complete

1. Launch a Flux instance emulating a 3 node cluster, redirecting log messages to the file `out` in the current directory:

`flux start --size=3 -o,-S,log-filename=out`

2. Submit the **submitter_wait_in_order.py** script, along with the number of jobs you want to run (if no argument is passed, 10 jobs are submitted):

`./submitter_wait_in_order.py 10`

```
submit: 141868138496 compute_jobspec
submit: 142203682816 compute_jobspec
submit: 142639890432 compute_jobspec
submit: 143025766400 compute_jobspec
submit: 143344533504 compute_jobspec
submit: 143730409472 bad_jobspec
submit: 144233725952 bad_jobspec
submit: 144518938624 bad_jobspec
submit: 144871260160 bad_jobspec
submit: 145156472832 bad_jobspec
wait: 143730409472 Error: task(s) exited with exit code 1
wait: 144518938624 Error: task(s) exited with exit code 1
wait: 145156472832 Error: task(s) exited with exit code 1
wait: 144871260160 Error: task(s) exited with exit code 1
wait: 144233725952 Error: task(s) exited with exit code 1
wait: 141868138496 Success
wait: 143025766400 Success
wait: 142639890432 Success
wait: 143344533504 Success
wait: 142203682816 Success
```

---

##### Notes

- `h = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.

- The following constructs a job request using the **JobspecV1** class with customizable parameters for how you want to utilize the resources allocated for your job:

```python
# create jobspec for compute.py
compute_jobspec = JobspecV1.from_command(command=["./compute.py", "15"], num_tasks=4, num_nodes=2, cores_per_task=2)
compute_jobspec.cwd = os.getcwd()
compute_jobspec.environment = dict(os.environ)
```

- `flux.job.submit(h, compute_jobspec, flags=flags)` submits the job to be run, and returns a job ID once it begins running.

- `result = job.wait(h, jobid)` waits for a job to transition to the **INACTIVE** state, then returns a summary of the job result, either a **Success** or an **Error** string.
