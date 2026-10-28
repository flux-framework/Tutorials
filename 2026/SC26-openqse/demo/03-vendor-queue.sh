#!/bin/bash
# Part 3: a device behind a vendor queue. One submit becomes a scout pair.
. "$(dirname "$0")/lib.sh"
fresh

section "Part 3. A device behind a vendor queue"
say "When somebody else controls the device, a grant from Fluxion does not mean the device is ready. fake-iqm stands in for a vendor machine, and it is marked queue = external in conf/qfw.toml. You type the same command, but it becomes two jobs."
say "First a room check: there has to be space for your job plus one core for a scout. Then your job goes in first, held, with its nodes and no device. Then a small scout job goes in, naming your job, asking for one core and the qpu. The scout only runs while it holds a lease."

heading "Submit the pair"
say "Your job prints its reservation and sleeps, so there is time to look around. The envelope flags matter here, because the scout passes them to the vendor."
run "C=\$(flux submit --job-name=C-fake-iqm -N1 -n4 --qfw-qpu=fake-iqm --qfw-max-qubits=5 --qfw-max-shots=1024 sh -c 'echo QFW_RESERVATIONS=\$QFW_RESERVATIONS; sleep 300')"
run qjobs
say "The scout is running because a lease was free. Your job is in SCHED with free nodes: that is the hold, not a busy device. Your jobspec says so, and the scout's id was memoed onto your job."
run "flux job info \$C jobspec | jq -c '.attributes.system | {hold, pair: .qfw.pair}'"
run "S=\$(flux jobs -no '{user.qfw_scout}' \$C); flux job id --to=f58 \$S"

heading "The scout gets a session and releases your job"
say "The scout opens a session on the vendor's queue and waits for it. The fake vendor takes about twenty seconds. Watch it go from queued to running."
watch_n 5 6 flux-qfw sessions
run "flux job wait-event -t 60 \$C start"
say "Now the memos on your job. There are three: the scout's id, the session it opened, and the reservation with a released key, which is the moment the hold was cleared."
run "flux job eventlog \$C | grep memo"
run qjobs

heading "Your job got the scout's reservation"
say "Every task saw the same QFW_RESERVATIONS, the session the scout got before your job ran. The shell reserved nothing and will release nothing."
run "sleep 2; flux job eventlog -p guest.output \$C | grep -E 'QFW_RESERVATIONS|flux-qfw'"
say "Your job's R has no qpu in it. The scout's R does, which is where it belongs."
run "flux job info \$C R | jq '[.scheduling.graph.nodes[].metadata.type | select(. == \"qpu\")] | length'"
run "flux job info \$S R | jq '[.scheduling.graph.nodes[].metadata.type | select(. == \"qpu\")] | length'"

heading "When your job ends, the scout lets go"
say "The scout holds the device and the session exactly as long as your job runs. End your job and watch the scout follow it."
run "flux cancel \$C; sleep 5"
run qjobs
run flux-qfw sessions
say "The scout's own log tells the story: it held the device for your job, opened a session, released your job when the session was ready, and closed the session when your job finished."
run "flux job attach \$S 2>&1 | grep 'flux-qfw scout'"
fresh
