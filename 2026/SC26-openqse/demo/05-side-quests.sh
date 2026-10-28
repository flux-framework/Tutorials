#!/bin/bash
# Side quests: three pairs on two leases, cancel while held, count the graph.
. "$(dirname "$0")/lib.sh"
fresh

section "Side quests"
heading "1. Three pairs, two leases"
say "fake-iqm has two leases. Submit three pairs. Two scouts run and open sessions. The third scout waits on the device, so its job stays held, and only two vendor sessions are ever open."
run "for i in 1 2 3; do flux submit --job-name=q\$i -N1 -n2 --qfw-qpu=fake-iqm sleep 60; done"
run "sleep 8; qjobs"
run flux-qfw sessions
fresh

heading "2. Cancel while held"
say "Cancel a job while it is still held. Its scout notices, closes the session, and exits, so the lease goes back right away."
run "X=\$(flux submit --job-name=cancelme -N1 -n1 --qfw-qpu=fake-iqm sleep 60)"
run "S=\$(flux jobs -no '{user.qfw_scout}' \$X); sleep 1; flux cancel \$X"
run "flux job wait-event -t 30 \$S clean"
run "flux job attach \$S 2>&1 | grep 'flux-qfw scout'"
fresh

heading "3. Count the graph"
say "Every vertex type in the graph: the cluster, the nodes and cores, and for each device a qdevice, its qpus, and one qubit pool per qpu."
run "flux kvs get resource.R | jq -r '.scheduling.graph.nodes[].metadata.type' | sort | uniq -c"
