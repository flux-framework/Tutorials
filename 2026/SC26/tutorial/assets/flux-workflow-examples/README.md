# Flux Workflow Examples

This contents used to be hosted at [flux-framework/flux-workflow-examples](https://github.com/flux-framework/flux-workflow-examples) and has been moved here for annual updates paired with the Flux Tutorials.

The examples contained here demonstrate and explain some simple use-cases with Flux,
and make use of Flux's command-line interface (CLI), Flux's C library,
and the Python and Lua bindings to the C library.

## Requirements

The examples assume that you have installed:

1. A recent version of Flux
2. Python 3.6+
3. Lua 5.1+

You can also use an interactive container locally, binding this directory to the container:

```bash
docker run -it -v $(pwd):/home/fluxuser/flux-workflow-examples fluxrm/flux-sched:jammy
cd /home/fluxuser/flux-workflow-examples/
```

**_1. [CLI: Job Submission](job-submit-cli)_**

Launch a flux instance and schedule/launch compute and io-forwarding jobs on
separate nodes using the CLI

**_2. [Python: Job Submission](job-submit-api)_**

Schedule/launch compute and io-forwarding jobs on separate nodes using the Python bindings

**_3. [Python: Job Submit/Wait](job-submit-wait)_**

Submit jobs and wait for them to complete using the Flux Python bindings

**_4. [Python: Asynchronous Bulk Job Submission](async-bulk-job-submit)_**

Asynchronously submit jobspec files from a directory and wait for them to complete in any order

**_5. [Python: Tracking Job Status and Events](job-status-control)_**

Submit job bundles, get event updates, and wait until all jobs complete

**_6. [Python: Job Cancellation](job-cancel)_**

Cancel a running job

**_7. [Lua: Use Events](synchronize-events)_**

Use events to synchronize compute and io-forwarding jobs running on separate
nodes

**_8. [Python: Simple KVS Example](kvs-python-bindings)_**

Use KVS Python interfaces to store user data into KVS

**_9. [CLI/Lua: Job Ensemble Submitted with a New Flux Instance](job-ensemble)_**

Submit job bundles, print live job events, and exit when all jobs are complete

**_10. [CLI: Hierarchical Launching](hierarchical-launching)_**

Launch a large number of sleep 0 jobs

**_11. [C/Lua: Use a Flux Comms Module](comms-module)_**

Use a Flux Comms Module to communicate with job elements

**_12. [C/Python: A Data Conduit Strategy](data-conduit)_**

Attach to a job that receives OS time data from compute jobs
