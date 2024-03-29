#!/usr/bin/env python3

import os
import argparse

from flux.job import JobspecV1, FluxExecutor


def event_callback(future, event):
    print(f"job {future.jobid()} triggered event {event.name!r}")


# main
def main():
    # set up command-line parser
    parser = argparse.ArgumentParser(
        description="submit and wait for the completion of "
        "N bundles, each consisting of compute "
        "and io-forwarding jobs"
    )
    parser.add_argument(
        "njobs", metavar="N", type=int, help="the number of bundles to submit and wait",
    )
    args = parser.parse_args()
    # set up jobspecs
    compute_jobreq = JobspecV1.from_command(
        command=["./compute.py", "10"], num_tasks=6, num_nodes=3, cores_per_task=2
    )
    compute_jobreq.cwd = os.getcwd()
    compute_jobreq.environment = dict(os.environ)
    io_jobreq = JobspecV1.from_command(
        command=["./io-forwarding.py", "10"], num_tasks=3, num_nodes=3, cores_per_task=1
    )
    io_jobreq.cwd = os.getcwd()
    io_jobreq.environment = dict(os.environ)
    # submit jobs and register event callbacks for all events
    with FluxExecutor() as executor:
        futures = [executor.submit(compute_jobreq) for _ in range(args.njobs // 2)]
        futures.extend(
            executor.submit(io_jobreq) for _ in range(args.njobs // 2, args.njobs)
        )
        print("bookkeeper: all jobs submitted")
        for fut in futures:
            # each event can have a different callback
            for event in executor.EVENTS:
                fut.add_event_callback(event, event_callback)
        print("bookkeeper: waiting until all jobs complete")
    # exiting the context manager waits for the executor to complete all futures
    print("bookkeeper: all jobs completed")


main()

# vi: ts=4 sw=4 expandtab
