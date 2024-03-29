#!/usr/bin/env python3

import time
import sys
import flux

from flux import job
from flux import constants

t0 = time.time()
jobs = []
label = "bulksubmit"

# open connection to broker
h = flux.Flux()


def log(s):
    print(label + ": " + s)


def progress(fraction, length=72, suffix=""):
    fill = int(round(length * fraction))
    bar = "\u2588" * fill + "-" * (length - fill)
    s = "\r|{0}| {1:.1f}% {2}".format(bar, 100 * fraction, suffix)
    sys.stdout.write(s)
    if fraction == 1.0:
        sys.stdout.write("\n")


def submit_cb(f):
    jobs.append(job.submit_get_id(f))


# asynchronously submit jobspec files from a directory
log("Starting...")
for file in sys.argv[1:]:
    with open(file) as jobspec:
        job.submit_async(h, jobspec.read(), waitable=True).then(submit_cb)

if h.reactor_run() < 0:
    h.fatal_error("reactor start failed")

total = len(jobs)
dt = time.time() - t0
jps = len(jobs) / dt
log("submitted {0} jobs in {1:.2f}s. {2:.2f}job/s".format(total, dt, jps))

count = 0
while count < total:
    # wait for jobs to complete in any order
    job.wait(h)
    count = count + 1
    if count == 1:
        log("First job finished in about {0:.3f}s".format(time.time() - t0))
    suffix = "({0:.1f} job/s)".format(count / (time.time() - t0))
    progress(count / total, length=58, suffix=suffix)

dt = time.time() - t0
log("Ran {0} jobs in {1:.1f}s. {2:.1f} job/s".format(total, dt, total / dt))

# vi: ts=4 sw=4 expandtab
