#!/usr/bin/env python3

import os
import argparse
import collections
import concurrent.futures as cf

from flux.job import JobspecV1, FluxExecutor


def main():
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument("njobs", nargs="?", type=int, default=10)
    parser.add_argument("window_size", nargs="?", type=int, default=2)
    args = parser.parse_args()
    print(args)
    # create jobspec for compute.py
    compute_jobspec = JobspecV1.from_command(
        command=["./compute.py", "5"], num_tasks=4, num_nodes=2, cores_per_task=2
    )
    compute_jobspec.cwd = os.getcwd()
    compute_jobspec.environment = dict(os.environ)
    # create a queue of the jobspecs to submit
    jobspec_queue = collections.deque(compute_jobspec for _ in range(args.njobs))
    futures = []  # holds incomplete futures
    with FluxExecutor() as executor:
        while jobspec_queue or futures:
            if len(futures) < args.window_size and jobspec_queue:
                fut = executor.submit(jobspec_queue.popleft())
                print(f"submit: {id(fut)}")
                futures.append(fut)
            else:
                done, not_done = cf.wait(futures, return_when=cf.FIRST_COMPLETED)
                futures = list(not_done)
                for fut in done:
                    if fut.exception() is not None:
                        print(
                            f"wait: {id(fut)} Error: job raised error "
                            f"{fut.exception()}"
                        )
                    elif fut.result() == 0:
                        print(f"wait: {id(fut)} Success")
                    else:
                        print(
                            f"wait: {id(fut)} Error: job returned "
                            f"exit code {fut.result()}"
                        )


if __name__ == "__main__":
    main()

# vim: tabstop=4 shiftwidth=4 expandtab
