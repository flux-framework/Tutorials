"""Reject orders the kitchen can't handle.

A Flux job validator plugin. Every job submitted to this instance passes through
validate() before it reaches the scheduler, so this is where site policy lives.

Test it without touching the instance:

    flux run --dry-run -n4 sleep 60 \\
        | flux job-validator --jobspec-only --plugins=./plugin-workshop/pizza_policy.py

Then load it for real:

    flux module reload job-ingest \\
        validator-plugins=jobspec,$(pwd)/plugin-workshop/pizza_policy.py
"""

import errno

from flux.job import JobspecV1
from flux.job.validator import ValidatorPlugin


class Validator(ValidatorPlugin):

    def validate(self, job):
        """Return None to accept the job, or (errno, message) to reject it."""

        # job.jobspec is the submitted jobspec as a plain dict.
        # job.userid, job.flags, and job.urgency are also available.
        counts = JobspecV1(**job.jobspec).resource_counts()
        ncores = counts.get("core", 0)
        nnodes = counts.get("node", 0)
        command = job.jobspec["tasks"][0]["command"]

        # YOUR CODE HERE.
        #
        # Decide whether this order goes to the kitchen. Return nothing to
        # accept it, or a tuple to send it back with a message the user sees:
        #
        #     return (errno.EINVAL, "we don't do pineapple")
        #
        # Ideas:
        #   * Cap ncores and reject anything over the limit
        #   * Reject a command by name, and say why
        #   * Require a job name, via job.jobspec["attributes"]["system"]
        #   * Only allow submissions during business hours
        #   * Reject anything asking for zero nodes, on principle
        return None
