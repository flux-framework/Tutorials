#!/usr/bin/env python3

import json
import os
import re
import flux
from flux.job import JobspecV1

f = flux.Flux()

compute_jobreq = JobspecV1.from_command(
    command=["./compute.py", "120"], num_tasks=6, num_nodes=3, cores_per_task=2
)
compute_jobreq.cwd = os.getcwd()
compute_jobreq.environment = dict(os.environ)
print(flux.job.submit(f, compute_jobreq))

io_jobreq = JobspecV1.from_command(
    command=["./io-forwarding.py", "120"], num_tasks=3, num_nodes=3, cores_per_task=1
)
io_jobreq.cwd = os.getcwd()
io_jobreq.environment = dict(os.environ)
print(flux.job.submit(f, io_jobreq))
