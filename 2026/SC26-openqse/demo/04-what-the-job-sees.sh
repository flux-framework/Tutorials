#!/bin/bash
# Part 4: what a job sees, for job scope and site scope.
. "$(dirname "$0")/lib.sh"
fresh

section "Part 4. What the job sees"
heading "Job scope"
say "This is the default for the simulators here, and there is no reservation at all. Every rank learns the job's own hosts, which is where the simulator will run, and a launch agent so MPI starts its daemons with flux exec instead of ssh."
run "flux run -N2 -n2 --qfw-qpu=shim-ornl-20q sh -c 'echo rank \$FLUX_TASK_RANK: scope=\$QFW_QPU_SCOPE nodes=\$QFW_SIMULATOR_NODES agent=\$(basename \$PRTE_MCA_plm_ssh_agent)'"

heading "Site scope"
say "Now force site scope on the same device. The job already holds the device, so the shell acquires nothing. It tells the QPM the job has its device when the job starts and again when it exits, and the QPM hands back the reservation id QFw needs. The mock backend stands in for the QPM."
run "flux run -N1 -n1 --qfw-qpu=shim-ornl-20q --qfw-scope=site --qfw-max-qubits=3 sh -c 'echo QFW_RESERVATIONS=\$QFW_RESERVATIONS'"

heading "An allocation registers once"
say "Like salloc --qpu on Slurm. The allocation's shell registers once when it starts, and every step inside inherits the same reservation. Neither step asks for the device."
run "flux alloc -N1 -n2 --qfw-qpu=iqm-ornl-20q --qfw-scope=site --qfw-max-qubits=5 --qfw-max-shots=16 bash -c 'flux run -n2 sh -c \"echo step 1: \\\$QFW_RESERVATIONS\"; flux run -n1 sh -c \"echo step 2: \\\$QFW_RESERVATIONS\"'"
fresh
