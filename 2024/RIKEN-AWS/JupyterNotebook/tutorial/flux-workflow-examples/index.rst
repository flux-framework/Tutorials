Flux Workflow Examples
----------------------

The examples contained here demonstrate and explain some simple use-cases with Flux,
and make use of Flux's command-line interface (CLI), Flux's C library, and the Python and Lua bindings to the C library.
The entire set of examples can be downloaded by cloning the `Github repo <https://github.com/flux-framework/flux-workflow-examples>`_.

The examples assume that you have installed:

#. A recent version of Flux

#. Python 3.6+

#. Lua 5.1+

:doc:`CLI: Job Submission <job-submit-cli/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch a flux instance and schedule/launch compute and io-forwarding
jobs on separate nodes using the CLI

:doc:`Python: Job Submission <job-submit-api/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Schedule/launch compute and io-forwarding jobs on separate nodes using
the Python bindings

:doc:`Python: Job Submit/Wait <job-submit-wait/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Submit jobs and wait for them to complete using the Flux Python bindings

:doc:`Python: Asynchronous Bulk Job Submission <async-bulk-job-submit/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Asynchronously submit jobspec files from a directory and wait for them
to complete in any order

:doc:`Python: Tracking Job Status and Events <job-status-control/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Submit job bundles and wait until all jobs complete

:doc:`Python: Job Cancellation <job-cancel/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Cancel a running job

:doc:`Lua: Use Events <synchronize-events/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use events to synchronize compute and io-forwarding jobs running on
separate nodes

:doc:`Python: Simple KVS Example <kvs-python-bindings/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use KVS Python interfaces to store user data into KVS

:doc:`CLI/Lua: Job Ensemble Submitted with a New Flux Instance <job-ensemble/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Submit job bundles, print live job events, and exit when all jobs are
complete

:doc:`CLI: Hierarchical Launching <hierarchical-launching/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch a large number of sleep 0 jobs

:doc:`C/Lua: Use a Flux Comms Module <comms-module/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a Flux Comms Module to communicate with job elements

:doc:`C/Python: A Data Conduit Strategy <data-conduit/README>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Attach to a job that receives OS time data from compute jobs

.. toctree::
   :hidden:

   job-submit-cli/README
   job-submit-api/README
   job-submit-wait/README
   async-bulk-job-submit/README
   job-status-control/README
   job-cancel/README
   synchronize-events/README
   kvs-python-bindings/README
   job-ensemble/README
   hierarchical-launching/README
   comms-module/README
   data-conduit/README
