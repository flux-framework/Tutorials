#!/usr/bin/env python3
"""The classical half of a coscheduled pair, talking to the QPU through QRMI.

By the time this runs, the scout has opened the vendor session and posted it
to this job's eventlog as a memo. The wrapper the plugin put around this
command read that memo and put the session in our environment, so there is
nothing to wait for. Each step of what this script does is its own function:

    print_quantum_environment   what the pair handed us, by name
    read_session                the session id, or stop if there is none
    connect_to_resource         a QRMI QuantumResource joined to that session
    build_circuit               a Bell state, or GHZ if wider
    transpile_for_device        into the device's basis gates
    run_sampler                 submit it into the session
    wait_for_task               poll until it is final
    report_counts               the counts and how many shots were ideal
    linger                      stay alive long enough to be watched

    flux submit -t 5m --quantum-vendor ibm --quantum-device ibm_kingston \\
        -n1 -- flux python workload.py --shots 100 --linger 0

Under the mock vendor there is a session and no QPU, so the script prints its
environment, lingers, and exits. The same submit is the token free rehearsal.
qrmi and qiskit are imported at the top. If they are missing, the ImportError
says so and that is the right answer.
"""

import argparse
import os
import sys
import time

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qrmi import QuantumResource, get_job_qpu_resources_and_types
from qrmi.primitives.ibm import SamplerV2, get_target

from flux_quantum.backends.qrmi import resource_type

# The variables the pair sets. QUANTUM_SESSION_ID is flux-quantum's own name.
# The rest are QRMI's job-side contract: whichever workload manager acquired
# the QPU (QRMI's Slurm or LSF plugins, or flux-quantum here) names the
# resource and its type this way, and get_job_qpu_resources_and_types reads
# them. This script only knows the job side, so it is portable across them.
HANDOFF = (
    "QUANTUM_SESSION_ID",
    "QRMI_JOB_QPU_RESOURCES",
    "QRMI_JOB_QPU_TYPES",
)
ACQUISITION_TOKEN = "_QRMI_JOB_ACQUISITION_TOKEN"


def section(title):
    print()
    print("== {} ==".format(title))


def print_quantum_environment():
    """Everything quantum related in the environment, by name.

    The handoff variables are printed with their values. They carry the
    session id, which is a handle on an open session: it is useless without
    the api key and stops meaning anything when the scout closes the session.
    <resource>_QRMI_JOB_ACQUISITION_TOKEN is that handle under the name QRMI
    reads, and connect_to_resource prints it as "handle".
    Everything else with QRMI in its name is a credential or a setting, and
    only its name is printed.
    """
    section("quantum environment")
    print("{:<44} {}".format("FLUX_JOB_ID", os.environ.get("FLUX_JOB_ID", "?")))
    for name in HANDOFF:
        print("{:<44} {}".format(name, os.environ.get(name, "(unset)")))
    handoff = set(HANDOFF)
    for name in sorted(os.environ):
        if name in handoff or "QRMI" not in name and "QUANTUM" not in name:
            continue
        if name.endswith(ACQUISITION_TOKEN):
            # QRMI's name for the session handle. Not a secret, see above.
            print("{:<44} {}".format(name, os.environ[name]))
        else:
            print("{:<44} (set, value not shown)".format(name))


def read_session():
    """The session the scout opened, or exit if this job was not paired."""
    session = os.environ.get("QUANTUM_SESSION_ID")
    if not session:
        sys.exit("no QUANTUM_SESSION_ID, this job was not started by the scout")
    section("session")
    print("session: ", session)
    print("job:     ", os.environ.get("FLUX_JOB_ID", "?"), "on", os.uname().nodename)
    return session


def connect_to_resource(session):
    """A QuantumResource for the QPU the pair was given, joined to the session.

    QRMI reads <resource>_QRMI_JOB_ACQUISITION_TOKEN as a preset session id,
    so this resource submits into the scout's session without acquiring one
    of its own. No acquire, no release, the scout owns the session.
    """
    resources, types = get_job_qpu_resources_and_types()
    resource, rtype = resources[0], types[0]
    print("resource:", resource, "type", rtype)
    handle = os.environ.get(resource + ACQUISITION_TOKEN)
    print(
        "handle:  ",
        handle,
        "(same as the session)" if handle == session else "(DIFFERS from the session)",
    )
    qr = QuantumResource(resource, resource_type(rtype))
    meta = qr.metadata()
    print(
        "metadata:",
        {
            k: meta[k]
            for k in sorted(meta)
            if k in ("session_id", "backend_name", "backend_status")
        },
    )
    if meta.get("session_id") not in (None, session):
        print("WARNING QRMI thinks the session is", meta.get("session_id"))
    return qr


def build_circuit(qubits):
    """A Bell state, or a GHZ state if wider. Every shot should come back all
    zeros or all ones."""
    qc = QuantumCircuit(qubits)
    qc.h(0)
    for q in range(1, qubits):
        qc.cx(q - 1, q)
    qc.measure_all()
    return qc


def transpile_for_device(qc, qr):
    """The circuit has to be in the device's basis before IBM accepts it, so
    transpile against the target QRMI reads back from the backend."""
    target = get_target(qr)
    isa = generate_preset_pass_manager(optimization_level=1, target=target).run(qc)
    print("circuit: ", dict(isa.count_ops()))
    return isa


def run_sampler(qr, isa, shots):
    """Submit the circuit into the session through the QRMI SamplerV2."""
    sampler = SamplerV2(qr, options={"default_shots": shots})
    job = sampler.run([isa])
    print("task:    ", job.job_id(), "submitted into the session")
    return job


def wait_for_task(job, interval=2.0):
    """Poll until the task is final, printing each status change."""
    started = time.time()
    last = None
    while not job.in_final_state():
        status = job.status()
        if status != last:
            print("status:  ", status, "at {:.0f}s".format(time.time() - started))
            last = status
        time.sleep(interval)
    print("status:  ", job.status(), "after {:.0f}s".format(time.time() - started))
    if job.errored():
        print("logs:")
        print(job.logs())
        sys.exit("the task failed")


def report_counts(job, qubits, shots):
    counts = job.result()[0].data.meas.get_counts()
    print("counts:  ", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    ideal = {"0" * qubits, "1" * qubits}
    good = sum(v for k, v in counts.items() if k in ideal)
    print("fidelity:", "{}/{} shots in {}".format(good, shots, sorted(ideal)))


def linger(seconds, step=5):
    """Stay alive so the job can be seen running. The session is open the
    whole time, so on a real device keep this short, or pass --linger 0."""
    if seconds <= 0:
        return
    section("lingering for {}s so the job can be watched".format(seconds))
    left = seconds
    while left > 0:
        print("working, {}s left".format(left), flush=True)
        time.sleep(min(step, left))
        left -= step
    print("done")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shots", type=int, default=100)
    ap.add_argument(
        "--qubits", type=int, default=2, help="width of the GHZ/Bell circuit, 2"
    )
    ap.add_argument(
        "--linger",
        type=int,
        default=30,
        help="seconds to stay alive after the work, so the job can be watched, 30",
    )
    args = ap.parse_args()

    print_quantum_environment()
    session = read_session()

    if not os.environ.get("QRMI_JOB_QPU_RESOURCES"):
        # the mock vendor hands over a session and no resource. The handoff
        # worked, and that is all a rehearsal can show.
        print("resource: none, a rehearsal with no QPU. Nothing submitted.")
        linger(args.linger)
        return

    section("the circuit, through QRMI")
    qr = connect_to_resource(session)
    isa = transpile_for_device(build_circuit(args.qubits), qr)
    job = run_sampler(qr, isa, args.shots)
    wait_for_task(job)
    report_counts(job, args.qubits, args.shots)
    linger(args.linger)


if __name__ == "__main__":
    main()
