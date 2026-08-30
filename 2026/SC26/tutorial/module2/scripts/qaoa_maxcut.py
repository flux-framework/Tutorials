#!/usr/bin/env python3
"""QAOA max-cut on a local statevector simulator, submitted as a Flux job.

Splits a graph of pizza orders across two ovens so that as many "conflicting"
pairs as possible end up in different ovens. No cloud account or quantum
hardware is required; qiskit-aer runs entirely on the CPU Flux gave us.
"""

import argparse
import json

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

# Each edge is a pair of orders that should not share an oven.
DEFAULT_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (1, 3)]


def build_circuit(edges, num_qubits, gammas, betas):
    """Build a p-layer QAOA circuit for max-cut on the given edge list."""
    qc = QuantumCircuit(num_qubits)
    qc.h(range(num_qubits))
    for gamma, beta in zip(gammas, betas):
        for i, j in edges:
            qc.cx(i, j)
            qc.rz(2.0 * gamma, j)
            qc.cx(i, j)
        for q in range(num_qubits):
            qc.rx(2.0 * beta, q)
    qc.measure_all()
    return qc


def cut_value(bitstring, edges):
    """Count edges whose endpoints land in different partitions."""
    bits = bitstring[::-1]
    return sum(1 for i, j in edges if bits[i] != bits[j])


def mean_cut(counts, edges):
    """Return the shot-weighted average cut value for a counts dict."""
    total = sum(counts.values())
    return sum(cut_value(b, edges) * n for b, n in counts.items()) / total


def run(edges, num_qubits, layers, shots, seed):
    """Optimize QAOA parameters and return the best partition found."""
    sim = AerSimulator(seed_simulator=seed)
    rng = np.random.default_rng(seed)

    def objective(params):
        gammas, betas = params[:layers], params[layers:]
        qc = build_circuit(edges, num_qubits, gammas, betas)
        counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
        return -mean_cut(counts, edges)

    x0 = rng.uniform(0, np.pi, 2 * layers)
    result = minimize(objective, x0, method="COBYLA", options={"maxiter": 120})

    gammas, betas = result.x[:layers], result.x[layers:]
    qc = build_circuit(edges, num_qubits, gammas, betas)
    counts = sim.run(transpile(qc, sim), shots=shots).result().get_counts()
    best = max(counts, key=lambda b: (cut_value(b, edges), counts[b]))
    return {
        "layers": layers,
        "shots": shots,
        "evaluations": int(result.nfev),
        "mean_cut": round(mean_cut(counts, edges), 3),
        "best_bitstring": best,
        "best_cut": cut_value(best, edges),
        "max_possible_edges": len(edges),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-p", "--layers", type=int, default=2)
    parser.add_argument("-s", "--shots", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=1848)
    args = parser.parse_args()

    edges = DEFAULT_EDGES
    num_qubits = max(max(e) for e in edges) + 1
    out = run(edges, num_qubits, args.layers, args.shots, args.seed)

    bits = out["best_bitstring"][::-1]
    oven_a = [i for i in range(num_qubits) if bits[i] == "0"]
    oven_b = [i for i in range(num_qubits) if bits[i] == "1"]
    out["oven_a"] = oven_a
    out["oven_b"] = oven_b

    print(json.dumps(out, indent=2))
    print(f"\nOven A: orders {oven_a}")
    print(f"Oven B: orders {oven_b}")
    print(f"Separated {out['best_cut']} of {len(edges)} conflicting pairs.")


if __name__ == "__main__":
    main()
