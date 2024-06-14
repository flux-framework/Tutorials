#!/usr/bin/env python3

import os
import argparse
import concurrent.futures

from flux.job import JobspecV1, FluxExecutor


def main():
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument("njobs", nargs="?", type=int, default=10)
    args = parser.parse_args()
    # create jobspec for compute.py
    compute_jobspec = JobspecV1.from_command(
        command=["./compute.py", "10"], num_tasks=4, num_nodes=2, cores_per_task=2
    )
    compute_jobspec.cwd = os.getcwd()
    compute_jobspec.environment = dict(os.environ)
    # create bad jobspec that will fail
    bad_jobspec = JobspecV1.from_command(["/bin/false"])
    # create an executor to submit jobs
    with FluxExecutor() as executor:
        futures = []
        # submit half successful jobs and half failures
        for _ in range(args.njobs // 2):
            futures.append(executor.submit(compute_jobspec))
            print(f"submit: {id(futures[-1])} compute_jobspec")
        for _ in range(args.njobs // 2, args.njobs):
            futures.append(executor.submit(bad_jobspec))
            print(f"submit: {id(futures[-1])} bad_jobspec")
        for fut in concurrent.futures.as_completed(futures):
            if fut.exception() is not None:
                print(f"wait: {id(fut)} Error: job raised error {fut.exception()}")
            elif fut.result() == 0:
                print(f"wait: {id(fut)} Success")
            else:
                print(f"wait: {id(fut)} Error: job returned exit code {fut.result()}")


if __name__ == "__main__":
    main()

# vim: tabstop=4 shiftwidth=4 expandtab
