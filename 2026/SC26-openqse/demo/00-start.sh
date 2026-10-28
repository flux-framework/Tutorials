#!/bin/bash
# Before you start: the instance, its nodes, and a clean queue.
. "$(dirname "$0")/lib.sh"

section "Before you start"
say "This terminal is already connected to a Flux instance with nine brokers. Rank 0 is flux-lead, and c1 through c8 have four cores each."
run flux getattr size
run "flux resource list -s all -no '{nodelist}'"

heading "Start fresh"
say "Cancel anything left over and clear the job list, so what we see next is ours."
run "flux cancel --all --user=all; flux queue idle --timeout=60; flux job purge --force --num-limit=0"
run qjobs
