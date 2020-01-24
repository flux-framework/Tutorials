#!/usr/bin/env python

import json
import os
import flux
import argparse

compute_jobreq = JobspecV1.from_command(
    command=["./compute.py", "120"], num_tasks=6, num_nodes=3, cores_per_task=2
)
compute_jobreq.cwd = os.getcwd()
compute_jobreq.environment = dict(os.environ)

io_jobreq = JobspecV1.from_command(
    command=["./io-forwarding.py", "120"], num_tasks=3, num_nodes=3, cores_per_task=1
)
io_jobreq.cwd = os.getcwd()
io_jobreq.environment = dict(os.environ)

njobs = 0


def job_state_cb(f, typemask, message, arg):
    global njobs
    N = args.integer
    for jobid, state in message.payload["transitions"]:
        print("job " + str(jobid) + " changed its state to " + str(state))
        if state == "INACTIVE":
            njobs += 1
        if njobs == N * 2:
            f.reactor_stop(f.get_reactor())


# submit bundles of jobs using flux.job.submit ()
def submit_bundles(f, N):
    f = flux.Flux()
    for i in range(0, N):
        print(flux.job.submit(f, compute_jobreq))
        print(flux.job.submit(f, io_jobreq))

    print("bookkeeper: all jobs submitted")


# main
def main():
    parser = argparse.ArgumentParser(
        description="submit and wait for the completion of "
        "N bundles, each consisting of compute "
        "and io-forwarding jobs"
    )
    parser.add_argument(
        "integer",
        metavar="N",
        type=int,
        help="the number of bundles to submit and wait",
    )
    global args
    args = parser.parse_args()

    f = flux.Flux()
    f.event_subscribe("job-state")
    f.msg_watcher_create(job_state_cb, 0, "job-state").start()
    submit_bundles(f, args.integer)
    print("bookkeeper: waiting until all jobs complete")
    f.reactor_run(f.get_reactor(), 0)
    print("bookkeeper: all jobs completed")


main()

# vi: ts=4 sw=4 expandtab
