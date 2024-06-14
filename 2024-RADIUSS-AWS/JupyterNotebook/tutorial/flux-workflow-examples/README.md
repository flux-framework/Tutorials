**WARNING**

This repository has been archived. It is no longer maintained and it is
likely the examples do not work or are no longer good or suggested
examples.

Please look elswhere for examples.

**Flux Workflow Examples**

The examples contained here demonstrate and explain some simple use-cases with Flux,
and make use of Flux's command-line interface (CLI), Flux's C library,
and the Python and Lua bindings to the C library.

**Requirements**

The examples assume that you have installed:

1. A recent version of Flux

2. Python 3.6+

3. Lua 5.1+

**_1. [CLI: Job Submission](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-submit-cli)_**

Launch a flux instance and schedule/launch compute and io-forwarding jobs on
separate nodes using the CLI

**_2. [Python: Job Submission](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-submit-api)_**

Schedule/launch compute and io-forwarding jobs on separate nodes using the Python bindings

**_3. [Python: Job Submit/Wait](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-submit-wait)_**

Submit jobs and wait for them to complete using the Flux Python bindings

**_4. [Python: Asynchronous Bulk Job Submission](https://github.com/flux-framework/flux-workflow-examples/tree/master/async-bulk-job-submit)_**

Asynchronously submit jobspec files from a directory and wait for them to complete in any order

**_5. [Python: Tracking Job Status and Events](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-status-control)_**

Submit job bundles, get event updates, and wait until all jobs complete

**_6. [Python: Job Cancellation](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-cancel)_**

Cancel a running job

**_7. [Lua: Use Events](https://github.com/flux-framework/flux-workflow-examples/tree/master/synchronize-events)_**

Use events to synchronize compute and io-forwarding jobs running on separate
nodes

**_8. [Python: Simple KVS Example](https://github.com/flux-framework/flux-workflow-examples/tree/master/kvs-python-bindings)_**

Use KVS Python interfaces to store user data into KVS

**_9. [CLI/Lua: Job Ensemble Submitted with a New Flux Instance](https://github.com/flux-framework/flux-workflow-examples/tree/master/job-ensemble)_**

Submit job bundles, print live job events, and exit when all jobs are complete

**_10. [CLI: Hierarchical Launching](https://github.com/flux-framework/flux-workflow-examples/tree/master/hierarchical-launching)_**

Launch a large number of sleep 0 jobs

**_11. [C/Lua: Use a Flux Comms Module](https://github.com/flux-framework/flux-workflow-examples/tree/master/comms-module)_**

Use a Flux Comms Module to communicate with job elements

**_12. [C/Python: A Data Conduit Strategy](https://github.com/flux-framework/flux-workflow-examples/tree/master/data-conduit)_**

Attach to a job that receives OS time data from compute jobs
