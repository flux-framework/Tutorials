# Building the QRMI tutorial container

All commands run from the `qrmi` directory (the build context is that directory, not
`docker/`).

## The base image

This Dockerfile does not start from `fluxrm/flux-sched`, as the SC26 image does. The
demo needs things that image does not have:

- a flux-sched with the `coschedule` queue policy, so a held job reserves its cores
- the flux-quantum jobtap plugin, for admission control, and the cli plugin, for the
  `--quantum-*` submit options
- the vendor devices populated into the fluxion graph before any job runs
- `qrmi[ibm]`, which needs python 3.11 or newer, in the python flux uses

All of that is the flux-quantum QRMI demo image, built from
[`examples/qrmi/container/Dockerfile`](https://github.com/converged-computing/flux-quantum/tree/braket-hybrid/examples/qrmi/container)
in converged-computing/flux-quantum. This Dockerfile layers JupyterLab and the launcher
on top of it. The default base is:

```
ghcr.io/converged-computing/flux-quantum:qrmi-demo-10-8-2026
```

To build the base yourself, from a flux-quantum checkout:

```bash
docker build -f examples/qrmi/container/Dockerfile -t flux-quantum-qrmi .
```

and then point this build at it with `--build-arg BASE_IMAGE=flux-quantum-qrmi`.
That build compiles flux-core and flux-sched and takes a while. The layer this
directory adds is a few minutes.

## Build

```bash
cd qrmi
docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:qrmi .
```

Build arguments:

| Argument | Default | What it is |
|---|---|---|
| `BASE_IMAGE` | `ghcr.io/converged-computing/flux-quantum:qrmi-demo-10-8-2026` | The demo image to layer jupyter on |
| `NB_USER` | `ubuntu` | The base image's user, which jupyter and the pair run as |

## Run

```bash
docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:qrmi
```

Open the URL with the token that JupyterLab prints. The container starts with
`flux-quantum-start -- jupyter lab`, which is `flux start` with the coschedule config
and JupyterLab as the instance's initial program, so terminals opened from the sidebar
have `FLUX_URI` set and are inside the instance. One broker, with as many cores as
docker gives the container.

To edit notebooks on your host and see changes live, mount over the copied tree:

```bash
docker run --rm -it -p 8888:8888 \
  -v $(pwd)/tutorial:/home/ubuntu/tutorial \
  ghcr.io/flux-framework/flux-tutorial:qrmi
```

To tune the instance, the base image's knobs still apply, for example two brokers
so the pair can land on different ranks:

```bash
docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:qrmi \
  flux-quantum-start -s 2 -- jupyter lab --ip=0.0.0.0 --port=8888
```

## Smoke tests

Once inside (a terminal in JupyterLab, or `docker exec -it <id> bash` followed by
`flux proxy local:///tmp/flux-*/local-0 bash` from the host), these are the things
worth checking before a session.

```bash
# the instance is alive and fluxion with the quantum plugin is what schedules it
flux resource list
flux module list | grep fluxion
flux jobtap list

# everything the pair needs, each line says what it found
flux-quantum-check

# one mocked pair, end to end, no token. Expect a held classical job in SCHED
# while the scout runs, a memo with quantum_session on the classical eventlog,
# and both jobs finishing
flux-quantum-demo mock

# the ibm part, with credentials exported in that terminal first
flux-quantum-check --ibm
```

The mock demo takes about ten seconds and ends with `submit to both done: <n>s` and a
path to the saved transcript under the home directory.

## Pushing

```bash
docker push ghcr.io/flux-framework/flux-tutorial:qrmi
```

## Files here

| File | Purpose |
|---|---|
| `Dockerfile` | The tutorial image, jupyter on the flux-quantum demo image |
| `jupyter-launcher.yaml` | Launcher tiles, one for the notebook, plus reference links |
| `requirements.txt` | JupyterLab, JupyterHub, and the launcher, installed into `/opt/venv` |
| `entrypoint.sh` | JupyterHub single-user entrypoint |
| `flux-icon.png` | Launcher icon |

## What is different from the SC26 image

- The base is the flux-quantum demo image, not `fluxrm/flux-sched:noble`, see above
- The user is `ubuntu`, the base image's user, not `jovyan`. The pair runs as the
  submitting user and reads credentials from that user's environment, so jupyter
  has to be that user
- The venv is on `PATH` first, as in SC26, so `python3` in a terminal is the venv
  python. The demo and the notebook's snippets use `flux python`, which is the base
  image's python regardless of `PATH` and the one with the flux bindings, flux_quantum,
  qrmi, and qiskit. A kernel on flux python is registered under the name `flux`
- The pip pins are fresh rather than the 2023 pip-compile output, which does not build
  on python 3.12
- No nodejs tarball, nothing here builds a lab extension
