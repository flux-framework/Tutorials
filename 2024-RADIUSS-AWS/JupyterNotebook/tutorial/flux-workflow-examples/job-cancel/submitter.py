#!/usr/bin/env python3

import time
import argparse

import flux
from flux.job import JobspecV1

f = flux.Flux()

parser = argparse.ArgumentParser(
    description="""
    Description: Submit two 'sleep 60' jobs that take up
    all resources on a node.
    """
)
parser.add_argument(dest="cores", help="number of cores on the node")
args = parser.parse_args()

# submit a sleep job that takes up all resources
sleep_jobspec = JobspecV1.from_command(
    ["sleep", "60"], num_tasks=1, cores_per_task=int(args.cores)
)
first_jobid = flux.job.submit(f, sleep_jobspec, waitable=True)
print("Submitted 1st job: %d" % (int(first_jobid)))
time.sleep(1)

# submit a second sleep job - will be scheduled, but not run
sleep_jobspec = JobspecV1.from_command(
    ["sleep", "60"], num_tasks=1, cores_per_task=int(args.cores)
)
second_jobid = flux.job.submit(f, sleep_jobspec, waitable=True)
print("Submitted 2nd job: %d\n" % (int(second_jobid)))
time.sleep(1)

# get list of JobInfo objects - fetch their ID's and current status
jobs = flux.job.JobList(f, max_entries=2).jobs()
print("First submitted job status (%d) - %s" % (int(jobs[1].id.dec), jobs[1].status))
print("Second submitted job status (%d) - %s\n" % (int(jobs[0].id.dec), jobs[0].status))

# cancel the first job
flux.job.cancel(f, first_jobid)
future = flux.job.wait_async(f, first_jobid).wait_for(5.0)
return_id, success, errmsg = future.get_status()
print("Canceled first job: %d\n" % (int(return_id)))
time.sleep(1)

# the second job should now run since the first was canceled
jobs = flux.job.JobList(f, max_entries=2).jobs()
print("First submitted job status (%d) - %s" % (int(jobs[1].id.dec), jobs[1].status))
print("Second submitted job status (%d) - %s" % (int(jobs[0].id.dec), jobs[0].status))
