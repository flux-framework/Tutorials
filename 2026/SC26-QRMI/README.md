# Coscheduling Quantum and Classical Work with QRMI

This is a notebook tutorial for the [flux-quantum](https://github.com/converged-computing/flux-quantum)
plugin to demonstrate using the QRMI bindings. 

> How does it work?

When you do a `flux submit` with the plugin we create a hybrid pair. The classical workers are held (reserved) until they await the signal of a scout job that submits the work and monitors the queue. The scout is going to open the session and wait for it to be first in the queue, and then fire an RPC "release" signal to the scheduler. While different backends are supported, this backend demonstrates using the the Quantum Resource Management Interface [QRMI](https://github.com/qiskit-community/qrmi). 

The demo runs first against a mock vendor (no token required), and then against an IBM QPU. You can adjust what you run depending on the credits or dollars you want to spend on IBM Quantum.

## Modules

We will add modules as needed.

| Module | What you will do |
|---|---|
| **1. Coscheduling with QRMI** | [`module1/`](tutorial/module1) — look at the instance and the plugins, run a mocked pair, then run the same pair against `ibm_kingston` through QRMI |

## How the notebooks work

Every notebook is **markdown with copy-paste bash blocks**, read alongside a terminal opened in the JupyterLab sidebar. Nothing in a notebook is executed as a cell, and this is my preference because I (@vsoch) dislike notebooks and want a more terminal-based experience. 

## Building and running the container

Full details, including what the base image is and smoke tests, are in
[`docker/README.md`](docker/README.md). The short version, from this directory:

```bash
docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:qrmi-notebook .
docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:qrmi-notebook
```

Open the URL with the token that JupyterLab prints, at `http://127.0.0.1:8888/lab?token=...`.
The launcher has one tile for the notebook. Open it, then open a terminal from the
sidebar and drag it next to the notebook.

The image is a layer on top of the flux-quantum QRMI demo image, which carries the
whole stack: flux-core, a flux-sched with the `coschedule` queue policy, the
flux-quantum jobtap and cli plugins, qrmi with qiskit, and the ibmcloud cli. The
container starts a one broker Flux instance with that configuration and runs
JupyterLab as its initial program, so every terminal you open is already in the
instance.

### Credentials for the IBM part

QRMI reads credentials from the environment, and Flux copies your shell environment
into both halves of the pair. Exporting inside a JupyterLab terminal is enough, and the
notebook walks through that. To have them there from the start instead:

```bash
docker run --rm -it -p 8888:8888 -e IBM_CLOUD_TOKEN=<your api key> ghcr.io/flux-framework/flux-tutorial:qrmi
```

Nothing in the image, the build, or the plugin reads a credential value. The ingest
validator checks by name that the variables the chosen resource needs are present.

### Editing the notebook live

To edit notebooks on your host and see changes without a rebuild, mount over the
copied tree:

```bash
docker run --rm -it -p 8888:8888 -v $(pwd)/tutorial:/home/ubuntu/tutorial ghcr.io/flux-framework/flux-tutorial:qrmi
```

## Files

| Path | Purpose |
|---|---|
| [`docker/`](docker) | The Dockerfile, launcher tiles, requirements, hub entrypoint, and icon |
| [`tutorial/`](tutorial) | What is copied into the image at `/home/ubuntu/tutorial` |
| [`tutorial/module1/01_coscheduling_qrmi.ipynb`](tutorial/module1/01_coscheduling_qrmi.ipynb) | The notebook |
| [`tutorial/module1/workload.py`](tutorial/module1/workload.py) | The classical half of the pair, a Bell circuit through the QRMI sampler |
| [`tutorial/assets/`](tutorial/assets) | The Flux logo the notebook banner uses |
