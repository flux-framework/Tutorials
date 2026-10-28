# QFw with Flux Tutorial

> The Framework Friends!

This is a notebook tutorial for running quantum jobs under Flux with QFw. Everything runs in one Docker container on your laptop. The quantum devices are simulators and a fake vendor queue, so you do not need an account anywhere or a real machine.

The notebook walks through four things. First you look at the resource graph and find the quantum devices sitting next to the nodes. Then you submit hybrid jobs on a device the site owns and watch them wait their turn, the same way jobs wait for a busy core. Then you try a device that sits behind a vendor queue, where the job is held until a session is ready. Last you look at what a job actually sees when it runs.

## Build and run

All you need is Docker.

```bash
git clone https://github.com/flux-framework/Tutorials
cd Tutorials/2026/SC26-openqse
make build
make run
```

The image is `ghcr.io/flux-framework/tutorials:sc26-openqse`. GitHub builds it from this directory, on pull requests to check it and on a manual run of the workflow to push it, so you can also `docker pull` it instead of building. Docker image names are lowercase, so the repository's `Tutorials` is `tutorials` here.

The first build takes a while. It compiles Fluxion, Open MPI, NWQ-Sim, TNQVM and QFw from source. After that it is cached.

When the container is up, open [http://localhost:8888](http://localhost:8888). Double click on the notebook in the left sidebar to open it. The notebook is for reading, and you run the commands in a terminal. Choose File, New, Terminal, then drag the terminal next to the notebook and paste each command into it as you go. The whole thing takes about fifteen minutes. Stop the container with Ctrl+C when you are done.

### Or run it all from a terminal

The `demo` directory has one script per part of the notebook, with the same commentary, so you can watch the whole tutorial run. Open a terminal in JupyterLab, which starts in `/tutorial` and is already connected to the instance, and run:

```bash
./demo/run-all.sh
```

Each command is shown before it runs, and the script waits for Enter. Run one part on its own with `./demo/03-vendor-queue.sh`, or set `DEMO_AUTO=1` to go straight through without stopping.
If your machine has more cores, `make build QFW_BUILD_JOBS=8` speeds up the QFw part of the build.

## What is in the container

The image builds everything from upstream sources.

| Piece | Where it comes from |
| --- | --- |
| flux-core | the `fluxrm/flux-core:noble` base image |
| Fluxion | the `hold` branch of [vsoch/flux-sched](https://github.com/vsoch/flux-sched) |
| flux-qfw | [openQSE/flux-qfw](https://github.com/openQSE/flux-qfw), the `updates` branch |
| QFw and DEFw | [openQSE/QFw](https://github.com/openQSE/QFw) |
| NWQ-Sim and TNQVM | built with QFw's own dependency scripts |
| libfabric, Open MPI, flux-pmix, QRMI | their upstream releases |

The resource graph is built at start by `flux-qfw add`, which encodes the nodes with Fluxion and adds the quantum devices beside them. The `flux/` directory has the `qfw-service` broker module, two drop ins that start the queue and load the module, and the launch agent.

## What is running

The container starts one Flux instance with nine brokers. Rank 0 is `flux-lead` and ranks 1 through 8 are `c1` through `c8` with four cores each. The resource graph has four quantum devices next to the nodes. JupyterLab is the instance's initial program, so any terminal you open in JupyterLab is already connected to that instance. When you stop Jupyter the instance goes away with it.

The QPM backend is `mock`. Reservations and vendor sessions are small files under `/tmp/flux-qfw-mock`. No real QPM or device is contacted. The full QFw stack is installed so you can go further than the notebook does.

## Pinned versions

Everything the build fetches is pinned, so a release somewhere else cannot break it. The base image is pinned by digest, and Fluxion, QFw, QRMI, libfabric, Open MPI, flux-pmix, Rust, SWIG and uv by version or commit (the `ARG` lines in the `Dockerfile`). Every Python package in the QFw and Jupyter venvs comes from `locks/`, at exact versions. The QFw lock was solved for the QFw commit in `QFW_REF`, so change them together. Each lock file says how to regenerate it.

## Choosing the flux-qfw version

The image installs flux-qfw from the branch in `FLUX_QFW_REF`, which is `updates` for now. Once that branch is merged, build from `main` instead:

```bash
make build FLUX_QFW_REF=main
```
