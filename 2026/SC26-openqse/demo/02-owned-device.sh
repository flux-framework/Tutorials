#!/bin/bash
# Part 2: a device the site owns. Jobs wait for it like a busy core.
. "$(dirname "$0")/lib.sh"
fresh

section "Part 2. A device the site owns"
heading "One hybrid job runs"
say "nwqsim has one qpu, so one job at a time can hold it. Job A asks for two nodes and the device. The device is free, so A gets both in one match and starts."
run "A=\$(flux submit --job-name=A-nwqsim -N2 -n8 --qfw-qpu=nwqsim sleep 300)"
run qjobs

heading "A second job on the same device waits"
say "Job B asks for the same device. There are free nodes, but the qpu is held by A, so B waits, the same way it would for a busy core."
run "B=\$(flux submit --job-name=B-nwqsim -N1 -n4 --qfw-qpu=nwqsim sleep 300)"
run qjobs

heading "Classical work is not blocked"
say "A plain job with no device runs right away on the free nodes. The device only holds back jobs that ask for it."
run "F=\$(flux submit --job-name=F-classical -N1 -n1 sleep 300)"
run qjobs

heading "The running job's R carries the qpu"
say "A's R, the record of what it was given, lists its nodes and the qpu together."
run "flux job info \$A R | jq -c '{nodes: .execution.nodelist, qpu: [.scheduling.graph.nodes[].metadata | select(.type==\"qpu\") | .paths.containment]}'"

heading "Freeing the device starts the waiting job"
say "Cancel A, and B starts on its own. Nobody had to tell the device B was next."
run "flux cancel \$A; sleep 2"
run qjobs
fresh
