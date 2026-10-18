# syntax=docker/dockerfile:1
# Flux tutorial image for the QRMI coscheduling demo.
#
# Build from the qrmi directory (the build context is that directory, not docker/).
#   docker build -f ./docker/Dockerfile -t ghcr.io/flux-framework/flux-tutorial:qrmi .
#
# Run locally. The docker socket is for the fluence notebook, which creates a
# kind cluster on the host's docker. Leave it off and only that notebook is
# affected.
#   docker run --rm -it -p 8888:8888 -v /var/run/docker.sock:/var/run/docker.sock \
#       ghcr.io/flux-framework/flux-tutorial:qrmi
#
# Adapted from 2026/SC26/docker/Dockerfile. The base is not fluxrm/flux-sched,
# because the demo needs a flux-sched with the coschedule queue policy, the
# flux-quantum jobtap and cli plugins, and qrmi in the python flux uses. All
# of that is the flux-quantum QRMI demo image, built from
# examples/qrmi/container/Dockerfile in converged-computing/flux-quantum.
# This file layers JupyterLab and the launcher on top of it, the way the SC26
# image layers them on fluxrm/flux-sched:noble.
#
# To use a base you built yourself.
#   docker build -f ./docker/Dockerfile --build-arg BASE_IMAGE=flux-quantum-qrmi \
#       -t ghcr.io/flux-framework/flux-tutorial:qrmi .
ARG BASE_IMAGE=ghcr.io/converged-computing/flux-quantum:qrmi-demo-10-8-2026
FROM ${BASE_IMAGE}

USER root
ENV DEBIAN_FRONTEND=noninteractive

# tini reaps and forwards signals as pid 1. python3-venv is for the jupyter
# venv below, git is for nbgitpuller.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini python3-venv git jq bash-completion \
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

# Kubernetes tooling for the fluence demo. kind creates its nodes on the
# host's docker, through the socket mounted at run time, so no daemon runs
# in here and nothing is privileged. The docker cli is the static build,
# without the daemon.
ARG DOCKER_VERSION=27.5.1
ARG KIND_VERSION=v0.32.0
RUN set -eu; arch=$(dpkg --print-architecture); \
    case "$arch" in amd64) darch=x86_64 ;; arm64) darch=aarch64 ;; *) echo "unsupported arch $arch" >&2; exit 1 ;; esac; \
    curl -fsSL "https://download.docker.com/linux/static/stable/${darch}/docker-${DOCKER_VERSION}.tgz" \
        | tar -xz -C /usr/local/bin --strip-components=1 docker/docker; \
    curl -fsSL -o /usr/local/bin/kind "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-${arch}"; \
    chmod +x /usr/local/bin/kind; \
    kver=$(curl -fsSL https://dl.k8s.io/release/stable.txt); \
    curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${kver}/bin/linux/${arch}/kubectl"; \
    chmod +x /usr/local/bin/kubectl; \
    docker --version; kind --version; kubectl version --client

# Tab completion in every terminal. bash-completion loads these lazily on the
# first Tab for each command, and the system bashrc turns bash-completion on
# for interactive shells, which is what a JupyterLab terminal is. k is kubectl.
RUN kubectl completion bash > /usr/share/bash-completion/completions/kubectl \
    && kind completion bash > /usr/share/bash-completion/completions/kind \
    && docker completion bash > /usr/share/bash-completion/completions/docker \
    && cat >> /etc/bash.bashrc <<'BASHRC'

# flux tutorial. Completion for kubectl, kind, docker, and k
if ! shopt -oq posix && [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
fi
alias k=kubectl
complete -o default -F __start_kubectl k 2>/dev/null || true
BASHRC

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

# The entrypoint starts as root so it can make a mounted docker socket usable
# by the tutorial user, then drops to that user with setpriv and execs the
# command.
COPY ./docker/bin/docker-entrypoint /usr/local/bin/
COPY ./docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["tini", "--", "docker-entrypoint"]

USER root
WORKDIR ${HOME}/tutorial

# flux-quantum-start is the base image's entrypoint. It writes the coschedule
# config, runs flux start with it, and the instance's initial program
# (flux-quantum-init) populates the vendor devices into the graph before
# running what follows the --. JupyterLab is that program, so every terminal
# opened from the sidebar is inside the instance with FLUX_URI set.
CMD ["flux-quantum-start", "--", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888"]
