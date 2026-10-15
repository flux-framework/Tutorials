# syntax=docker/dockerfile:1
# Flux tutorial image for the QRMI coscheduling demo.
#
# Build from the qrmi directory (the build context is that directory, not docker/):
#   docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:qrmi .
#
# Run locally:
#   docker run --rm -it -p 8888:8888 ghcr.io/flux-framework/flux-tutorial:qrmi
#
# Adapted from 2026/SC26/docker/Dockerfile. The base is not fluxrm/flux-sched,
# because the demo needs a flux-sched with the coschedule queue policy, the
# flux-quantum jobtap and cli plugins, and qrmi in the python flux uses. All
# of that is the flux-quantum QRMI demo image, built from
# examples/qrmi/container/Dockerfile in converged-computing/flux-quantum.
# This file layers JupyterLab and the launcher on top of it, the way the SC26
# image layers them on fluxrm/flux-sched:noble.
#
# To use a base you built yourself:
#   docker build -f ./docker/Dockerfile --build-arg BASE_IMAGE=flux-quantum-qrmi \
#       -t ghcr.io/flux-framework/flux-tutorial:qrmi .
ARG BASE_IMAGE=ghcr.io/converged-computing/flux-quantum:qrmi-demo-10-8-2026
FROM ${BASE_IMAGE}

USER root
ENV DEBIAN_FRONTEND=noninteractive

# tini reaps and forwards signals as pid 1. python3-venv is for the jupyter
# venv below, git is for nbgitpuller.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini python3-venv git jq \
    && rm -rf /var/lib/apt/lists/*

# JupyterLab in its own venv, on PATH first, as the SC26 image does. python3
# in a terminal is therefore the venv python. The demo and every snippet in
# the notebook use flux python, which is the base image's /usr/bin/python3
# regardless of PATH, and that is where qrmi, qiskit, and flux-quantum are.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY ./docker/requirements.txt /tmp/requirements.txt
RUN python3 -m venv ${VIRTUAL_ENV} \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# The notebooks are markdown read next to a terminal, nothing in them is
# meant to be executed. A kernel on flux python is registered anyway, under
# its own name so the venv's python3 kernel does not shadow it, so a cell
# that is run sees the flux bindings, flux_quantum, and qrmi.
RUN /usr/bin/python3 -m pip install --break-system-packages --no-cache-dir ipykernel \
    && /usr/bin/python3 -m ipykernel install --prefix=/usr/local --name flux \
         --display-name "Python 3 (flux python)"

# This customizes the launcher UI
# https://jupyter-app-launcher.readthedocs.io/en/latest/usage.html
ENV JUPYTER_APP_LAUNCHER_PATH=/usr/local/share/jupyter/lab/jupyter_app_launcher/
COPY ./docker/jupyter-launcher.yaml ${JUPYTER_APP_LAUNCHER_PATH}jp_app_launcher.yaml
COPY ./docker/flux-icon.png ${JUPYTER_APP_LAUNCHER_PATH}static/flux-icon.png

# The demo runs as the base image's user, ubuntu, uid 1000. The scout and the
# classical job run as that user and read the vendor credentials from its
# environment, so jupyter, and the terminals it opens, run as that user too.
ARG NB_USER=ubuntu
ENV NB_USER=${NB_USER} \
    HOME=/home/${NB_USER}

COPY --chown=${NB_USER}:${NB_USER} ./tutorial ${HOME}/tutorial
COPY --chown=${NB_USER}:${NB_USER} ./docker/flux-icon.png ${HOME}/flux-icon.png
RUN mkdir -p ${HOME}/.local/share \
    && chown -R ${NB_USER}:${NB_USER} ${HOME}

ENV SHELL=/usr/bin/bash \
    FLUX_URI_RESOLVE_LOCAL=t

EXPOSE 8888
ENTRYPOINT ["tini", "--"]

# This is for JupyterHub
COPY ./docker/entrypoint.sh /entrypoint.sh

USER ${NB_USER}
WORKDIR ${HOME}

# flux-quantum-start is the base image's entrypoint: it writes the coschedule
# config, runs flux start with it, and the instance's initial program
# (flux-quantum-init) populates the vendor devices into the graph before
# running what follows the --. JupyterLab is that program, so every terminal
# opened from the sidebar is inside the instance with FLUX_URI set.
CMD ["flux-quantum-start", "--", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888"]
