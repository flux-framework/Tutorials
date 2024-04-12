## Job Cancellation

### Description: Cancel a running job

#### Setup

If you haven't already, download the files and change your working directory:

```
$ git clone https://github.com/flux-framework/flux-workflow-examples.git
$ cd flux-workflow-examples/job-cancel
```

#### Execution

1. Launch the submitter script:

`./submitter.py $(flux resource list -no {ncores} --state=up)`

_note: for older versions of Flux, you might need to instead run: `./submitter.py $(flux hwloc info | awk '{print $3}')`_

```
Submitted 1st job: 2241905819648
Submitted 2nd job: 2258951471104

First submitted job status (2241905819648) - RUNNING
Second submitted job status (2258951471104) - PENDING

Canceled first job: 2241905819648

First submitted job status (2241905819648) - CANCELED
Second submitted job status (2258951471104) - RUNNING
```

### Notes

- `f = flux.Flux()` creates a new Flux handle which can be used to connect to and interact with a Flux instance.

- `flux.job.submit(f, sleep_jobspec, waitable=True)` submits a jobspec, returning a job ID that can be used to interact with the submitted job.

- `flux.job.cancel(f, jobid)` cancels the job.

- `flux.job.wait_async(f, jobid)` will wait for the job to complete (or in this case, be canceled). It returns a Flux future, which can be used to process the result later. Only jobs submitted with `waitable=True` can be waited for.
