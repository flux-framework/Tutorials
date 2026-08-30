"""Cap how many cores a single order may request.

A complete Flux job validator plugin, for reference. Rejects any job asking for
more cores than the configured limit, and refuses a short list of toppings.

    flux run --dry-run -n8 sleep 60 \\
        | flux job-validator --jobspec-only \\
              --plugins=./plugin-workshop/oven_capacity.py --max-cores=4
"""

import errno

from flux.job import JobspecV1
from flux.job.validator import ValidatorPlugin

BANNED = {"pineapple", "ketchup"}


class Validator(ValidatorPlugin):

    def __init__(self, parser):
        parser.add_argument(
            "--max-cores",
            metavar="N",
            type=int,
            default=4,
            help="maximum cores a single job may request. default: 4",
        )
        super().__init__(parser)

    def configure(self, args):
        """Read the core limit from the command line."""
        self.max_cores = args.max_cores

    def validate(self, job):
        """Reject oversized orders and banned toppings."""
        counts = JobspecV1(**job.jobspec).resource_counts()
        ncores = counts.get("core", 0)

        if ncores > self.max_cores:
            return (
                errno.EINVAL,
                f"order needs {ncores} cores, the oven fits {self.max_cores}",
            )

        name = job.jobspec["attributes"]["system"].get("job_name", "")
        banned = BANNED & set(name.lower().split("-"))
        if banned:
            return (errno.EINVAL, f"we do not serve {', '.join(sorted(banned))}")

        return None
