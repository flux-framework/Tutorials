"""Start the configured queues when the broker boots.

flux-core brings a named queue ([queues.<name>] in conf.d/system.toml) up
with scheduling stopped, and nothing in the standard rc1 starts it: a job
submitted to a fresh instance waits forever with "normal queue stopped".
The job manager checkpoints queue state, so a queue started once stays
started across broker restarts, but a recreated container (./do_stop.sh
delete, ./do_restart.sh --force-recreate) starts from nothing again.

This modprobe rc1 drop-in (installed under /etc/flux/modprobe/rc1.d) runs
`flux queue start --all` on rank 0 once the job manager and the scheduler
are loaded. It is disabled in an instance with no [queues] table, so nested
instances started by `flux alloc` and the single-broker test instances
under `flux start` are unaffected.
"""

from flux.modprobe import task


@task(
    "qfw-start-queues",
    ranks="0",
    needs=["job-manager"],
    after=["job-manager", "sched"],
    needs_config=["queues"],
)
def qfw_start_queues(context):
    context.bash("flux queue start --all --quiet")
