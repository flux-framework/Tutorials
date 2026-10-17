# Flux Tutorial — Coscheduling with QRMI, and Fluence

Open a terminal in the sidebar and work through the notebooks next to it.

## Module 1: Coscheduling quantum and classical work
1. [Coscheduling with QRMI](module1/01_coscheduling_qrmi.ipynb) — the instance and its plugins, a mocked pair, then the same pair against an IBM QPU through QRMI

The classical half of the pair is [`module1/workload.py`](module1/workload.py).

## Module 2: Fluence in Kubernetes
1. [Fluence](module2/01_fluence.ipynb) — a kind cluster on your docker, fluence installed into it, a gang placed all or nothing, and two modeled QPU backends shared by three pods

Everything the notebook applies is in [`module2/manifests/`](module2/manifests).

Module 2 needs the container started with the docker socket mounted, see the README one level up.
