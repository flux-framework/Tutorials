#!/usr/bin/env python3

import flux
import sys
import os

from flux import job
from flux.job import JobspecV1

njobs = 10
window_size = 2
if len(sys.argv) >= 2:
    njobs = int(sys.argv[1])
if len(sys.argv) == 3:
    window_size = int(sys.argv[2])

# open connection to broker
h = flux.Flux()

# create jobspec for compute.py
compute_jobspec = JobspecV1.from_command(
    command=["./compute.py", "5"], num_tasks=4, num_nodes=2, cores_per_task=2
)
compute_jobspec.cwd = os.getcwd()
compute_jobspec.environment = dict(os.environ)

flags = flux.constants.FLUX_JOB_WAITABLE
done = 0
running = 0

# submit jobs, keep [window_size] jobs running
while done < njobs:
    if running < window_size and done + running < njobs:
        jobid = flux.job.submit(h, compute_jobspec, flags=flags)
        print("submit: {}".format(jobid))
        running += 1

    if running == window_size or done + running == njobs:
        jobid, success, errstr = job.wait(h)
        if success:
            print("wait: {} Success".format(jobid))
        else:
            print("wait: {} Error: {}".format(jobid, errstr))
        done += 1
        running -= 1

# vim: tabstop=4 shiftwidth=4 expandtab
