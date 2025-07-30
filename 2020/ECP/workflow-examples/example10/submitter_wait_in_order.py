#!/usr/bin/env python3

import flux
import sys
import os

from flux import job
from flux.job import JobspecV1

if len(sys.argv) != 2:
    njobs = 10
else:
    njobs = int(sys.argv[1])

# open connection to broker
h = flux.Flux()

# create jobspec for compute.py
compute_jobspec = JobspecV1.from_command(
    command=["./compute.py", "10"], num_tasks=4, num_nodes=2, cores_per_task=2
)
compute_jobspec.cwd = os.getcwd()
compute_jobspec.environment = dict(os.environ)

# create bad jobspec that will fail
bad_jobspec = JobspecV1.from_command(["/bin/false"])

jobs = []
flags = flux.constants.FLUX_JOB_WAITABLE

# submit jobs
for i in range(njobs):
    if i < njobs / 2:
        jobid = flux.job.submit(h, compute_jobspec, flags=flags)
        print("submit: {} compute.py".format(jobid))
    else:
        jobid = job.submit(h, bad_jobspec, flags=flags)
        print("submit: {} bad_jobspec".format(jobid))
    jobs.append(jobid)

# wait for each job in turn by jobid
for jobid in jobs:
    result = job.wait(h, jobid)
    if result.success:
        print("wait: {} Success".format(result.jobid))
    else:
        print("wait: {} Error: {}".format(result.jobid, result.errstr))

# vim: tabstop=4 shiftwidth=4 expandtab
