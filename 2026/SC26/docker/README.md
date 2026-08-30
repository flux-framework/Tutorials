# Building the SC26 tutorial container

All commands run from `2026/SC26` (the build context is this directory, not `docker/`).

## Build

```bash
cd 2026/SC26
docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:sc26 .
```

The base image is `fluxrm/flux-sched:noble`, so Flux and Fluxion come pre-built. The
Dockerfile layers on JupyterLab, the launcher UI, and the Module 2 quantum dependencies.
Expect roughly 10–15 minutes on a cold cache.

## Run

```bash
docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:sc26
```

Open the URL with the token that JupyterLab prints. The container starts with
`flux start --test-size=4`, so you get four faux nodes to schedule against.

To edit notebooks on your host and see changes live, mount over the copied tree:

```bash
docker run --rm -it -p 8888:8888 \
  -v $(pwd)/tutorial:/home/jovyan \
  ghcr.io/flux-framework/flux-tutorial:sc26
```

## Smoke tests

Once inside (`docker exec -it <id> bash`, or a terminal in JupyterLab), these are the
things worth checking before the tutorial. Each maps to a `TODO(sc26)` in the tree.

```bash
# Flux is alive and this is how many cores the puzzle has to work with
flux resource list
flux uptime

# Module 1 plugin workshop: Python validator, standalone then loaded live
cd ~/module1
flux run --dry-run -n8 sleep 60 \
  | flux job-validator --jobspec-only --plugins=./plugin-workshop/oven_capacity.py --max-cores=4
flux module reload job-ingest validator-plugins=jobspec,$(pwd)/plugin-workshop/oven_capacity.py
flux submit -n8 sleep 60      # should be rejected
flux module reload job-ingest validator-plugins=jobspec

# Optional Lua bonus: does -o userrc work for this user?
flux run -o verbose=2 -o userrc=plugin-workshop/order-ticket.lua -n2 hostname

# Module 2 quantum: local simulator, no credentials
cd ~/module2
flux run --cores-per-task=1 python3 scripts/qaoa_maxcut.py -p 2 -s 2048
```

Module 2's Kubernetes notebooks will **not** work in this container. Usernetes needs
rootless Docker, cgroup v2 delegation, and the `vxlan` and `br_netfilter` kernel modules,
and the operator and LAMMPS images are ARM-only. Those sections require the EC2 instance
built by [`build/build-ubuntu.sh`](../build/build-ubuntu.sh), which installs Usernetes and
places `start-usernetes.sh` in the home directory.

The QAOA run should report `"best_cut": 6` out of 7 edges, which is the true optimum for
the built-in graph, and take a few seconds.

## Pushing

CI builds this on pull request and pushes on merge. See
[`.github/workflows/docker-builds.yaml`](../../../.github/workflows/docker-builds.yaml),
where SC26 is now the only live matrix entry and prior years are commented out.

To push by hand:

```bash
docker push ghcr.io/flux-framework/flux-tutorial:sc26
```

## Files here

| File | Purpose |
|---|---|
| `Dockerfile` | The tutorial image |
| `jupyter-launcher.yaml` | Launcher tiles, one per module notebook, plus reference links |
| `requirements.txt` | JupyterHub/Lab pins, carried over from 2026/HPSF |
| `requirements_venv.txt` | Build-time venv requirements |
| `entrypoint.sh` | JupyterHub single-user entrypoint |
| `flux-icon.png` | Launcher icon |

## What changed from the 2026 images

- Copies `module1/`, `module2/`, `module3/` instead of `ch1` through `ch5`
- Adds `qiskit`, `qiskit-aer`, and `scipy` for the Module 2 quantum notebook
- Drops `amazon-braket-sdk`, since that example was replaced by a local simulator
- Drops `flux-mcp`, since the agentic science section was cut
