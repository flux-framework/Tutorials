# Chapter 5: Hybrid Quantum-Classical Workflows with Flux and AWS Braket

This chapter adds a quantum backend to the tutorial. It runs a QAOA max-cut
optimization as a hybrid quantum-classical workflow: a classical COBYLA optimizer
scheduled by Flux repeatedly evaluates a quantum circuit on the AWS Braket **SV1**
state-vector simulator.

The notebook, [05_flux_quantum_braket.ipynb](05_flux_quantum_braket.ipynb), walks
through five parts:

1. Setup and confirming SV1 access
2. QAOA on the free **local** simulator under Flux (no cost)
3. QAOA on **AWS Braket SV1** under Flux
4. An **ensemble** of quantum tasks with Flux
5. (Advanced) The same pipeline as **containers in Usernetes**

## Files

- `scripts/qaoa_maxcut.py` — self-contained QAOA max-cut driver. Condenses the
  four-stage pipeline from
  [converged-computing/quantum-braket](https://github.com/converged-computing/quantum-braket)
  (problem-generator → transpiler → gateway → optimizer) into one script that Flux
  can launch. Supports `--backend local` (free) and `--backend sv1`.
- `braket-qaoa-pipeline.yaml` — the containerized pipeline as a Kubernetes Pod for
  the optional Usernetes section, using the published
  `ghcr.io/converged-computing/quantum-braket-*` images.

## Credentials and IAM

The tutorial VM has **no** stored AWS keys (`~/.aws` is removed at boot). It runs
with an IAM instance role whose only Braket permission is the SV1 device ARN
`arn:aws:braket:::device/quantum-simulator/amazon/sv1`. The Braket SDK picks up the
instance-role credentials automatically via instance metadata, so the notebook
never configures a key, and any attempt to reach another device is denied.

The role's Braket + S3 permissions come from
[`../../ec2/jupyterhub-braket-policy.json`](../../ec2/jupyterhub-braket-policy.json).
See the top-level [README](../../README.md) for the one-time deployment commands
(attaching the policy and creating the Braket service-linked role).

## Cost

SV1 is billed at **$0.075 / minute** in `us-east-1`, with **one free hour of
simulation per month** for the first 12 months. The circuits here run in seconds,
so a full run is a few cents at most (often $0 under the free tier). Use the
`local` backend for cost-free testing.
