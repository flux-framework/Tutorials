#!/usr/bin/env python3

import time
import sys
import argparse
import concurrent.futures as cf

from flux.job import FluxExecutor, JobspecV1


def log(label, s):
    print(label + ": " + s)


def progress(fraction, length=72, suffix=""):
    fill = int(round(length * fraction))
    bar = "\u2588" * fill + "-" * (length - fill)
    s = f"\r|{bar}| {100 * fraction:.1f}% {suffix}"
    sys.stdout.write(s)
    if fraction == 1.0:
        sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Submit a command repeatedly using FluxExecutor"
    )
    parser.add_argument(
        "-n",
        "--njobs",
        type=int,
        metavar="N",
        help="Set the total number of jobs to run",
        default=100,
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        args.command = ["true"]
    t0 = time.perf_counter()
    label = "bulksubmit_executor"
    with FluxExecutor() as executor:
        compute_jobspec = JobspecV1.from_command(args.command)
        futures = [executor.submit(compute_jobspec) for _ in range(args.njobs)]
        # wait for the jobid for each job, as a proxy for the job being submitted
        for fut in futures:
            fut.jobid()
        # all jobs submitted - print timings
        dt = time.perf_counter() - t0
        jps = args.njobs / dt
        log(label, f"submitted {args.njobs} jobs in {dt:.2f}s. {jps:.2f}job/s")
        # wait for jobs to complete
        for i, _ in enumerate(cf.as_completed(futures)):
            if i == 0:
                log(
                    label,
                    f"First job finished in about {time.perf_counter() - t0:.3f}s",
                )
            jps = (i + 1) / (time.perf_counter() - t0)
            progress((i + 1) / args.njobs, length=58, suffix=f"({jps:.1f} job/s)")
    # print time summary
    dt = time.perf_counter() - t0
    log(label, f"Ran {args.njobs} jobs in {dt:.1f}s. {args.njobs / dt:.1f} job/s")


if __name__ == "__main__":
    main()
