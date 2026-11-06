#!/usr/bin/env python3
"""
qaoa_maxcut.py -- a single-file QAOA max-cut demo for the Flux + Usernetes tutorial.

This is a self-contained condensation of the four-stage pipeline from
https://github.com/converged-computing/quantum-braket
(problem-generator -> transpiler -> gateway -> optimizer) into one script so it
can be launched directly by Flux (``flux run`` / ``flux submit``) on the tutorial
VM. It builds a QAOA ansatz for max-cut on a random k-regular graph, evaluates it
on a quantum backend, and optimizes the variational parameters with COBYLA.

Credentials
-----------
The default backend is the fully local simulator, which needs NO AWS account and
NO credentials. Nothing is configured or transmitted; the circuits run on this VM.

The optional --backend sv1 path uses AWS Braket. Only use it if you have your own
Braket access; the tutorial itself never requires AWS credentials. (On an instance
that happens to carry a Braket-enabled IAM role, boto3 would pick that up
automatically via instance metadata -- but that is not needed for this tutorial.)

Backends
--------
--backend local   Local state-vector simulator in the Braket SDK. No AWS calls,
                  no credentials, no cost. This is the DEFAULT and what the
                  tutorial uses throughout.
--backend sv1     (Optional) AWS Braket SV1 on-demand simulator. Requires AWS
                  Braket access and is billed per minute. Not used by the
                  tutorial by default.

Cost
----
The default local backend is free. The optional SV1 backend is $0.075/minute in
us-east-1 (with a 1-hour/month free tier for the first 12 months); a tiny circuit
runs in seconds, and the Braket Cost Tracker prints the estimate when used.

Examples
--------
    # Local run (default, no AWS, no cost): full hybrid optimization
    flux run python3 scripts/qaoa_maxcut.py --nodes 6 --max-iter 5

    # Local, single circuit evaluation (no optimizer loop)
    flux run python3 scripts/qaoa_maxcut.py --backend local --max-iter 0

    # (Optional) real SV1 run, only if you have AWS Braket access
    flux run python3 scripts/qaoa_maxcut.py --backend sv1 --nodes 6 --max-iter 5

Environment variables (overridden by CLI flags if given):
    N_NODES, K_REGULAR, SEED, P_LAYERS, N_SHOTS, MAX_ITER, BRAKET_DEVICE, BACKEND
"""

import argparse
import json
import math
import os
import random
import sys
import time

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"


# --------------------------------------------------------------------------- #
# 1. Problem generation: random k-regular graph (from problem-generator)
# --------------------------------------------------------------------------- #
def generate_k_regular_graph(n, k, seed):
    """Random k-regular graph on n nodes via the configuration/pairing model."""
    if n * k % 2 != 0:
        raise ValueError(f"n*k must be even (got n={n}, k={k})")
    if k >= n:
        raise ValueError(f"k must be less than n (got k={k}, n={n})")

    rng = random.Random(seed)
    for _attempt in range(100):
        stubs = []
        for node in range(n):
            stubs.extend([node] * k)
        rng.shuffle(stubs)

        edges = set()
        valid = True
        for i in range(0, len(stubs), 2):
            u, v = stubs[i], stubs[i + 1]
            if u == v or (min(u, v), max(u, v)) in edges:
                valid = False
                break
            edges.add((min(u, v), max(u, v)))
        if valid:
            return [(u, v, 1.0) for u, v in sorted(edges)]

    raise RuntimeError(
        f"Could not build a {k}-regular graph on {n} nodes in 100 tries; "
        "try a different seed or smaller k."
    )


# --------------------------------------------------------------------------- #
# 2. Circuit construction (from transpiler / gateway)
# --------------------------------------------------------------------------- #
def build_qaoa_circuit(n_qubits, edges, gammas, betas):
    """Build a Braket Circuit for the current (gammas, betas). Supports p >= 1."""
    from braket.circuits import Circuit

    circ = Circuit()
    for i in range(n_qubits):
        circ.h(i)

    for layer in range(len(gammas)):
        gamma = gammas[layer]
        beta = betas[layer]
        # Cost unitary: CNOT - RZ(gamma) - CNOT on every edge
        for u, v, _ in edges:
            circ.cnot(u, v)
            circ.rz(v, gamma)
            circ.cnot(u, v)
        # Mixer unitary: RX(2*beta) on every qubit
        for i in range(n_qubits):
            circ.rx(i, 2 * beta)
    return circ


def initial_params(p, seed):
    rng = random.Random(seed)
    gammas = [rng.uniform(0.1, math.pi - 0.1) for _ in range(p)]
    betas = [rng.uniform(0.1, math.pi / 2 - 0.1) for _ in range(p)]
    return gammas, betas


# --------------------------------------------------------------------------- #
# 3. Cost function (from gateway)
# --------------------------------------------------------------------------- #
def maxcut_cost(counts, edges, n_qubits):
    """Expected cut value over the measured bitstrings."""
    total_shots = sum(counts.values())
    total = 0.0
    for bitstring, shots in counts.items():
        if len(bitstring) != n_qubits:
            bitstring = bitstring.zfill(n_qubits)
        bits = [int(b) for b in bitstring]
        cut = sum(w for u, v, w in edges if bits[u] != bits[v])
        total += shots * cut
    return total / total_shots


# --------------------------------------------------------------------------- #
# Backend wiring
# --------------------------------------------------------------------------- #
def get_device(backend, device_arn):
    if backend == "local":
        from braket.devices import LocalSimulator

        return LocalSimulator()
    from braket.aws import AwsDevice

    return AwsDevice(device_arn)


def run_circuit(device, circ, shots):
    task = device.run(circ, shots=shots)
    return task.result().measurement_counts


# --------------------------------------------------------------------------- #
# Main driver
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description="QAOA max-cut on AWS Braket SV1 or local sim.")
    p.add_argument("--backend", default=os.environ.get("BACKEND", "local"),
                   choices=["local", "sv1"], help="Quantum backend to use.")
    p.add_argument("--device-arn", default=os.environ.get("BRAKET_DEVICE", SV1_ARN),
                   help="Braket device ARN (only used when --backend sv1).")
    p.add_argument("--nodes", type=int, default=int(os.environ.get("N_NODES", 6)))
    p.add_argument("--k", type=int, default=int(os.environ.get("K_REGULAR", 3)))
    p.add_argument("--seed", type=int, default=int(os.environ.get("SEED", 42)))
    p.add_argument("--p-layers", type=int, default=int(os.environ.get("P_LAYERS", 1)))
    p.add_argument("--shots", type=int, default=int(os.environ.get("N_SHOTS", 100)))
    p.add_argument("--max-iter", type=int, default=int(os.environ.get("MAX_ITER", 5)),
                   help="COBYLA iterations. Use 0 for a single circuit evaluation.")
    args = p.parse_args()

    print(f"[qaoa] backend={args.backend} nodes={args.nodes} k={args.k} "
          f"p={args.p_layers} shots={args.shots} max_iter={args.max_iter}")

    edges = generate_k_regular_graph(args.nodes, args.k, args.seed)
    n_qubits = args.nodes
    print(f"[qaoa] graph: {n_qubits} nodes, {len(edges)} edges "
          f"(upper-bound cut = {len(edges)})")

    gammas0, betas0 = initial_params(args.p_layers, args.seed)

    # Build the device once. On SV1 this validates the device ARN via GetDevice.
    try:
        device = get_device(args.backend, args.device_arn)
    except Exception as e:  # noqa: BLE001
        print(f"[qaoa] ERROR creating device: {e}", file=sys.stderr)
        sys.exit(1)

    # Optional cost tracking (SV1 only; the tracker is a no-op cost for local).
    tracker_ctx = None
    if args.backend == "sv1":
        try:
            from braket.tracking import Tracker

            tracker_ctx = Tracker()
            tracker_ctx.__enter__()
        except Exception:  # noqa: BLE001
            tracker_ctx = None

    eval_count = [0]

    def evaluate(gammas, betas):
        circ = build_qaoa_circuit(n_qubits, edges, gammas, betas)
        t0 = time.time()
        counts = run_circuit(device, circ, args.shots)
        dt = time.time() - t0
        cost = maxcut_cost(counts, edges, n_qubits)
        print(f"[qaoa] eval {eval_count[0]:2d}  cut={cost:7.4f}  "
              f"gamma0={gammas[0]:.4f} beta0={betas[0]:.4f}  ({dt:.2f}s)")
        eval_count[0] += 1
        return cost

    # Initial evaluation
    best_cost = evaluate(gammas0, betas0)
    best_gammas, best_betas = gammas0, betas0

    # Optional COBYLA optimization loop (maximize cut == minimize -cut)
    if args.max_iter > 0:
        try:
            import numpy as np
            from scipy.optimize import minimize
        except ImportError:
            print("[qaoa] scipy/numpy not available; skipping optimization.",
                  file=sys.stderr)
        else:
            x0 = np.array(gammas0 + betas0, dtype=float)
            pl = args.p_layers

            def objective(x):
                g = list(x[:pl])
                b = list(x[pl:])
                return -evaluate(g, b)

            res = minimize(objective, x0, method="COBYLA",
                           options={"maxiter": args.max_iter, "rhobeg": 0.5})
            best_gammas = list(res.x[:pl])
            best_betas = list(res.x[pl:])
            best_cost = -res.fun
            print(f"[qaoa] optimizer done: {res.message}")

    approx_ratio = best_cost / len(edges) if edges else 0.0
    print("\n[qaoa] ===== Result =====")
    print(f"  best cut            : {best_cost:.4f}")
    print(f"  approximation ratio : {approx_ratio:.4f}")
    print(f"  evaluations         : {eval_count[0]}")

    if tracker_ctx is not None:
        try:
            cost = tracker_ctx.simulator_tasks_cost()
            print(f"  estimated SV1 cost  : ${float(cost):.4f} USD")
            tracker_ctx.__exit__(None, None, None)
        except Exception:  # noqa: BLE001
            pass

    # Emit a machine-readable summary line (handy for Flux output scraping)
    summary = {
        "backend": args.backend,
        "n_nodes": args.nodes,
        "n_edges": len(edges),
        "p": args.p_layers,
        "shots": args.shots,
        "best_cut": round(best_cost, 6),
        "approximation_ratio": round(approx_ratio, 6),
        "evaluations": eval_count[0],
    }
    print(f"[qaoa] SUMMARY {json.dumps(summary)}")


if __name__ == "__main__":
    main()
