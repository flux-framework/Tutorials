#!/usr/bin/env python3
"""The classical half of a coscheduled pair.

The scout opened the vendor session and posted it to this job's eventlog as a
memo. The wrapper put it in our environment, so there is nothing to wait for.
Each step is a function, called in order from main.

    flux submit -t 5m --quantum-vendor ibm --quantum-device ibm_kingston \\
        -n1 -- flux python workload.py --shots 100 --linger 0

Under the mock vendor there is a session and no QPU, so the script prints its
environment, lingers, and exits.
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

# QUANTUM_SESSION_ID is flux-quantum's name for the session. The other two are
# QRMI's job side contract, the same names its Slurm and LSF plugins set.
HANDOFF = ("QUANTUM_SESSION_ID", "QRMI_JOB_QPU_RESOURCES", "QRMI_JOB_QPU_TYPES")

# QRMI reads the session id under <resource> plus this. A handle, not a secret.
ACQUISITION_TOKEN = "_QRMI_JOB_ACQUISITION_TOKEN"


def section(title):
    print("\n== {} ==".format(title))


def print_quantum_environment():
    """Every quantum variable by name. Values only for the handoff and the handle."""
    section("quantum environment")
    print("{:<44} {}".format("FLUX_JOB_ID", os.environ.get("FLUX_JOB_ID", "?")))
    for name in HANDOFF:
        print("{:<44} {}".format(name, os.environ.get(name, "(unset)")))
    for name in sorted(os.environ):
        if name in HANDOFF or ("QRMI" not in name and "QUANTUM" not in name):
            continue
        if name.endswith(ACQUISITION_TOKEN):
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
    """A QuantumResource joined to the scout's session. No acquire, no release."""
    resources, types = get_job_qpu_resources_and_types()
    resource, rtype = resources[0], types[0]
    handle = os.environ.get(resource + ACQUISITION_TOKEN)
    print("resource:", resource, "type", rtype)
    print("handle:  ", handle, "(same as the session)" if handle == session else "(DIFFERS)")
    qr = QuantumResource(resource, resource_type(rtype))
    meta = qr.metadata()
    print("backend: ", meta.get("backend_name"), meta.get("backend_status"))
    if meta.get("session_id") not in (None, session):
        print("WARNING QRMI thinks the session is", meta.get("session_id"))
    return qr


def build_circuit(qubits):
    """A Bell state, or GHZ if wider. Every shot should be all zeros or all ones."""
    qc = QuantumCircuit(qubits)
    qc.h(0)
    for q in range(1, qubits):
        qc.cx(q - 1, q)
    qc.measure_all()
    return qc


def transpile_for_device(qc, qr):
    """Into the device's basis gates, from the target QRMI reads back."""
    target = get_target(qr)
    isa = generate_preset_pass_manager(optimization_level=1, target=target).run(qc)
    print("circuit: ", dict(isa.count_ops()))
    return isa


def run_sampler(qr, isa, shots):
    """Submit the circuit into the session."""
    sampler = SamplerV2(qr, options={"default_shots": shots})
    job = sampler.run([isa])
    print("task:    ", job.job_id())
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
        print(job.logs())
        sys.exit("the task failed")


def report_counts(job, qubits, shots):
    """The counts, and how many shots were all zeros or all ones."""
    counts = job.result()[0].data.meas.get_counts()
    print("counts:  ", dict(sorted(counts.items(), key=lambda kv: -kv[1])))
    ideal = {"0" * qubits, "1" * qubits}
    good = sum(v for k, v in counts.items() if k in ideal)
    print("fidelity:", "{}/{} shots in {}".format(good, shots, sorted(ideal)))


def linger(seconds, step=5):
    """Stay alive so the job can be watched. The session is open the whole time."""
    if seconds <= 0:
        return
    section("lingering for {}s so the job can be watched".format(seconds))
    while seconds > 0:
        print("working, {}s left".format(seconds))
        time.sleep(min(step, seconds))
        seconds -= step
    print("done")


def main():
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shots", type=int, default=100)
    ap.add_argument("--qubits", type=int, default=2, help="width of the circuit")
    ap.add_argument("--linger", type=int, default=30, help="seconds to stay alive after")
    args = ap.parse_args()

    print_quantum_environment()
    session = read_session()

    # the mock vendor hands over a session and no resource
    if not os.environ.get("QRMI_JOB_QPU_RESOURCES"):
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
