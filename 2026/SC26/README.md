# Flux Tutorial — SC26

Materials for the Flux Framework tutorial at [SC26](https://sc26.supercomputing.org),
McCormick Place, Chicago, 15–20 November 2026.

## Modules

| Module | Presentation | Hands-on |
|---|---|---|
| **1. Flux Foundations & Hierarchical Scheduling** | Background and story, limitations of traditional schedulers, the graph-based model, Flux as a system manager, community growth | [`module1/`](tutorial/module1) — foundations, Python SDK, internals + plugin workshop |
| **2. Converged Environments: Cloud, AI/ML, and Kubernetes** | Flux in the cloud, user-space Kubernetes on-prem, Kubeflow Trainer | [`module2/`](tutorial/module2) — Usernetes, Flux Operator, Kubeflow, quantum |
| **3. Lightning Talks, Research, and Open Forum** | Plugins and development, the admin perspective, real-world R&D | [`module3/`](tutorial/module3) — plugin show and tell, trivia, wrap-up |

## How the notebooks work

Every notebook is **markdown with copy-paste bash blocks**, read alongside a terminal
opened in the JupyterLab sidebar. This is deliberate: `flux top`, `flux alloc`, manpages,
and anything using `$FLUX_URI` need a real TTY. The Python SDK tutorial is an actual notebook.

## Theme

The tutorial theme is Chicago deep dish, in the actual Flux brand blues (`#036291` and
`#91C2D8`, taken from `assets/Flux-logo.svg`) with a crust-gold accent. A deep dish is
built in layers, each doing its own job, in a deliberate order. A single-queue scheduler
is a flat pizza. `flux uptime` tells you which layer you are standing on.

## Interactive pieces

- **Side quests** (Module 1, end of every notebook) — optional ten-minute challenges with folded-up answers: chain the Chicago hot dog scripts with `--dependency`, pack six pizzas into a six-core `flux alloc`, find out why a job died from its eventlog, write a `flux menu` subcommand, and more.
- **Plugin workshop** (Module 1, notebook 3) — a half-written **Python** job validator in [`plugin-workshop/`](tutorial/module1/plugin-workshop). We give the class and the resource lookups and attendees write the policy decision. A Lua job shell plugin skeleton is there too.
- **Deep Dish Trivia** (Module 3) — 24 questions, 4 rounds, a joke between each. Self-contained static page in [`trivia/`](tutorial/module3/trivia).

## Building and running the container

Full instructions, including smoke tests, are in [`docker/README.md`](docker/README.md).
The short version, from this directory:

```bash
docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:sc26 .
docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:sc26
```

