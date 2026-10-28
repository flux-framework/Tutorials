#!/bin/bash
# Part 1: the resource graph, and what a hybrid request looks like.
. "$(dirname "$0")/lib.sh"

section "Part 1. The resource graph"
say "First the plain Fluxion view. Nothing quantum yet: eight nodes with four cores each, all in the normal queue. flux-lead runs the broker and is kept out of scheduling."
run flux resource list

heading "The quantum devices"
say "Each QPM is a vertex in the same graph. qpus is how many jobs may hold the device at once, and qubits is how wide the device is. fake-iqm allows two at a time, the rest one."
run flux-qfw devices
say "Here are the qpu vertices straight from the graph. They sit under the cluster root, beside the nodes and not under any node, because any node can reach a device over the network."
run "flux kvs get resource.R | jq -c '[.scheduling.graph.nodes[].metadata | select(.type==\"qpu\") | .paths.containment]'"

heading "What a hybrid request looks like"
say "The --qfw-qpu flag adds a second entry to what the job asks for, so Fluxion matches the nodes and the device in one pass. A dry run shows the request without submitting anything."
run "flux run --dry-run -N2 -n8 --qfw-qpu=nwqsim --qfw-max-qubits=5 hostname | jq -c '.resources[1], (.attributes.system.qfw | {qpu, scope, queue, max_qubits})'"
say "The first line is the device entry. Its qpu asks for 5 qubits, so Fluxion only matches a device at least that wide. The second line is the envelope, the size of the work, which also goes to the QPM."
say "Ask for more qubits than the device has, and the job is refused right here, at submit."
run "flux run --dry-run -N1 -n1 --qfw-qpu=nwqsim --qfw-max-qubits=64 hostname > /dev/null"
